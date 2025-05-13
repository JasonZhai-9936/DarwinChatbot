# ui.py

import json
import os
import time
from nicegui import ui, app
from fastapi import Request

PLAYLIST_PATH = os.path.join("stream", "playlist", "playlist.json")
BACKGROUND_PLAYLIST_PATH = os.path.join("stream", "playlist", "background_playlist.json")

def build_ui(trigger_response_callback):
    with ui.row().classes('w-full h-screen items-start justify-start gap-8 p-8').style('overflow-x: hidden;'):
        # === LEFT VIDEO PLAYER ===
        with ui.column().classes('items-start shrink-0'):
            video_container = ui.card().classes('p-0 overflow-hidden').style('width: 767px; height: 1152px; background: black;')
            with video_container:
                ui.html('''
                <div id="custom-video-container" style="width: 100%; height: 100%; position: relative;">
                    <video id="video-player" autoplay controls 
                        style="width: 100%; height: 100%; object-fit: contain;">
                    </video>
                </div>
                ''').classes('w-full h-full')

        # === RIGHT SIDE PANEL ===
        with ui.column().classes('items-center relative gap-4 max-w-full shrink h-full'):
            # === BACKGROUND VIDEO PLAYER + TITLE ===
            ui.html('''
            <div id="rectangular-background-container" style="
                width: 1000px;
                max-width: 100%;
                aspect-ratio: 16 / 9;
                margin-top: 20px;
                border-radius: 16px;
                overflow: hidden;
                background: black;
                position: relative;
            ">
                <video id="background-player" autoplay muted 
                    style="width: 100%; height: 100%; object-fit: cover; display: block; position: absolute; top: 0; left: 0;">
                </video>
            </div>

            <div id="background-title" style="
                margin-top: 8px;
                font-size: 24px;
                font-weight: bold;
                color: black;
                text-align: center;
                width: 1000px;
                max-width: 100%;
                overflow-wrap: break-word;
            "></div>
            ''')

            # === TEXT INPUT & BUTTON ===
            with ui.column().classes('items-center gap-4 w-full z-10 relative').style('margin-bottom: 20px;'):
                prompt_input = ui.textarea(label='Your prompt', placeholder='Type something...') \
                    .props('outlined') \
                    .classes('w-full mb-4') \
                    .style('background-color: white; min-height: 180px; font-size: 24px; position: relative; z-index: 10;')

                def submit_prompt():
                    user_text = prompt_input.value
                    if user_text and user_text.strip():
                        trigger_response_callback(user_text)
                        prompt_input.value = ""
                    else:
                        ui.notify("Please enter a prompt first", color="warning")

                ui.button('Ask Darwin', on_click=submit_prompt) \
                   .classes('text-2xl py-4 px-10 w-full') \
                   .style('position: relative; z-index: 10;')

        # === JS Handlers ===
        ui.add_body_html('''
        <script>
        window.addEventListener('load', function() {
            let playlist = [];
            let currentIndex = 0;
            const video = document.getElementById('video-player');
            const backgroundVideo = document.getElementById('background-player');
            const bgTitle = document.getElementById('background-title');

            if (!video || !backgroundVideo) return;
            video.muted = false;
            backgroundVideo.muted = true;

            function playVideo(index) {
                if (!playlist || playlist.length === 0) return;
                if (index >= playlist.length) index = 0;

                const timestamp = new Date().getTime();
                const videoPath = playlist[index];
                video.src = `${videoPath}?t=${timestamp}`;
                video.muted = false;
                video.play().catch(err => console.error('Play error:', err));
                console.log(`Playing video: ${videoPath} (index: ${index})`);
                fetch(`/video_update?index=${index}&current=${encodeURIComponent(videoPath)}`);
            }

            let bgPlaylist = [];
            let bgCurrentIndex = 0;

            function playBackgroundVideo(index) {
                if (!bgPlaylist || bgPlaylist.length === 0) {
                    backgroundVideo.removeAttribute('src');
                    return;
                }
                if (index >= bgPlaylist.length) index = 0;

                const timestamp = new Date().getTime();
                const mediaPath = bgPlaylist[index];
                const ext = mediaPath.split('.').pop().toLowerCase();

                // Extract base name and update title
                let baseName = mediaPath.split('/').pop().split('.').slice(0, -1).join('.');
                bgTitle.innerText = baseName;

                if (["mp4", "webm"].includes(ext)) {
                    backgroundVideo.src = `${mediaPath}?t=${timestamp}`;
                    backgroundVideo.style.display = "block";
                    backgroundVideo.play().catch(err => console.error('Background video play error:', err));
                } else {
                    backgroundVideo.style.display = "none";
                    const imgOverlay = document.createElement("img");
                    imgOverlay.src = `${mediaPath}?t=${timestamp}`;
                    imgOverlay.style.cssText = "position: absolute; width: 100%; height: 100%; object-fit: cover; top: 0; left: 0; z-index: 1;";
                    document.getElementById("rectangular-background-container").appendChild(imgOverlay);

                    setTimeout(() => {
                        imgOverlay.remove();
                        bgCurrentIndex = (bgCurrentIndex + 1) % bgPlaylist.length;
                        playBackgroundVideo(bgCurrentIndex);
                    }, 5000);
                }

                console.log(`Playing background media: ${mediaPath} (index: ${index})`);
            }

            async function checkForPlaylistUpdates() {
                try {
                    const response = await fetch('/reload-playlist');
                    const data = await response.json();
                    if (JSON.stringify(data) !== JSON.stringify(playlist)) {
                        console.log('Playlist updated:', data);
                        playlist = data;
                        currentIndex = 0;
                        playVideo(currentIndex);
                    }
                } catch (err) {
                    console.error('Failed to check playlist:', err);
                }
            }

            async function checkForBackgroundPlaylistUpdates() {
                try {
                    const response = await fetch('/reload-background-playlist');
                    const data = await response.json();
                    if (JSON.stringify(data) !== JSON.stringify(bgPlaylist)) {
                        console.log('Background playlist updated:', data);
                        bgPlaylist = data;
                        bgCurrentIndex = 0;
                        playBackgroundVideo(bgCurrentIndex);
                    }
                } catch (err) {
                    console.error('Failed to check background playlist:', err);
                }
            }

            video.addEventListener('ended', () => {
                currentIndex = (currentIndex + 1) % playlist.length;
                playVideo(currentIndex);
            });

            backgroundVideo.addEventListener('ended', () => {
                if (bgPlaylist.length > 0) {
                    bgCurrentIndex = (bgCurrentIndex + 1) % bgPlaylist.length;
                    playBackgroundVideo(bgCurrentIndex);
                }
            });

            setInterval(checkForPlaylistUpdates, 2000);
            setInterval(checkForBackgroundPlaylistUpdates, 2000);
            checkForPlaylistUpdates();
            checkForBackgroundPlaylistUpdates();

            window.reloadPlaylist = checkForPlaylistUpdates;
            window.reloadBackgroundPlaylist = checkForBackgroundPlaylistUpdates;
        });
        </script>
        ''')

        @app.get('/video_update')
        def video_update(index: int, current: str):
            try:
                from PlaylistManagerTest import update_video_state
                if current.startswith('/stream/'):
                    video_path = current[8:]
                else:
                    video_path = current
                update_video_state(index, video_path)
                return {"status": "ok"}
            except Exception as e:
                print(f"[ERROR] Failed to update video state: {e}")
                return {"status": "error", "message": str(e)}

        _last_playlist = None
        @app.get('/reload-playlist')
        def reload_playlist():
            nonlocal _last_playlist
            try:
                with open(PLAYLIST_PATH, "r") as f:
                    playlist_data = json.load(f)
                full_playlist = [f"/stream/{item[7:]}" if item.startswith("stream/") else f"/stream/{item}" for item in playlist_data]
                new_playlist_str = json.dumps(full_playlist)
                if new_playlist_str != _last_playlist:
                    print(f"[DEBUG] Playlist updated: {full_playlist}")
                    _last_playlist = new_playlist_str
                return full_playlist
            except Exception as e:
                print(f"[API] Failed to reload playlist: {e}")
                return []

        _last_bg_playlist = None
        @app.get('/reload-background-playlist')
        def reload_background_playlist():
            nonlocal _last_bg_playlist
            try:
                if not os.path.exists(BACKGROUND_PLAYLIST_PATH):
                    return []
                with open(BACKGROUND_PLAYLIST_PATH, "r") as f:
                    playlist_data = json.load(f)
                full_playlist = [f"/stream/{item[7:]}" if item.startswith("stream/") else f"/stream/{item}" for item in playlist_data]
                new_playlist_str = json.dumps(full_playlist)
                if new_playlist_str != _last_bg_playlist:
                    print(f"[DEBUG] Background playlist updated: {full_playlist}")
                    _last_bg_playlist = new_playlist_str
                return full_playlist 
            except Exception as e:
                print(f"[API] Failed to reload background playlist: {e}")
                return []
