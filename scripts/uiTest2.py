# uiTest.py - Updated with Audio Playback Integration

import json
import os
import time
from nicegui import ui, app
from fastapi import Request
from PlaylistManagerTest4 import update_video_state

PLAYLIST_PATH = os.path.join("stream", "playlist", "playlist.json")
BACKGROUND_PLAYLIST_PATH = os.path.join("stream", "playlist", "background_playlist.json")

def build_ui(trigger_response_callback):
    with ui.row().classes('w-full h-screen items-start justify-start gap-8 p-8'):
        # === LEFT VIDEO PLAYER ===
        with ui.column().classes('items-start shrink-0'):
            video_container = ui.card().classes('p-0 overflow-hidden').style('width: 767px; height: 1152px; background: black;')
            with video_container:
                ui.html('''
                <div id="custom-video-container" style="width: 100%; height: 100%; position: relative;">
                    <video id="videoA" autoplay playsinline controls 
                        style="width: 100%; height: 100%; object-fit: contain; position: absolute; top: 0; left: 0; z-index: 1; opacity: 1; transition: opacity 0.5s;">
                    </video>
                    <video id="videoB" autoplay playsinline controls 
                        style="width: 100%; height: 100%; object-fit: contain; position: absolute; top: 0; left: 0; z-index: 0; opacity: 0; transition: opacity 0.5s;">
                    </video>
                    <!-- AUDIO PLAYER FOR SPEECH -->
                    <audio id="speechPlayer" style="display: none;" preload="auto"></audio>
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
                display: none; /* NEW: start hidden */
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

            <!-- FULLSCREEN BACKGROUND VIDEO OVERLAY -->
            <div id="fullscreen-overlay" style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: rgba(0, 0, 0, 0.95);
                z-index: 9999;
                display: none;
                opacity: 0;
                transition: opacity 1s ease-in-out;
            ">
                <video id="fullscreen-background-player" autoplay muted loop
                    style="width: 100%; height: 100%; object-fit: cover;">
                </video>
                
                <!-- Exit Button -->
                <button id="fullscreen-exit-btn" style="
                    position: absolute;
                    top: 30px;
                    right: 30px;
                    width: 60px;
                    height: 60px;
                    background: rgba(255, 255, 255, 0.2);
                    border: 2px solid rgba(255, 255, 255, 0.5);
                    border-radius: 50%;
                    color: white;
                    font-size: 24px;
                    font-weight: bold;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    backdrop-filter: blur(10px);
                    transition: all 0.3s ease;
                    z-index: 10000;
                " onmouseover="this.style.background='rgba(255, 255, 255, 0.3)'; this.style.transform='scale(1.1)'" 
                   onmouseout="this.style.background='rgba(255, 255, 255, 0.2)'; this.style.transform='scale(1)'">
                    ✕
                </button>
                
                <!-- Title Overlay -->
                <div id="fullscreen-title" style="
                    position: absolute;
                    bottom: 50px;
                    left: 50%;
                    transform: translateX(-50%);
                    color: white;
                    font-size: 32px;
                    font-weight: bold;
                    text-align: center;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
                    padding: 20px;
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 10px;
                    backdrop-filter: blur(10px);
                "></div>
                
                <!-- Auto-close timer indicator -->
                <div id="timer-indicator" style="
                    position: absolute;
                    top: 30px;
                    left: 30px;
                    color: white;
                    font-size: 16px;
                    background: rgba(0, 0, 0, 0.5);
                    padding: 10px 15px;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                ">
                    Auto-close in: <span id="timer-countdown">20</span>s
                </div>
            </div>
            ''')

            # === AUDIO STATUS DISPLAY ===
            ui.html('''
            <div id="audio-status" style="
                margin-top: 10px;
                padding: 10px 20px;
                border-radius: 8px;
                background: #f0f0f0;
                color: #333;
                font-size: 16px;
                text-align: center;
                min-width: 300px;
                display: none;
            ">
                🎵 Darwin is speaking...
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
                    .classes('text-2xl py-4 px-10 w-full rounded-full') \
                    .style('background-color: black; color: white; position: relative; z-index: 10;')


        # === ENHANCED JS Handlers with Audio Support ===
        ui.add_body_html('''
        <script>
        window.addEventListener('load', function() {
            let playlist = [];
            let currentIndex = 0;
            let activeVideo = 'A';

            const videoA = document.getElementById('videoA');
            const videoB = document.getElementById('videoB');
            const speechPlayer = document.getElementById('speechPlayer');
            const audioStatus = document.getElementById('audio-status');

            function getActiveVideo() {
                return activeVideo === 'A' ? videoA : videoB;
            }

            function getInactiveVideo() {
                return activeVideo === 'A' ? videoB : videoA;
            }

            function crossfadeToVideo(path) {
                const timestamp = new Date().getTime();
                const nextVideo = getInactiveVideo();
                const currentVideo = getActiveVideo();

                nextVideo.src = `${path}?t=${timestamp}`;
                nextVideo.currentTime = 0;

                nextVideo.oncanplay = () => {
                    nextVideo.style.zIndex = 2;
                    nextVideo.style.opacity = 1;

                    currentVideo.style.zIndex = 1;
                    currentVideo.style.opacity = 0;

                    nextVideo.play().catch(err => console.error('Play error:', err));

                    setTimeout(() => {
                        currentVideo.pause();
                        currentVideo.style.zIndex = 0;
                        activeVideo = activeVideo === 'A' ? 'B' : 'A';
                    }, 500);
                };
            }

            function playVideo(index) {
                if (!playlist || playlist.length === 0) return;
                if (index >= playlist.length) index = 0;

                const videoPath = playlist[index];
                crossfadeToVideo(videoPath);
                fetch(`/video_update?index=${index}&current=${encodeURIComponent(videoPath)}`);
            }

            // === AUDIO FUNCTIONS ===
            let currentSpeechFile = '';
            let isPlayingAudio = false;

            function showAudioStatus() {
                audioStatus.style.display = 'block';
                console.log('Audio status shown');
            }

            function hideAudioStatus() {
                audioStatus.style.display = 'none';
                console.log('Audio status hidden');
            }

            function playAudio(audioPath) {
                // Prevent playing the same file multiple times
                if (currentSpeechFile === audioPath || isPlayingAudio) {
                    console.log('Audio already playing or same file, skipping:', audioPath);
                    return;
                }
                
                console.log('Playing audio:', audioPath);
                currentSpeechFile = audioPath;
                isPlayingAudio = true;
                showAudioStatus();
                
                speechPlayer.src = audioPath;
                speechPlayer.load();
                
                speechPlayer.oncanplay = () => {
                    console.log('Audio can play, starting playback');
                    speechPlayer.play().catch(err => {
                        console.error('Audio play error:', err);
                        isPlayingAudio = false;
                        hideAudioStatus();
                    });
                };
                
                speechPlayer.onended = () => {
                    console.log('Audio playback ended');
                    isPlayingAudio = false;
                    currentSpeechFile = '';
                    hideAudioStatus();
                    // Clear the speech file on the backend
                    fetch('/clear_speech');
                };
                
                speechPlayer.onerror = (e) => {
                    console.error('Audio error:', e);
                    isPlayingAudio = false;
                    currentSpeechFile = '';
                    hideAudioStatus();
                };
            }

            async function checkForNewSpeech() {
                try {
                    const response = await fetch('/get_latest_speech');
                    const data = await response.json();
                    
                    if (data.available && data.speech_file && data.speech_file !== currentSpeechFile && !isPlayingAudio) {
                        console.log('New speech file available:', data.speech_file);
                        playAudio(data.speech_file);
                    }
                } catch (err) {
                    console.error('Failed to check for speech:', err);
                }
            }

            // === FULLSCREEN BACKGROUND VIDEO FUNCTIONS ===
            let fullscreenTimer = null;
            let countdownTimer = null;
            let fullscreenTimeoutId = null;
            
            const fullscreenOverlay = document.getElementById('fullscreen-overlay');
            const fullscreenPlayer = document.getElementById('fullscreen-background-player');
            const fullscreenTitle = document.getElementById('fullscreen-title');
            const fullscreenExitBtn = document.getElementById('fullscreen-exit-btn');
            const timerIndicator = document.getElementById('timer-indicator');
            const timerCountdown = document.getElementById('timer-countdown');

            function enterFullscreenMode(mediaPath, title) {
                console.log('Entering fullscreen mode with:', mediaPath);
                
                // Set up the fullscreen video
                const timestamp = new Date().getTime();
                fullscreenPlayer.src = `${mediaPath}?t=${timestamp}`;
                fullscreenTitle.innerText = title || '';
                
                // Show the overlay with fade-in
                fullscreenOverlay.style.display = 'block';
                setTimeout(() => {
                    fullscreenOverlay.style.opacity = '1';
                }, 50);
                
                // Start countdown timer
                let timeLeft = 20;
                timerCountdown.innerText = timeLeft;
                
                countdownTimer = setInterval(() => {
                    timeLeft--;
                    timerCountdown.innerText = timeLeft;
                    
                    if (timeLeft <= 0) {
                        exitFullscreenMode();
                    }
                }, 1000);
                
                // Auto-exit after 20 seconds
                fullscreenTimer = setTimeout(() => {
                    exitFullscreenMode();
                }, 20000);
                
                console.log('Fullscreen mode activated');
            }

            function exitFullscreenMode() {
                console.log('Exiting fullscreen mode');
                
                // Clear timers
                if (fullscreenTimer) {
                    clearTimeout(fullscreenTimer);
                    fullscreenTimer = null;
                }
                if (countdownTimer) {
                    clearInterval(countdownTimer);
                    countdownTimer = null;
                }
                
                // Fade out the overlay
                fullscreenOverlay.style.opacity = '0';
                
                setTimeout(() => {
                    fullscreenOverlay.style.display = 'none';
                    fullscreenPlayer.pause();
                    fullscreenPlayer.src = '';
                    
                    // Resume normal background video if there's a playlist
                    if (bgPlaylist.length > 0) {
                        playBackgroundVideo(bgCurrentIndex);
                    }
                }, 1000);
                
                console.log('Fullscreen mode deactivated');
            }

            // Add click handler for exit button
            fullscreenExitBtn.addEventListener('click', exitFullscreenMode);

            // === BACKGROUND VIDEO FUNCTIONS (UPDATED) ===
            let bgPlaylist = [];
            let bgCurrentIndex = 0;
            const backgroundVideo = document.getElementById('background-player');
            const bgTitle = document.getElementById('background-title');

            function playBackgroundVideo(index) {
                if (!bgPlaylist || bgPlaylist.length === 0) {
                    backgroundVideo.removeAttribute('src');
                    document.getElementById('rectangular-background-container').style.display = 'none';
                    return;
                }
                
                bgTitle.innerText = "";

                // Show the container only when playing something
                document.getElementById('rectangular-background-container').style.display = 'block';

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
                    
                    // TRIGGER FULLSCREEN MODE WITH 5 SECOND DELAY
                    if (fullscreenTimeoutId) {
                        clearTimeout(fullscreenTimeoutId);
                    }
                    
                    fullscreenTimeoutId = setTimeout(() => {
                        enterFullscreenMode(mediaPath, baseName);
                    }, 5000);
                    
                } else {
                    backgroundVideo.style.display = "none";
                    const imgOverlay = document.createElement("img");
                    imgOverlay.src = `${mediaPath}?t=${timestamp}`;
                    imgOverlay.style.cssText = "position: absolute; width: 100%; height: 100%; object-fit: cover; top: 0; left: 0; z-index: 1;";
                    document.getElementById("rectangular-background-container").appendChild(imgOverlay);

                    // TRIGGER FULLSCREEN MODE WITH 5 SECOND DELAY FOR IMAGES TOO
                    if (fullscreenTimeoutId) {
                        clearTimeout(fullscreenTimeoutId);
                    }
                    
                    fullscreenTimeoutId = setTimeout(() => {
                        enterFullscreenMode(mediaPath, baseName);
                        
                        // For images, set a longer display time in fullscreen
                        setTimeout(() => {
                            imgOverlay.remove();
                            bgCurrentIndex = (bgCurrentIndex + 1) % bgPlaylist.length;
                            playBackgroundVideo(bgCurrentIndex);
                        }, 25000); // 25 seconds total (5 delay + 20 fullscreen)
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

            // === EVENT LISTENERS ===
            videoA.addEventListener('ended', () => {
                currentIndex = (currentIndex + 1) % playlist.length;
                playVideo(currentIndex);
            });

            videoB.addEventListener('ended', () => {
                currentIndex = (currentIndex + 1) % playlist.length;
                playVideo(currentIndex);
            });

            backgroundVideo.addEventListener('ended', () => {
                if (bgPlaylist.length > 0) {
                    bgCurrentIndex = (bgCurrentIndex + 1) % bgPlaylist.length;
                    playBackgroundVideo(bgCurrentIndex);
                }
            });

            // === POLLING INTERVALS ===
            setInterval(checkForPlaylistUpdates, 2000);
            setInterval(checkForBackgroundPlaylistUpdates, 2000);
            setInterval(checkForNewSpeech, 1000);  // Check for new speech every second
            
            // Initial checks
            checkForPlaylistUpdates();
            checkForBackgroundPlaylistUpdates();

            // Expose functions to global scope
            window.reloadPlaylist = checkForPlaylistUpdates;
            window.reloadBackgroundPlaylist = checkForBackgroundPlaylistUpdates;
            window.checkForNewSpeech = checkForNewSpeech;
        });
        </script>
        ''')

        @app.get('/video_update')
        def video_update(index: int, current: str):
            try:
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