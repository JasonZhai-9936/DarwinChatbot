# ui.py

import json
import os
import time
from nicegui import ui

PLAYLIST_PATH = os.path.join("stream", "playlist", "playlist.json")
PLAYLIST_FOLDER = "/stream"

def build_ui(trigger_response_callback):
    with ui.row().classes('w-full h-screen items-start justify-start gap-8 p-8'):

        # === VIDEO PLAYER ===
        with ui.column().classes('items-start'):
            video = ui.video(src='').props('autoplay muted controls') \
                .style('max-height: 100vh; aspect-ratio: 2 / 3; width: auto; height: auto; object-fit: cover;') \
                .classes('rounded-xl shadow-xl')

        playlist = []
        current_index = 0

        def load_playlist():
            nonlocal playlist, current_index
            try:
                with open(PLAYLIST_PATH, "r") as f:
                    playlist = json.load(f)
                    current_index = 0
                    print(f"[UI] Loaded playlist with {len(playlist)} items")
            except Exception as e:
                print(f"[UI] Failed to load playlist: {e}")
                playlist = []

        def play_current_video():
            if current_index < len(playlist):
                src = os.path.join(PLAYLIST_FOLDER, playlist[current_index])
                src = src.replace("\\", "/")
                video.props(f'src={src}?t={time.time()}')
                print(f"[UI] Playing: {src}")
            else:
                print("[UI] No videos to play")

        def play_next_video():
            nonlocal current_index
            current_index += 1
            if current_index < len(playlist):
                play_current_video()
            else:
                print("[UI] Reached end of playlist, reloading")
                load_playlist()
                play_current_video()

        video.on("ended", lambda _: play_next_video())
        load_playlist()
        play_current_video()

        # === RIGHT SIDE PANEL ===
        with ui.column().classes('items-start gap-4'):
            with ui.row().classes('items-center gap-4'):
                ui.input(label='Your prompt', placeholder='Type something...') \
                  .props('outlined') \
                  .classes('w-96')
                ui.button('Enter Prompt', on_click=lambda: print('[INFO] Prompt submission placeholder'))

            # Just one button now
            ui.button("Trigger Response Mode", on_click=trigger_response_callback)
