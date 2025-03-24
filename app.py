from flask import Flask, render_template, request, redirect, url_for, send_file
import subprocess
import os

app = Flask(__name__)

VIDEO_PATH = os.path.join("LivePortrait", "outputs", "finaloutput.mp4")

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    if request.method == "POST":
        user_input = request.form.get("user_input")
        print(f"[USER INPUT] {user_input}")  # Just logs input
        if request.form.get("generate_btn"):
            subprocess.run(["python", "LivePortraitMain.py"])
            return redirect(url_for("video"))
        message = "Input received. You can now generate the video."
    return render_template("index.html", message=message)

@app.route("/video")
def video():
    if os.path.isfile(VIDEO_PATH):
        return render_template("video.html", video_url=url_for("serve_video"))
    return "❌ Video not generated yet."

@app.route("/finaloutput.mp4")
def serve_video():
    return send_file(VIDEO_PATH, mimetype="video/mp4")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
