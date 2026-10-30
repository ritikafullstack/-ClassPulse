# ClassPulse — Multimodal Attendance & Engagement Agent

**An offline-first classroom support prototype** for attendance management, local face-count assistance, session observations, and teaching reflection prompts.

> Important: this repository is a runnable MVP, not a validated biometric attendance product. The camera module detects the number of faces in one frame; it does **not** identify students. A teacher confirms named attendance. Engagement events are instructor-recorded observations, not automated claims about a learner's internal attention or mental state.

## Features

- Flask dashboard with a local student roster.
- Start/end class sessions.
- Mark each learner Present, Absent, Late, or leave them Unmarked.
- Export attendance to CSV.
- Camera preview and local OpenCV face-count endpoint. Frames are processed in memory and are not written to disk.
- Session engagement/interaction event log with instructor notes.
- Rule-based reflection prompts for teaching support.
- SQLite database stored locally in `attendance.db`.
- No cloud AI API keys or external AI services required.

## Tech stack

- Python 3.10+
- Flask
- SQLite
- OpenCV + NumPy
- HTML, CSS, JavaScript, browser camera API

## Run locally

### 1. Install Python

Use Python 3.10 or newer.

### 2. Create and activate a virtual environment

**Windows PowerShell**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start the app

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser. The database is created automatically on first run.

Camera access is supported on `localhost`/`127.0.0.1` in modern browsers. If the camera does not start, check browser permissions and OS camera permissions.

## Quick demo

1. Add 3–5 learners using distinct roll numbers.
2. Start a session (for example, `AI Fundamentals — Lecture 01`).
3. Open the session and mark attendance for each learner.
4. Click **Enable camera**, then **Count faces** to test the local face-count demo.
5. Record an interaction or instructor observation in the engagement section.
6. Export the attendance CSV.
7. End the session from the dashboard.

## Project structure

```text
multimodal-attendance-engagement-agent/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   ├── base.html
│   ├── index.html
│   └── session.html
└── static/
    ├── app.js
    └── style.css
```

## Architecture

```text
Browser UI (HTML/CSS/JS)
  ├── Roster and session management
  ├── Attendance form and CSV export
  ├── Camera preview (browser permission)
  │     └── Single frame → Flask endpoint → OpenCV face count
  └── Engagement observations
           ↓
       Flask application
           ↓
       Local SQLite database
```

All application data stays on the machine running the app unless you deliberately copy or export it. The optional camera endpoint receives one frame from the browser, processes it in memory, and returns a face count; it does not persist the image. Do not expose the Flask development server to a public network.

## Privacy, ethics, and limitations

- Obtain institutional approval and informed consent before using camera-based features.
- Provide a non-camera alternative and an accessible way to correct attendance.
- Do not use face counts, head pose, movement, silence, or audio activity alone to grade, discipline, or infer comprehension.
- This MVP does not implement identity recognition, emotion recognition, automated audio transcription, or validated engagement scoring.
- There is no Gemini integration: keeping the initial project offline avoids sending classroom data to a third-party service.
- Before real deployment, add authentication, role-based access, database backups, retention/deletion policies, audit logs, security testing, and a formal privacy review.

## GitHub: publish this project

1. Create a new **empty** repository on GitHub, for example `multimodal-attendance-engagement-agent`. Do not add a README if you plan to push this folder's existing README.
2. Open a terminal in this project folder.
3. Run the following commands, replacing `YOUR_USERNAME` with your GitHub username:

```bash
git init
git add .
git commit -m "Initial ClassPulse project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/multimodal-attendance-engagement-agent.git
git push -u origin main
```

4. Your public repository URL will be:
   `https://github.com/YOUR_USERNAME/multimodal-attendance-engagement-agent`

If Git asks you to authenticate, complete the GitHub browser sign-in or use the authentication method GitHub recommends. Never commit passwords, access tokens, real student data, or the generated `attendance.db` file.

## Suggested project description for GitHub

ClassPulse is an offline-first Multimodal Attendance & Engagement Agent prototype for educational institutions. It combines a Flask dashboard, local SQLite attendance records, OpenCV face-count assistance, session observation logging, and teacher-facing reflection prompts. It is designed as an assistive classroom tool with privacy and human oversight at its core.

## License

For a student project, you can add an MIT License if you want others to reuse the code. Review your institution's submission requirements before choosing a license.
