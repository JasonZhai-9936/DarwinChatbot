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
            # === BACKGROUND VIDEO PLAYER (15% bigger than original 700px = 805px) ===
            ui.html('''
            <div id="rectangular-background-container" style="
                width: 1000px;
                max-width: 100%;
                aspect-ratio: 16 / 9;
                margin-top: 20px;
                border-radius: 16px;
                overflow: hidden;
                background: black;
            ">
                <video id="background-player" autoplay muted 
                    style="width: 100%; height: 100%; object-fit: cover;">
                </video>
            </div>
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

        # Add JavaScript as a separate body HTML - this handles both video players
        ui.add_body_html('''
        <script>
        // Wait for the page to fully load before initializing the players
        window.addEventListener('load', function() {
            // === MAIN DARWIN VIDEO PLAYER ===
            let playlist = [];
            let currentIndex = 0;
            
            // Get the video elements
            const video = document.getElementById('video-player');
            const backgroundVideo = document.getElementById('background-player');
            
            if (!video) {
                console.error("Could not find video player element!");
                return;
            }
            
            if (!backgroundVideo) {
                console.error("Could not find background video player element!");
                return;
            }
            
            // Ensure main video is not muted
            video.muted = false;
            
            // Ensure background video is muted
            backgroundVideo.muted = true;
            
            // Function to load and play a video
            function playVideo(index) {
                if (!playlist || playlist.length === 0) return;
                if (index >= playlist.length) index = 0;
                
                // Set the new source with cache-busting
                const timestamp = new Date().getTime();
                const videoPath = playlist[index];
                video.src = `${videoPath}?t=${timestamp}`;
                
                // Play the video with sound
                video.muted = false;
                video.play().catch(err => console.error('Play error:', err));
                console.log(`Playing video: ${videoPath} (index: ${index})`);
                
                // Notify server about current video and index
                fetch(`/video_update?index=${index}&current=${encodeURIComponent(videoPath)}`);
            }
            
            // Background video handling
            let bgPlaylist = [];
            let bgCurrentIndex = 0;
            
            function playBackgroundVideo(index) {
                if (!bgPlaylist || bgPlaylist.length === 0) {
                    // If no background videos, set to a blank background
                    backgroundVideo.removeAttribute('src');
                    return;
                }
                
                if (index >= bgPlaylist.length) index = 0;
                
                // Set the new source with cache-busting
                const timestamp = new Date().getTime();
                const videoPath = bgPlaylist[index];
                backgroundVideo.src = `${videoPath}?t=${timestamp}`;
                
                // Always mute background videos
                backgroundVideo.muted = true;
                backgroundVideo.play().catch(err => console.error('Background play error:', err));
                console.log(`Playing background video: ${videoPath} (index: ${index})`);
            }
            
            // Check for playlist updates for main video
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
            
            // Check for background playlist updates
            async function checkForBackgroundPlaylistUpdates() {
                try {
                    const response = await fetch('/reload-background-playlist');
                    const data = await response.json();
                    
                    // Check if the playlist has changed by comparing stringified versions
                    const newPlaylistStr = JSON.stringify(data);
                    const oldPlaylistStr = JSON.stringify(bgPlaylist);
                    
                    if (newPlaylistStr !== oldPlaylistStr) {
                        console.log('Background playlist updated:', data);
                        bgPlaylist = data;
                        
                        if (bgPlaylist.length > 0) {
                            // Reset to first video in playlist when it changes
                            bgCurrentIndex = 0;
                            playBackgroundVideo(bgCurrentIndex);
                        }
                    }
                } catch (err) {
                    console.error('Failed to check background playlist:', err);
                }
            }
            
            // Set up the ended event to play the next video for main player
            video.addEventListener('ended', function() {
                currentIndex = (currentIndex + 1) % playlist.length;
                playVideo(currentIndex);
            });
            
            // Set up the ended event to play the next video for background player
            backgroundVideo.addEventListener('ended', function() {
                if (bgPlaylist.length > 0) {
                    bgCurrentIndex = (bgCurrentIndex + 1) % bgPlaylist.length;
                    playBackgroundVideo(bgCurrentIndex);
                }
            });
            
            // Periodically check for playlist updates
            setInterval(checkForPlaylistUpdates, 2000);
            
            // Periodically check for background playlist updates
            setInterval(checkForBackgroundPlaylistUpdates, 2000);
            
            // Initial playlist loads
            checkForPlaylistUpdates();
            checkForBackgroundPlaylistUpdates();
            
            // Store references to reload functions for debugging
            window.reloadPlaylist = checkForPlaylistUpdates;
            window.reloadBackgroundPlaylist = checkForBackgroundPlaylistUpdates;
        });
        </script>
        ''')
        
        # Add an endpoint to handle video updates
        @app.get('/video_update')
        def video_update(index: int, current: str):
            """Handle updates from the client about the current video"""
            try:
                # Import the update function only when needed to avoid circular imports
                from PlaylistManagerTest import update_video_state
                
                # Strip the /stream/ prefix from the current video path
                if current.startswith('/stream/'):
                    video_path = current[8:]  # Remove "/stream/" prefix
                else:
                    video_path = current
                
                # Update the playlist state
                update_video_state(index, video_path)
                
                return {"status": "ok"}
            except Exception as e:
                print(f"[ERROR] Failed to update video state: {e}")
                return {"status": "error", "message": str(e)}
        
        # Endpoint to reload the playlist - improved to reduce logging spam
        _last_playlist = None
        
        @app.get('/reload-playlist')
        def reload_playlist():
            nonlocal _last_playlist
            try:
                with open(PLAYLIST_PATH, "r") as f:
                    playlist_data = json.load(f)
                
                full_playlist = []
                for item in playlist_data:
                    # Fix: Ensure we don't have paths that start with "stream/"
                    if item.startswith("stream/"):
                        # Remove the "stream/" prefix to avoid duplication
                        item = item[7:]  # Skip past "stream/"
                    
                    # Now add the URL path correctly
                    url = f"/stream/{item}"
                    full_playlist.append(url)
                
                # Only log if the playlist has changed
                new_playlist_str = json.dumps(full_playlist)
                if new_playlist_str != _last_playlist:
                    print(f"[DEBUG] Playlist updated: {full_playlist}")
                    _last_playlist = new_playlist_str
                
                return full_playlist
            except Exception as e:
                print(f"[API] Failed to reload playlist: {e}")
                return []
        
        # Endpoint to reload the background playlist
        _last_bg_playlist = None
        
        @app.get('/reload-background-playlist')
        def reload_background_playlist():
            nonlocal _last_bg_playlist
            try:
                if not os.path.exists(BACKGROUND_PLAYLIST_PATH):
                    return []
                    
                with open(BACKGROUND_PLAYLIST_PATH, "r") as f:
                    playlist_data = json.load(f)
                
                full_playlist = []
                for item in playlist_data:
                    # Fix: Ensure we don't have paths that start with "stream/"
                    if item.startswith("stream/"):
                        # Remove the "stream/" prefix to avoid duplication
                        item = item[7:]  # Skip past "stream/"
                    
                    # Now add the URL path correctly
                    url = f"/stream/{item}"
                    full_playlist.append(url)
                
                # Only log if the playlist has changed
                new_playlist_str = json.dumps(full_playlist)
                if new_playlist_str != _last_bg_playlist:
                    print(f"[DEBUG] Background playlist updated: {full_playlist}")
                    _last_bg_playlist = new_playlist_str
                
                return full_playlist 
            except Exception as e:
                print(f"[API] Failed to reload background playlist: {e}")
                return []