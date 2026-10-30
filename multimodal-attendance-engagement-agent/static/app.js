(() => {
  const video = document.getElementById("camera");
  if (!video) return;
  const canvas = document.getElementById("capture");
  const start = document.getElementById("start-camera");
  const analyze = document.getElementById("analyze-camera");
  const result = document.getElementById("camera-result");
  const placeholder = document.getElementById("camera-placeholder");
  let stream = null;

  start.addEventListener("click", async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
      video.srcObject = stream;
      placeholder.style.display = "none";
      analyze.disabled = false;
      start.textContent = "Camera enabled";
      result.textContent = "Camera is active. Click “Count faces” to analyze one frame.";
    } catch (err) {
      result.textContent = "Could not access the camera. Allow camera permission and use localhost or HTTPS.";
    }
  });

  analyze.addEventListener("click", async () => {
    if (!video.videoWidth) {
      result.textContent = "Wait for the camera preview to load, then try again.";
      return;
    }
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    const image = canvas.toDataURL("image/jpeg", 0.7);
    result.textContent = "Analyzing frame locally…";
    analyze.disabled = true;
    try {
      const response = await fetch("/api/analyze-frame", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ image })
      });
      const data = await response.json();
      result.textContent = data.ok ? `Detected faces: ${data.face_count}. ${data.message}` : data.error;
    } catch (err) {
      result.textContent = "Analysis failed. Check that the local Flask server is running.";
    } finally {
      analyze.disabled = false;
    }
  });

  window.addEventListener("beforeunload", () => {
    if (stream) stream.getTracks().forEach(track => track.stop());
  });
})();
