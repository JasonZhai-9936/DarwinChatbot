# ui.py

import json
import os
import time
from nicegui import ui, app

PLAYLIST_PATH = os.path.join("stream", "playlist", "playlist.json")
PLAYLIST_FOLDER = "/stream"

def build_ui(trigger_response_callback):
    with ui.row().classes('w-full h-screen items-start justify-start gap-8 p-8'):

        # === VIDEO PLAYER ===
        with ui.column().classes('items-start'):
            # Create a fixed-size container for our custom player
            container = ui.card().classes('p-0 overflow-hidden').style('width: 852px; height: 1280px; background: black;')
            
            # Create a custom HTML element for our video player
            custom_player = ui.html('''
            <div id="custom-video-container" style="width: 100%; height: 100%; position: relative;">
                <video id="video-player" autoplay muted controls 
                    style="width: 100%; height: 100%; object-fit: contain;">
                </video>
            </div>
            ''').classes('w-full h-full')

        playlist = []
        
        def load_and_play_playlist():
            try:
                with open(PLAYLIST_PATH, "r") as f:
                    playlist_data = json.load(f)
                    
                    # Prepare full URLs for the playlist
                    full_playlist = []
                    for item in playlist_data:
                        url = os.path.join(PLAYLIST_FOLDER, item).replace("\\", "/")
                        full_playlist.append(url)
                    
                    # Convert to JSON string to pass to JavaScript
                    playlist_json = json.dumps(full_playlist)
                    
                    # Initialize the player with our custom JavaScript
                    js = f'''
                    (function() {{
                        // Store the playlist
                        const playlist = {playlist_json};
                        let currentIndex = 0;
                        
                        // Get the video element
                        const video = document.getElementById('video-player');
                        if (!video) return;
                        
                        // Function to load and play a video
                        function playVideo(index) {{
                            if (index >= playlist.length) index = 0;
                            
                            // Set the new source with cache-busting
                            const timestamp = new Date().getTime();
                            video.src = `${{playlist[index]}}?t=${{timestamp}}`;
                            
                            // Play the video
                            video.play().catch(err => console.error('Play error:', err));
                            console.log(`Playing video: ${{playlist[index]}}`);
                        }}
                        
                        // Set up the ended event to play the next video
                        video.addEventListener('ended', function() {{
                            currentIndex = (currentIndex + 1) % playlist.length;
                            playVideo(currentIndex);
                        }});
                        
                        // Start playing the first video
                        playVideo(currentIndex);
                        
                        // Store the controller functions in the window object for later access
                        window.customVideoPlayer = {{
                            playlist: playlist,
                            playVideo: playVideo,
                            reload: function() {{
                                // Function to reload the playlist
                                fetch('/reload-playlist')
                                    .then(response => response.json())
                                    .then(data => {{
                                        window.customVideoPlayer.playlist = data;
                                        console.log('Playlist reloaded:', data);
                                    }})
                                    .catch(err => console.error('Failed to reload playlist:', err));
                            }}
                        }};
                    }})();
                    '''
                    
                    # Run the JavaScript to initialize the player
                    ui.run_javascript(js)
                    print(f"[UI] Loaded playlist with {len(playlist_data)} items")
                    
            except Exception as e:
                print(f"[UI] Failed to load playlist: {e}")
                ui.run_javascript('''
                    console.error("Failed to load playlist");
                ''')

        # Initialize the player
        load_and_play_playlist()
        
        # Endpoint to reload the playlist
        @app.get('/reload-playlist')
        def reload_playlist():
            try:
                with open(PLAYLIST_PATH, "r") as f:
                    playlist_data = json.load(f)
                
                full_playlist = []
                for item in playlist_data:
                    url = os.path.join(PLAYLIST_FOLDER, item).replace("\\", "/")
                    full_playlist.append(url)
                
                return full_playlist
            except Exception as e:
                print(f"[API] Failed to reload playlist: {e}")
                return []

        # === RIGHT SIDE PANEL ===
        with ui.column().classes('items-start gap-4'):
            with ui.row().classes('items-center gap-4'):
                ui.input(label='Your prompt', placeholder='Type something...') \
                  .props('outlined') \
                  .classes('w-96')
                ui.button('Enter Prompt', on_click=lambda: print('[INFO] Prompt submission placeholder'))

            # Response button
            ui.button("Trigger Response Mode", on_click=trigger_response_callback)
            
            # Add a refresh playlist button (useful for debugging)
            ui.button("Refresh Playlist", on_click=lambda: ui.run_javascript('window.customVideoPlayer.reload()'))