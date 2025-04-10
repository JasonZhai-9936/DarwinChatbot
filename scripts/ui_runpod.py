# ui.py

import json
import os
import time
import threading
from nicegui import ui, app

PLAYLIST_PATH = os.path.join("stream", "playlist", "playlist.json")
PLAYLIST_FOLDER = "/stream"

# Thread-safe way to reload the playlist
def reload_playlist_safe():
    try:
        with open(PLAYLIST_PATH, "r") as f:
            playlist_data = json.load(f)
            
        # Prepare full URLs for the playlist
        full_playlist = []
        for item in playlist_data:
            url = os.path.join(PLAYLIST_FOLDER, item).replace("\\", "/")
            full_playlist.append(url)
        
        # Convert to JSON string for JavaScript
        playlist_json = json.dumps(full_playlist)
        return playlist_json
    except Exception as e:
        print(f"[API] Failed to reload playlist: {e}")
        return json.dumps([])  # Return empty playlist on error

def build_ui(trigger_response_callback):
    # Use a container to hold our UI elements
    with ui.column().classes('w-full h-screen p-4'):
        # Title section
        ui.label('Darwin AI Chatbot').classes('text-2xl font-bold mb-4')
        
        with ui.row().classes('w-full gap-8'):
            # === VIDEO PLAYER ===
            with ui.card().classes('p-0 overflow-hidden').style('width: 450px; height: 675px; background: black;'):
                # Create a custom HTML element for our video player
                custom_player = ui.html('''
                <div id="custom-video-container" style="width: 100%; height: 100%; position: relative;">
                    <video id="video-player" autoplay muted controls 
                        style="width: 100%; height: 100%; object-fit: contain;">
                    </video>
                </div>
                ''').classes('w-full h-full')

            # === RIGHT SIDE PANEL ===
            with ui.card().classes('p-4 flex flex-col gap-4'):
                ui.label("Ask Darwin").classes('text-xl font-bold')
                
                # Input field and submit button in a form
                with ui.form() as form:
                    prompt_input = ui.input(label='Your prompt', placeholder="What would you like to ask Charles Darwin?") \
                        .props('outlined').classes('w-full')
                    
                    with ui.row().classes('items-center justify-between w-full'):
                        # Submit button
                        def submit_prompt():
                            user_text = prompt_input.value
                            if user_text and user_text.strip():
                                # Clear input first to prevent UI modifications during update
                                text_value = prompt_input.value
                                prompt_input.value = ""
                                # Update status
                                status_label.text = "Processing your request..."
                                # Trigger the response in a separate thread to avoid blocking the UI
                                def trigger_with_prompt():
                                    trigger_response_callback(text_value)
                                
                                threading.Thread(target=trigger_with_prompt).start()
                            else:
                                ui.notify("Please enter a prompt first", color="warning")
                        
                        ui.button('Ask Darwin', on_click=submit_prompt).props('color=primary')
                        ui.button('Refresh Video', on_click=lambda: ui.run_javascript('window.customVideoPlayer.reload()'))
                
                # Status display
                status_label = ui.label("Ready for your questions").classes('text-sm text-gray-500 mt-4')
                
                # Instructions card
                with ui.card().classes('mt-4 p-4 bg-blue-50'):
                    ui.label("About this Chatbot").classes('text-lg font-bold')
                    ui.label(
                        "This is a Charles Darwin chatbot that uses RAG (Retrieval Augmented Generation) "
                        "to provide accurate responses about Darwin's life and work. The system combines "
                        "an LLM with special knowledge about Darwin, text-to-speech, and lip-sync technology."
                    ).classes('text-sm')

    # Initialize the player when the page loads
    @ui.page('/').on_load  # Execute this only once when the page loads
    def load_and_play_playlist():
        try:
            playlist_json = reload_playlist_safe()
            
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
                                // Reset to first video
                                currentIndex = 0;
                                playVideo(currentIndex);
                            }})
                            .catch(err => console.error('Failed to reload playlist:', err));
                    }}
                }};
            }})();
            '''
            
            # Run the JavaScript to initialize the player
            ui.run_javascript(js)
            print(f"[UI] Player initialized")
            
        except Exception as e:
            print(f"[UI] Failed to initialize player: {e}")
            ui.run_javascript('''
                console.error("Failed to initialize player");
            ''')
        
    # Endpoint to reload the playlist - use a separate function to avoid modifying UI state
    @app.get('/reload-playlist')
    def reload_playlist_api():
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