from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
import sqlite3
import os
import csv
import io

try:
    import cv2
    import numpy as np
except Exception:
    cv2 = None
    np = None

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "attendance.db")
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-demo-change-this-key")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Present',
            marked_at TEXT NOT NULL,
            UNIQUE(session_id, student_id),
            FOREIGN KEY(session_id) REFERENCES sessions(id),
            FOREIGN KEY(student_id) REFERENCES students(id)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS engagement_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            value REAL NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )""")

def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")

@app.route("/")
def index():
    with db() as conn:
        students = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
        sessions = conn.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 8").fetchall()
        active = conn.execute("SELECT * FROM sessions WHERE ended_at IS NULL ORDER BY id DESC LIMIT 1").fetchone()
        total_students = conn.execute("SELECT COUNT(*) n FROM students").fetchone()["n"]
        total_sessions = conn.execute("SELECT COUNT(*) n FROM sessions").fetchone()["n"]
        present_today = 0
        if active:
            present_today = conn.execute("SELECT COUNT(*) n FROM attendance WHERE session_id=? AND status='Present'", (active["id"],)).fetchone()["n"]
    return render_template("index.html", students=students, sessions=sessions, active=active,
                           total_students=total_students, total_sessions=total_sessions, present_today=present_today)

@app.post("/students/add")
def add_student():
    name = request.form.get("name", "").strip()
    roll = request.form.get("roll_number", "").strip()
    if not name or not roll:
        flash("Enter both student name and roll number.", "error")
        return redirect(url_for("index"))
    try:
        with db() as conn:
            conn.execute("INSERT INTO students(name, roll_number, created_at) VALUES(?,?,?)", (name, roll, now()))
        flash("Student added.", "success")
    except sqlite3.IntegrityError:
        flash("That roll number already exists.", "error")
    return redirect(url_for("index"))

@app.post("/students/<int:student_id>/delete")
def delete_student(student_id):
    with db() as conn:
        conn.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))
        conn.execute("DELETE FROM students WHERE id=?", (student_id,))
    flash("Student removed.", "success")
    return redirect(url_for("index"))

@app.post("/sessions/start")
def start_session():
    title = request.form.get("title", "").strip() or "Class Session"
    with db() as conn:
        active = conn.execute("SELECT id FROM sessions WHERE ended_at IS NULL LIMIT 1").fetchone()
        if active:
            flash("End the active session before starting another.", "error")
        else:
            conn.execute("INSERT INTO sessions(title, started_at) VALUES(?,?)", (title, now()))
            flash("Session started.", "success")
    return redirect(url_for("index"))

@app.post("/sessions/<int:session_id>/end")
def end_session(session_id):
    with db() as conn:
        conn.execute("UPDATE sessions SET ended_at=? WHERE id=? AND ended_at IS NULL", (now(), session_id))
    flash("Session ended.", "success")
    return redirect(url_for("index"))

@app.post("/sessions/<int:session_id>/attendance")
def mark_attendance(session_id):
    student_id = request.form.get("student_id", type=int)
    status = request.form.get("status", "Present")
    if status not in ("Present", "Absent", "Late"):
        status = "Present"
    if not student_id:
        flash("Choose a student.", "error")
        return redirect(url_for("session_detail", session_id=session_id))
    with db() as conn:
        conn.execute("""INSERT INTO attendance(session_id, student_id, status, marked_at)
            VALUES(?,?,?,?) ON CONFLICT(session_id, student_id)
            DO UPDATE SET status=excluded.status, marked_at=excluded.marked_at""",
            (session_id, student_id, status, now()))
    flash("Attendance saved.", "success")
    return redirect(url_for("session_detail", session_id=session_id))

@app.route("/sessions/<int:session_id>")
def session_detail(session_id):
    with db() as conn:
        session = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        if not session:
            flash("Session not found.", "error")
            return redirect(url_for("index"))
        students = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
        attendance = conn.execute("""SELECT s.id student_id, s.name, s.roll_number,
            COALESCE(a.status, 'Unmarked') status, a.marked_at
            FROM students s LEFT JOIN attendance a ON a.student_id=s.id AND a.session_id=?
            ORDER BY s.name""", (session_id,)).fetchall()
        events = conn.execute("SELECT * FROM engagement_events WHERE session_id=? ORDER BY id DESC LIMIT 30", (session_id,)).fetchall()
        counts = conn.execute("""SELECT
            SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) present,
            SUM(CASE WHEN status='Absent' THEN 1 ELSE 0 END) absent,
            SUM(CASE WHEN status='Late' THEN 1 ELSE 0 END) late
            FROM attendance WHERE session_id=?""", (session_id,)).fetchone()
    return render_template("session.html", session=session, students=students, attendance=attendance, events=events, counts=counts)

@app.post("/sessions/<int:session_id>/event")
def add_event(session_id):
    event_type = request.form.get("event_type", "Instructor note")
    note = request.form.get("note", "").strip()
    value = request.form.get("value", type=float)
    if value is None:
        value = 0.0
    allowed = {"Audio activity", "Attention check", "Interaction", "Instructor note"}
    if event_type not in allowed:
        event_type = "Instructor note"
    with db() as conn:
        conn.execute("INSERT INTO engagement_events(session_id,event_type,value,note,created_at) VALUES(?,?,?,?,?)",
                     (session_id, event_type, value, note, now()))
    flash("Engagement event saved.", "success")
    return redirect(url_for("session_detail", session_id=session_id))

@app.post("/api/analyze-frame")
def analyze_frame():
    """Local-only face count demo. The image is processed in memory and never stored."""
    if cv2 is None or np is None:
        return jsonify({"ok": False, "error": "OpenCV is not installed. Run pip install -r requirements.txt."}), 503
    payload = request.get_json(silent=True) or {}
    data_url = payload.get("image", "")
    if "," not in data_url:
        return jsonify({"ok": False, "error": "No image supplied."}), 400
    import base64
    try:
        raw = base64.b64decode(data_url.split(",", 1)[1])
        arr = np.frombuffer(raw, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Invalid image")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        detector = cv2.CascadeClassifier(cascade_path)
        faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        return jsonify({"ok": True, "face_count": int(len(faces)),
                        "message": "Face count only; this does not identify people or automatically mark named attendance."})
    except Exception:
        return jsonify({"ok": False, "error": "Could not analyze this frame."}), 400

@app.get("/sessions/<int:session_id>/export.csv")
def export_csv(session_id):
    with db() as conn:
        session = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        rows = conn.execute("""SELECT s.name, s.roll_number, COALESCE(a.status,'Unmarked') status, a.marked_at
            FROM students s LEFT JOIN attendance a ON a.student_id=s.id AND a.session_id=?
            ORDER BY s.name""", (session_id,)).fetchall()
    if not session:
        flash("Session not found.", "error")
        return redirect(url_for("index"))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Session", session["title"]])
    writer.writerow(["Started at", session["started_at"]])
    writer.writerow(["Ended at", session["ended_at"] or "Active"])
    writer.writerow([])
    writer.writerow(["Student name", "Roll number", "Status", "Marked at"])
    for row in rows:
        writer.writerow([row["name"], row["roll_number"], row["status"], row["marked_at"] or ""])
    from flask import Response
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=session_{session_id}_attendance.csv"})

@app.route("/health")
def health():
    return jsonify({"status": "ok", "opencv_available": cv2 is not None})

init_db()
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
