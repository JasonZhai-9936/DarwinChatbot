from flask import Flask, render_template, request, redirect, url_for, send_file
import subprocess
import os

app = Flask(__name__)
VIDEO_PATH = os.path.join("LivePortrait", "outputs", "finaloutput.mp4")

#temp change
env = os.environ.copy()
env["LIVEPORTRAIT_SKIP_RELAUNCH"] = "1"


@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    if request.method == "POST":
        user_input = request.form.get("user_input")
        print(f"[USER INPUT] {user_input}")

        # Check if button pressed is meant to generate video
        action = request.form.get("action")
        if action == "generate":
            print("Running LivePortraitMain.py via subprocess...", flush=True)
            try:
                subprocess.run(
                    ["python", "LivePortraitMain.py"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env
                )
                print("Video generation completed.", flush=True)
            except subprocess.CalledProcessError as e:
                print(" Error while running LivePortraitMain.py:", flush=True)
                print(e.output, flush=True)
            return redirect(url_for("video"))

        message = "Input received."
    return render_template("index.html", message=message)


@app.route("/video")
def video():
    if os.path.isfile(VIDEO_PATH):
        return render_template("video.html", video_url=url_for("serve_video"))
    return "No finaloutput.mp4 found."

@app.route("/LivePortrait/outputs/finaloutput.mp4")
def serve_video():
    return send_file(VIDEO_PATH, mimetype="video/mp4")

if __name__ == "__main__":
    port = 5000
    host = "0.0.0.0"
    print(f"\n Flask server running at: http://localhost:{port} or http://127.0.0.1:{port}")
    app.run(debug=True, host=host, port=port)