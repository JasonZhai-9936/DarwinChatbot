# ui.py

import json
import os
import time
from nicegui import ui, app

PLAYLIST_PATH = os.path.join("stream", "playlist", "playlist.json")

def build_ui(trigger_response_callback):
    with ui.row().classes('w-full h-screen items-start justify-start gap-8 p-8'):

        # === VIDEO PLAYER ===
        # Only include a single player implementation
        with ui.column().classes('items-start'):
            # Create a fixed-size container for our player
            video_container = ui.card().classes('p-0 overflow-hidden').style('width: 852px; height: 1280px; background: black;')
            
            # Create a single HTML video element with embedded JavaScript for playlist handling
            with video_container:
                ui.html('''
                <div id="custom-video-container" style="width: 100%; height: 100%; position: relative;">
                    <video id="video-player" autoplay controls 
                        style="width: 100%; height: 100%; object-fit: contain;">
                    </video>
                </div>
                ''').classes('w-full h-full')
        
        # Add JavaScript as a separate body HTML - this avoids duplicate video elements
        ui.add_body_html('''
        <script>
        // Wait for the page to fully load before initializing the player
        window.addEventListener('load', function() {
            let playlist = [];
            let currentIndex = 0;
            
            // Get the video element
            const video = document.getElementById('video-player');
            if (!video) {
                console.error("Could not find video player element!");
                return;
            }
            
            // Ensure video is not muted
            video.muted = false;
            
            // Function to load and play a video
            function playVideo(index) {
                if (!playlist || playlist.length === 0) return;
                if (index >= playlist.length) index = 0;
                
                // Set the new source with cache-busting
                const timestamp = new Date().getTime();
                video.src = `${playlist[index]}?t=${timestamp}`;
                
                // Play the video with sound
                video.muted = false;
                video.play().catch(err => console.error('Play error:', err));
                console.log(`Playing video: ${playlist[index]}`);
            }
            
            // Check for playlist updates
            async function checkForPlaylistUpdates() {
                try {
                    const response = await fetch('/reload-playlist');
                    const data = await response.json();
                    
                    // Check if the playlist has changed by comparing stringified versions
                    const newPlaylistStr = JSON.stringify(data);
                    const oldPlaylistStr = JSON.stringify(playlist);
                    
                    if (newPlaylistStr !== oldPlaylistStr) {
                        console.log('Playlist updated:', data);
                        playlist = data;
                        // Reset to first video in playlist when it changes
                        currentIndex = 0;
                        playVideo(currentIndex);
                    }
                } catch (err) {
                    console.error('Failed to check playlist:', err);
                }
            }
            
            // Set up the ended event to play the next video
            video.addEventListener('ended', function() {
                currentIndex = (currentIndex + 1) % playlist.length;
                playVideo(currentIndex);
            });
            
            // Periodically check for playlist updates
            setInterval(checkForPlaylistUpdates, 2000);
            
            // Initial playlist load
            checkForPlaylistUpdates();
            
            // Store a reference to reload function for debugging
            window.reloadPlaylist = checkForPlaylistUpdates;
        });
        </script>
        ''')
        
        # Endpoint to reload the playlist
        @app.get('/reload-playlist')
        def reload_playlist():
            try:
                with open(PLAYLIST_PATH, "r") as f:
                    playlist_data = json.load(f)
                
                full_playlist = []
                for item in playlist_data:
                    # Fix: Ensure we don't have paths that start with "stream/"
                    # because that would create a double path with the /stream route
                    if item.startswith("stream/"):
                        # Remove the "stream/" prefix to avoid duplication
                        item = item[7:]  # Skip past "stream/"
                    
                    # Now add the URL path correctly
                    url = f"/stream/{item}"
                    full_playlist.append(url)
                
                # Debug: Print what we're returning
                print(f"[DEBUG] Playlist URLs: {full_playlist}")
                return full_playlist
            except Exception as e:
                print(f"[API] Failed to reload playlist: {e}")
                return []

        # === RIGHT SIDE PANEL ===
        with ui.column().classes('items-start gap-4'):
            with ui.row().classes('items-center gap-4'):
                # Added white background to input
                prompt_input = ui.input(label='Your prompt', placeholder='Type something...') \
                  .props('outlined') \
                  .classes('w-96') \
                  .style('background-color: white;')
                
                # Submit the prompt when the button is clicked
                def submit_prompt():
                    user_text = prompt_input.value
                    if user_text and user_text.strip():
                        trigger_response_callback(user_text)
                        prompt_input.value = ""  # Clear input after submission
                    else:
                        ui.notify("Please enter a prompt first", color="warning")
                
                ui.button('Ask Darwin', on_click=submit_prompt)