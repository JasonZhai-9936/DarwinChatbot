# Updated app.py to support progressive video streaming
from flask import Flask, render_template, request, redirect, url_for, send_file, Response, send_from_directory

import subprocess
import os
import threading
import time

app = Flask(__name__)

# Paths
<<<<<<< HEAD
STREAM_DIR = os.path.join("outputs", "stream")
=======
STREAM_DIR = os.path.join("static", "stream")
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3
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

<<<<<<< HEAD
=======
def generate_m3u8():
    """Polls the stream directory and updates the .m3u8 playlist dynamically."""
    chunk_index = 1
    with open(M3U8_PATH, "w") as f:
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:3\n")
        f.write("#EXT-X-TARGETDURATION:5\n")
        f.write("#EXT-X-MEDIA-SEQUENCE:0\n")

    while True:
        chunk_path = os.path.join(STREAM_DIR, f"chunk{chunk_index}.mp4")
        if os.path.exists(chunk_path):
            with open(M3U8_PATH, "a") as f:
                f.write(f"#EXTINF:5.0,\nchunk{chunk_index}.ts\n")
            chunk_index += 1
        else:
            time.sleep(1)
        # End stream if finaloutput is done
        if os.path.exists(VIDEO_PATH):
            break

>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form.get("user_input")
        print(f"[USER INPUT] {user_input}")
        action = request.form.get("action")

        if action == "generate":
<<<<<<< HEAD
            print("[INFO] Launching full generation in background thread")
            threading.Thread(target=run_video_generation).start()
            return redirect(url_for("stream"))

        elif action == "test":
            print("[INFO] Running teststream.py to stream starter chunks")
            threading.Thread(target=lambda: subprocess.run(["python", "teststream.py"], env=env)).start()
=======
            print("[INFO] Launching generation in background threads")
            threading.Thread(target=run_video_generation).start()
            threading.Thread(target=generate_m3u8).start()
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3
            return redirect(url_for("stream"))

    return render_template("index.html")

@app.route("/stream")
def stream():
    return render_template("video_stream.html")

<<<<<<< HEAD
@app.route("/outputs/stream/<filename>")
def stream_chunks(filename):
    print(f"[STREAM] Client requested: {filename}")
=======
@app.route("/static/stream/<filename>")
def stream_chunks(filename):
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3
    return send_from_directory(STREAM_DIR, filename)

@app.route("/LivePortrait/outputs/finaloutput.mp4")
def serve_video():
    return send_file(VIDEO_PATH, mimetype="video/mp4")

<<<<<<< HEAD
@app.route("/outputs/stream/playlist.m3u8")
def stream_playlist():
    return send_file(M3U8_PATH, mimetype="application/vnd.apple.mpegurl")
=======
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3


if __name__ == "__main__":
    port = 5000
    host = "0.0.0.0"
    print(f"\n Flask server running at: http://localhost:{port} or http://127.0.0.1:{port}")
    app.run(debug=True, host=host, port=port)
