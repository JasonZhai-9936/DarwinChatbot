# Updated app.py to support progressive video streaming
from flask import Flask, render_template, request, redirect, url_for, send_file, Response, send_from_directory

import subprocess
import os
import threading
import time

app = Flask(__name__)

# Paths
STREAM_DIR = os.path.join("outputs", "stream")
VIDEO_PATH = os.path.join("LivePortrait", "outputs", "finaloutput.mp4")
M3U8_PATH = os.path.join(STREAM_DIR, "playlist.m3u8")

# Temp env fix for subprocess
env = os.environ.copy()
env["LIVEPORTRAIT_SKIP_RELAUNCH"] = "1"

# Ensure stream dir exists
os.makedirs(STREAM_DIR, exist_ok=True)

# Background generation thread
def run_video_generation():
    subprocess.run(["python", "LivePortraitMainStream.py"], env=env)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form.get("user_input")
        print(f"[USER INPUT] {user_input}")
        action = request.form.get("action")

        if action == "generate":
            print("[INFO] Launching full generation in background thread")
            threading.Thread(target=run_video_generation).start()
            return redirect(url_for("stream"))

        elif action == "test":
            print("[INFO] Running teststream.py to stream starter chunks")
            threading.Thread(target=lambda: subprocess.run(["python", "teststream.py"], env=env)).start()
            return redirect(url_for("stream"))

    return render_template("index.html")

@app.route("/stream")
def stream():
    return render_template("video_stream.html")

@app.route("/outputs/stream/<filename>")
def stream_chunks(filename):
    return send_from_directory(STREAM_DIR, filename)

@app.route("/LivePortrait/outputs/finaloutput.mp4")
def serve_video():
    return send_file(VIDEO_PATH, mimetype="video/mp4")

@app.route("/outputs/stream/playlist.m3u8")
def stream_playlist():
    return send_file(M3U8_PATH, mimetype="application/vnd.apple.mpegurl")


if __name__ == "__main__":
    port = 5000
    host = "0.0.0.0"
    print(f"\n Flask server running at: http://localhost:{port} or http://127.0.0.1:{port}")
    app.run(debug=True, host=host, port=port)
