# avatar_creation_kit.py - Avatar Creation Kit for Darwin AI (Updated with Node Manager)
# Location: Darwinchatbot/scripts/avatar_creation_kit/avatar_creation_kit.py

import os
import base64
from nicegui import ui, app
from pathlib import Path

# Import the node manager
try:
    from node_manager import NodeManager, create_node_manager_ui
    NODE_MANAGER_AVAILABLE = True
except ImportError:
    print("[CREATION KIT] Warning: node_manager.py not found. Node Manager will be disabled.")
    NODE_MANAGER_AVAILABLE = False

# === Configuration ===
CREATION_KIT_PORT = 8081

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths relative to avatar_creation_kit directory
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..", "..")  # Go up to Darwinchatbot/
STREAM_DIR = os.path.join(PROJECT_ROOT, "stream")
OUTPUT_DIR = os.path.join(STREAM_DIR, "generated_assets") 
TEMP_DIR = os.path.join(SCRIPT_DIR, "temp")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# === Global State ===
current_portrait_image = None
current_prompt = ""
current_page = "avatar_creation"  # Track current page: "avatar_creation", "supporting_assets", or "node_manager"
node_manager_instance = None

def create_portrait_creator_ui():
    """Create the Portrait Creator column UI"""
    
    with ui.column().classes('w-full p-6 gap-6'):
        
        # Column Header
        ui.label('Portrait Creator').classes('text-2xl font-bold text-center mb-4')
        
        # Instruction Box
        with ui.card().classes('w-full p-4 bg-blue-50'):
            ui.label('Instructions:').classes('font-semibold mb-2')
            ui.label('Enter a text prompt to generate a portrait, or drag an existing image below for img2img transformation.').classes('text-sm text-gray-700')
        
        # Text Input Box
        prompt_input = ui.textarea(
            label='Portrait Prompt',
            placeholder='Enter your portrait description here...'
        ).classes('w-full').props('outlined rows=3 filled')
        
        # Node Dropdown Selector
        ui.label('Node').classes('text-xl font-bold mb-1')
        node_select = ui.select(
            ['main', 'pipe', 'newspaper', 'phone', 'standingMansion', 'standingMansionSmoke', 'standingBeach', 'standingBeachSmoke'],
            value='main'
        ).classes('w-full mb-4 text-lg text-gray-900').props('outlined dense')
        
        # Image Display/Drop Zone
        with ui.card().classes('w-full aspect-square border-2 border-dashed border-gray-300 hover:border-blue-400 transition-colors'):
            with ui.column().classes('w-full h-full justify-center items-center p-4'):
                
                # Image display area
                image_display = ui.image().classes('max-w-full max-h-full object-contain hidden')
                
                # Drop zone content (shown when no image)
                drop_zone_content = ui.column().classes('justify-center items-center text-center gap-2')
                with drop_zone_content:
                    ui.icon('cloud_upload', size='3rem').classes('text-gray-400')
                    ui.label('Drag & Drop Image Here').classes('text-lg font-medium text-gray-600')
                    ui.label('or click to browse').classes('text-sm text-gray-400')
        
        # Action Buttons Row
        with ui.row().classes('w-full gap-2'):
            generate_btn = ui.button('Generate Portrait', icon='auto_awesome').classes('flex-1 bg-green-600 text-white')
            clear_btn = ui.button('Clear', icon='clear').classes('bg-gray-500 text-white')
        
        # Progress/Status Area
        status_label = ui.label('Ready to create portrait').classes('text-center text-sm text-gray-600')
        progress_bar = ui.linear_progress(value=0).classes('w-full hidden')

def create_video_creator_ui():
    """Create the Video Creator column UI with img2vid and vid2vid sections"""
    
    with ui.column().classes('w-full p-6 gap-6'):
        
        # Column Header
        ui.label('Video Creator').classes('text-2xl font-bold text-center mb-4')
        
        ui.label('Node').classes('text-xl font-bold mb-1')
        node_select = ui.select(
            ['main', 'pipe', 'newspaper', 'phone', 'standingMansion', 'standingMansionSmoke', 'standingBeach', 'standingBeachSmoke'],
            value='main'
        ).classes('w-full mb-4 text-lg text-gray-900').props('outlined dense')
        
        # === IMG2VID Section ===
        with ui.card().classes('w-full p-4'):
            ui.label('Image to Video').classes('text-lg font-semibold mb-3')
            
            # Instruction for img2vid
            with ui.card().classes('w-full p-3 bg-green-50'):
                ui.label('Convert static images into animated videos').classes('text-sm text-gray-700')
            
            # Prompt input for img2vid
            img2vid_prompt = ui.textarea(
                label='Animation Prompt',
                placeholder='Describe the movement or animation you want...'
            ).classes('w-full mb-3').props('outlined rows=2 filled')
            
            # Action button for img2vid
            ui.button('Generate Video from Image', icon='play_circle').classes('w-full bg-green-600 text-white')
        
        # === VID2VID Section ===
        with ui.card().classes('w-full p-4'):
            ui.label('Video to Video').classes('text-lg font-semibold mb-3')
            
            # Instruction for vid2vid
            with ui.card().classes('w-full p-3 bg-purple-50'):
                ui.label('Transform existing videos with new styles or effects').classes('text-sm text-gray-700')
            
            # Prompt input for vid2vid
            vid2vid_prompt = ui.textarea(
                label='Transformation Prompt',
                placeholder='Describe how to transform the video...'
            ).classes('w-full mb-3').props('outlined rows=2 filled')
            
            # Action button for vid2vid
            ui.button('Transform Video', icon='transform').classes('w-full bg-purple-600 text-white')

def create_character_generation_ui():
    """Create the Character Generation column UI"""
    
    with ui.column().classes('w-full p-6 gap-6'):
        
        # Column Header
        ui.label('Character Generation').classes('text-2xl font-bold text-center mb-4')
        
        # Instruction Box
        with ui.card().classes('w-full p-4 bg-orange-50'):
            ui.label('Instructions:').classes('font-semibold mb-2')
            ui.label('Describe your desired avatar character. Include appearance, personality traits, clothing style, and any specific features you want.').classes('text-sm text-gray-700')
        
        # Character Description Input
        character_input = ui.textarea(
            label='Avatar Character Description',
            placeholder='Describe your avatar character in detail...\n\nExample: A wise elderly professor with gray hair, wearing Victorian-era clothing, kind eyes, and a gentle smile. Should appear scholarly and approachable.'
        ).classes('w-full').props('outlined rows=8 filled')

def create_asset_search_ui():
    """Create the Asset Search column UI with auto generation and link inputs"""
    
    with ui.column().classes('w-full p-6 gap-6'):
        
        # Column Header
        ui.label('Asset Search & Collection').classes('text-2xl font-bold text-center mb-4')
        
        # === AUTO GENERATION Section ===
        with ui.card().classes('w-full p-4'):
            ui.label('Auto Generation').classes('text-lg font-semibold mb-3')
            
            # Instruction for auto generation
            with ui.card().classes('w-full p-3 bg-blue-50'):
                ui.label('Enter basic prompts about your character and the system will automatically find relevant images and videos online').classes('text-sm text-gray-700')
            
            # Character prompt input
            auto_gen_prompt = ui.textarea(
                label='Character Search Prompt',
                placeholder='Enter keywords about your character...\nExample: Victorian scientist, Charles Darwin, evolution, natural selection'
            ).classes('w-full mb-3').props('outlined rows=3 filled')
            
            # Search options
            with ui.row().classes('w-full gap-2 mb-3'):
                search_images = ui.checkbox('Search Images', value=True).classes('flex-1')
                search_videos = ui.checkbox('Search Videos', value=True).classes('flex-1')
            
            # Action button for auto generation
            ui.button('Auto-Find Assets', icon='search').classes('w-full bg-blue-600 text-white')
        
        # === LINK INPUTS Section ===
        with ui.card().classes('w-full p-4'):
            ui.label('Manual Link Input').classes('text-lg font-semibold mb-3')
            
            # Instruction for link inputs
            with ui.card().classes('w-full p-3 bg-green-50'):
                ui.label('Enter image URLs and YouTube links, one per line. The system will download and organize them automatically.').classes('text-sm text-gray-700')
            
            # Link input textarea
            link_input = ui.textarea(
                label='Asset Links',
                placeholder='Enter links one per line...\n\nhttps://example.com/image1.jpg\nhttps://youtube.com/watch?v=abc123\nhttps://example.com/image2.png'
            ).classes('w-full mb-3').props('outlined rows=6 filled')
            
            # Action buttons for link processing
            with ui.row().classes('w-full gap-2'):
                ui.button('Process Links', icon='download').classes('flex-1 bg-green-600 text-white')
                ui.button('Validate Links', icon='check_circle').classes('bg-gray-600 text-white')

def create_asset_organization_ui():
    """Create the Asset Organization column UI"""
    
    with ui.column().classes('w-full p-6 gap-6'):
        
        # Column Header
        ui.label('Asset Organization').classes('text-2xl font-bold text-center mb-4')
        
        # === ASSET FOLDER MANAGER Section ===
        with ui.card().classes('w-full p-4'):
            ui.label('Asset Folder Manager').classes('text-lg font-semibold mb-3')
            
            # Instruction for folder manager
            with ui.card().classes('w-full p-3 bg-purple-50'):
                ui.label('Manage and organize your asset folders. View, move, and categorize your generated assets.').classes('text-sm text-gray-700')
            
            # Placeholder textbox for folder manager
            folder_manager_input = ui.textarea(
                label='Folder Management (Coming Soon)',
                placeholder='This section will allow you to:\n- View existing asset folders\n- Move assets between folders\n- Rename and organize categories\n- Preview folder contents'
            ).classes('w-full mb-3').props('outlined rows=4 readonly filled')
            
            # Action button (placeholder)
            ui.button('Open Folder Manager', icon='folder_open').classes('w-full bg-purple-600 text-white').props('disabled')
        
        # === ASSET FOLDER GENERATION Section ===
        with ui.card().classes('w-full p-4'):
            ui.label('Asset Folder Generation').classes('text-lg font-semibold mb-3')
            
            # Instruction for folder generation
            with ui.card().classes('w-full p-3 bg-orange-50'):
                ui.label('Automatically generate relevant asset folders that the LLM system expects (darwin_family, beagle_voyage, etc.)').classes('text-sm text-gray-700')
            
            # Available folder types display
            with ui.card().classes('w-full p-3 bg-gray-50 mb-3'):
                ui.label('Standard Folders to Generate:').classes('font-medium mb-2')
                folder_list = [
                    'beagle_voyage', 'darwin_family', 'darwin_himself', 'darwins_finches',
                    'evolution_conv_div', 'natural_selection', 'shropshire', 'tree_of_life'
                ]
                ui.label(' • ' + '\n • '.join(folder_list)).classes('text-sm text-gray-700 whitespace-pre-line')
            
            # Custom folder input
            custom_folders_input = ui.textarea(
                label='Additional Custom Folders',
                placeholder='Enter additional folder names, one per line...\n\nExample:\ndarwin_theories\nevolution_examples\nscientific_instruments'
            ).classes('w-full mb-3').props('outlined rows=3 filled')
            
            # Action buttons for folder generation
            with ui.row().classes('w-full gap-2'):
                ui.button('Generate Standard Folders', icon='create_new_folder').classes('flex-1 bg-orange-600 text-white')
                ui.button('Create Custom Folders', icon='add').classes('bg-gray-600 text-white')

def create_supporting_assets_page():
    """Create the Supporting Asset Generation page with horizontal scrolling"""
    
    # Main Content Area - Horizontal scrolling container
    with ui.scroll_area().classes('w-full min-h-screen bg-gray-100'):
        with ui.row().classes('p-6 gap-6').style('min-width: fit-content;'):
            
            # Asset Search Column
            with ui.card().classes('min-h-96').style('width: 300px; flex-shrink: 0;'):
                create_asset_search_ui()
            
            # Asset Organization Column
            with ui.card().classes('min-h-96').style('width: 300px; flex-shrink: 0;'):
                create_asset_organization_ui()

def create_node_manager_page():
    """Create the Node Manager page"""
    global node_manager_instance
    
    if not NODE_MANAGER_AVAILABLE:
        # Show error message if node manager is not available
        with ui.column().classes('w-full p-6 items-center justify-center'):
            ui.label('Node Manager Unavailable').classes('text-2xl font-bold text-red-600 mb-4')
            ui.label('The node_manager.py file could not be loaded.').classes('text-lg text-gray-600 mb-2')
            ui.label('Please ensure node_manager.py is in the same directory as this script.').classes('text-sm text-gray-500')
        return
    
    # Initialize node manager if not already done
    if node_manager_instance is None:
        node_manager_instance = NodeManager(OUTPUT_DIR)
    
    # Create the node manager UI
    with ui.row().classes('w-full min-h-screen bg-gray-100 p-6'):
        with ui.card().classes('w-full min-h-96'):
            create_node_manager_ui(node_manager_instance)

def create_main_ui():
    """Create the main Creation Kit interface with page switching"""
    
    global current_page
    
    # Container for dynamic content
    content_container = ui.column().classes('w-full')
    
    # App Header with Navigation
    with ui.header().classes('bg-gray-800 bg-blue-800 text-white px-6 py-4'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('Darwin Avatar Creation Kit').classes('text-xl font-bold')
            
            # Right side: Avatar selector and Navigation buttons
            with ui.row().classes('gap-4 items-center'):
                # Avatar selector with load button
                with ui.row().classes('gap-2 items-center'):
                    avatar_select = ui.select(
                    ['Darwin', 'Einstein', 'Newton', 'Tesla', 'Custom Avatar'],
                    label='Avatar',
                    value='Darwin'
                ).classes('w-48 text-lg bg-blue-500 text-white').props('dense outlined')

                    load_btn = ui.button('Load', icon='download').classes('bg-green-600 text-white px-2 py-1 text-sm')
                
                # Navigation buttons
                avatar_btn_container = ui.row()
                assets_btn_container = ui.row()
                nodes_btn_container = ui.row()
    
    def create_avatar_button(active=True):
        avatar_btn_container.clear()
        with avatar_btn_container:
            btn_classes = 'bg-blue-600 text-white'
            if active:
                btn_classes += ' ring-2 ring-green-400'
            return ui.button('Avatar Creation Kit', icon='face').classes(btn_classes).on('click', switch_to_avatar_page)
    
    def create_assets_button(active=False):  
        assets_btn_container.clear()
        with assets_btn_container:
            btn_classes = 'bg-blue-600 text-white'
            if active:
                btn_classes += ' ring-2 ring-green-400'
            return ui.button('Supporting Asset Generation', icon='folder').classes(btn_classes).on('click', switch_to_assets_page)
    
    def create_nodes_button(active=False):
        nodes_btn_container.clear()
        with nodes_btn_container:
            btn_classes = 'bg-blue-600 text-white'
            if active:
                btn_classes += ' ring-2 ring-green-400'
            # Show different icon/text if node manager is unavailable
            if NODE_MANAGER_AVAILABLE:
                return ui.button('Node Manager', icon='account_tree').classes(btn_classes).on('click', switch_to_nodes_page)
            else:
                return ui.button('Node Manager (Unavailable)', icon='account_tree').classes(btn_classes + ' opacity-50').props('disable').on('click', switch_to_nodes_page)
    
    def switch_to_avatar_page():
        global current_page
        current_page = "avatar_creation"
        create_avatar_button(active=True)
        create_assets_button(active=False)
        create_nodes_button(active=False)
        update_page_content()
    
    def switch_to_assets_page():
        global current_page
        current_page = "supporting_assets"
        create_avatar_button(active=False)
        create_assets_button(active=True)
        create_nodes_button(active=False)
        update_page_content()
    
    def switch_to_nodes_page():
        global current_page
        current_page = "node_manager"
        create_avatar_button(active=False)
        create_assets_button(active=False)
        create_nodes_button(active=True)
        update_page_content()
    
    def update_page_content():
        content_container.clear()
        with content_container:
            if current_page == "avatar_creation":
                create_avatar_creation_page()
            elif current_page == "supporting_assets":
                create_supporting_assets_page()
            elif current_page == "node_manager":
                create_node_manager_page()
    
    # Initial setup
    create_avatar_button(active=True)
    create_assets_button(active=False)
    create_nodes_button(active=False)
    update_page_content()

def create_avatar_creation_page():
    """Create the original Avatar Creation page with horizontal scrolling columns"""
    
    # Main Content Area - Horizontal scrolling container
    with ui.scroll_area().classes('w-full min-h-screen bg-gray-100'):
        with ui.row().classes('p-6 gap-6').style('min-width: fit-content; flex-wrap: nowrap;'):
            
            # Node Manager Placeholder Column (First)
            with ui.card().classes('min-h-96').style('width: 400px; flex-shrink: 0;'):
                with ui.column().classes('w-full p-6 gap-6'):
                    ui.label('Node Manager').classes('text-2xl font-bold text-center mb-4')
                    with ui.card().classes('w-full p-4 bg-gray-50'):
                        ui.label('Node connection visualization will appear here. Use the Node Manager tab for full functionality.').classes('text-sm text-gray-600 text-center')
            
            # Portrait Creator Column
            with ui.card().classes('min-h-96').style('width: 400px; flex-shrink: 0;'):
                create_portrait_creator_ui()
            
            # Video Creator Column
            with ui.card().classes('min-h-96').style('width: 400px; flex-shrink: 0;'):
                create_video_creator_ui()
            
            # Character Generation Column
            with ui.card().classes('min-h-96').style('width: 400px; flex-shrink: 0;'):
                create_character_generation_ui()

def main():
    """Main entry point for the Avatar Creation Kit"""
    
    print(f"[CREATION KIT] Starting Avatar Creation Kit on port {CREATION_KIT_PORT}")
    print(f"[CREATION KIT] Script location: {SCRIPT_DIR}")
    print(f"[CREATION KIT] Project root: {os.path.abspath(PROJECT_ROOT)}")
    print(f"[CREATION KIT] Output directory: {os.path.abspath(OUTPUT_DIR)}")
    
    if NODE_MANAGER_AVAILABLE:
        print(f"[CREATION KIT] Node Manager: Available")
    else:
        print(f"[CREATION KIT] Node Manager: Unavailable (node_manager.py not found)")
    
    # Set up the UI
    create_main_ui()
    
    # Add custom CSS for better styling
    ui.add_head_html('''
    <style>
        .nicegui-content {
            padding: 0 !important;
        }
        
        /* Horizontal scroll container */
        .q-scrollarea__container {
            overflow-x: auto !important;
        }
        
        /* Prevent column wrapping */
        .q-col-gutter-md > * {
            flex-wrap: nowrap !important;
        }
        
        /* Custom drag and drop styling */
        .drop-zone {
            transition: all 0.3s ease;
        }
        
        .drop-zone:hover {
            background-color: #f8fafc;
        }
        
        /* Button styling */
        .q-btn {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        /* Header navigation button styling */
        .q-btn.border-2 {
            transition: border-color 0.3s ease;
        }
        
        .q-btn.border-green-500:hover {
            background-color: rgba(34, 197, 94, 0.1);
        }
        
        /* Node canvas styling */
        .node-canvas {
            background-image: 
                radial-gradient(circle at 1px 1px, rgba(0,0,0,.15) 1px, transparent 0);
            background-size: 20px 20px;
        }
    </style>
    ''')
    
    # Run the NiceGUI app
    ui.run(
        port=CREATION_KIT_PORT,
        title="Darwin Avatar Creation Kit",
        favicon="🎨"
    )

if __name__ in {"__main__", "__mp_main__"}:  # Support multiprocessing
    main()