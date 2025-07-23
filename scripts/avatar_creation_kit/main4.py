# main.py - Avatar Creation Kit for Darwin AI 
# Location: Darwinchatbot/scripts/avatar_creation_kit/main.py

import os
import base64
from nicegui import ui, app
from pathlib import Path

# Import the node manager and avatar manager
try:
    from node_manager3 import NodeManager, create_node_manager_ui
    NODE_MANAGER_AVAILABLE = True
except ImportError:
    print("[CREATION KIT] Warning: node_manager.py not found. Node Manager will be disabled.")
    NODE_MANAGER_AVAILABLE = False

try:
    from avatar_manager import AvatarManager
    AVATAR_MANAGER_AVAILABLE = True
except ImportError:
    print("[CREATION KIT] Warning: avatar_manager.py not found. Avatar management will be limited.")
    AVATAR_MANAGER_AVAILABLE = False

# Import the character creator
try:
    from character_creator import CharacterCreator
    CHARACTER_CREATOR_AVAILABLE = True
except ImportError:
    print("[CREATION KIT] Warning: character_creator.py not found. Character Creator will be disabled.")
    CHARACTER_CREATOR_AVAILABLE = False

# === Configuration ===
CREATION_KIT_PORT = 8081

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths relative to avatar_creation_kit directory
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..", "..")  # Go up to Darwinchatbot/
STREAM_DIR = os.path.join(PROJECT_ROOT, "stream")
OUTPUT_DIR = os.path.join(STREAM_DIR) 
TEMP_DIR = os.path.join(SCRIPT_DIR, "temp")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# === Global State ===
current_portrait_image = None
current_prompt = ""
current_page = "avatar_creation"  # Track current page
node_manager_instance = None
avatar_manager_instance = None
current_avatar_name = "Darwin"  # Currently selected avatar
main_update_page_content = None  # Global reference to the main update function
avatar_select_component = None  # Global reference to avatar selector
current_avatar_info_label = None  # Global reference to avatar info display

# Character Creator Instance
character_creator_instance = None

def initialize_managers():
    """Initialize the avatar and node managers"""
    global avatar_manager_instance, node_manager_instance
    
    if AVATAR_MANAGER_AVAILABLE and avatar_manager_instance is None:
        avatar_manager_instance = AvatarManager(SCRIPT_DIR)
    
    if NODE_MANAGER_AVAILABLE and node_manager_instance is None:
        # Initialize with default avatar directory
        default_avatar_dir = get_current_avatar_directory()
        node_manager_instance = NodeManager(default_avatar_dir)
        
        # Set up auto-save callback
        node_manager_instance.set_auto_save_callback(sync_nodes_to_avatar)

def load_avatar_into_node_manager(avatar_name: str):
    """Load avatar data into the node manager"""
    global node_manager_instance
    
    if not (AVATAR_MANAGER_AVAILABLE and NODE_MANAGER_AVAILABLE):
        print("[CREATION KIT] Managers not available for avatar loading")
        return False
    
    if not avatar_name or avatar_name.strip() == "":
        print("[CREATION KIT] Warning: Empty avatar name provided")
        return False
    
    try:
        print(f"[CREATION KIT] Loading avatar '{avatar_name}' into node manager...")
        
        # Get avatar directory and set context
        avatar_dir = avatar_manager_instance.get_avatar_directory(avatar_name)
        print(f"[CREATION KIT] Avatar directory: {avatar_dir}")
        
        # Set the node manager context
        node_manager_instance.set_avatar_context(avatar_name, str(avatar_dir))
        
        # Clear existing nodes first
        node_manager_instance.nodes.clear()
        node_manager_instance.connections.clear()
        print(f"[CREATION KIT] Cleared existing nodes for avatar switch")
        
        # Load avatar data if it exists
        avatar_data = avatar_manager_instance.load_avatar(avatar_name)
        if avatar_data and avatar_data.get('nodes'):
            node_manager_instance.load_from_avatar_data(avatar_data.get('nodes', []))
            print(f"[CREATION KIT] Loaded {len(avatar_data.get('nodes', []))} nodes for avatar '{avatar_name}'")
        else:
            print(f"[CREATION KIT] No node data found for avatar '{avatar_name}', starting with empty nodes")
        
        print(f"[CREATION KIT] Avatar '{avatar_name}' successfully loaded into node manager. Data will save to: {avatar_dir}")
        return True
        
    except Exception as e:
        print(f"[CREATION KIT] Error loading avatar '{avatar_name}' into node manager: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_character_creator_data_callback(character_data):
    """Callback for saving character creator data"""
    global current_avatar_name
    
    if not AVATAR_MANAGER_AVAILABLE:
        ui.notify("Avatar manager not available", type='error')
        return False
    
    if not character_data['name'] or character_data['name'].strip() == "":
        ui.notify("Please enter a character name", type='error')
        return False
    
    try:
        # Prepare avatar-level data only
        avatar_data = {
            'name': character_data['name'],
            'portrait_prompt': character_data['portrait_prompt'],
            'personality': character_data['personality'],
            'character_description': ''  # Initialize empty description for new characters
        }
        
        # Add portrait image if exists
        if character_data['portrait_image']:
            avatar_data['portrait_image'] = character_data['portrait_image']
        
        # Save the avatar info (this creates avatar.json)
        success = avatar_manager_instance.save_avatar(avatar_data)
        
        if success:
            # Update current avatar name and switch to the new avatar
            old_avatar = current_avatar_name
            current_avatar_name = character_data['name']
            
            print(f"[CREATION KIT] Avatar '{current_avatar_name}' saved, switching from '{old_avatar}'")
            
            # Refresh the avatar dropdown first
            refresh_avatar_selector()
            
            # Now switch to the new avatar (this will load it into node manager)
            switch_to_avatar(current_avatar_name)
            
            # Now save nodes separately using node manager
            if NODE_MANAGER_AVAILABLE and character_data['nodes']:
                # Switch node manager to new avatar directory
                avatar_dir = avatar_manager_instance.get_avatar_directory(current_avatar_name)
                if node_manager_instance:
                    node_manager_instance.set_avatar_context(current_avatar_name, str(avatar_dir))
                    
                    # Convert CharacterNode objects to Node manager format
                    node_manager_instance.nodes.clear()
                    node_manager_instance.connections.clear()
                    
                    for i, char_node in enumerate(character_data['nodes']):
                        from node_manager3 import Node
                        
                        # Create node with grid positions
                        grid_x = i % 3  # Simple grid layout
                        grid_y = i // 3
                        
                        node = Node(
                            getattr(char_node, 'id', f"node_{i+1}"),
                            char_node.name,
                            grid_x,
                            grid_y
                        )
                        node.prompt = char_node.prompt
                        
                        # Handle image data
                        if hasattr(char_node, 'image_data') and char_node.image_data:
                            # Save the image and get path
                            import base64
                            try:
                                # Extract and save image
                                if char_node.image_data.startswith('data:'):
                                    header, data = char_node.image_data.split(',', 1)
                                    image_bytes = base64.b64decode(data)
                                    
                                    image_filename = f"node_{i}_{char_node.name.lower().replace(' ', '_')}.png"
                                    image_path = avatar_dir / "nodes" / image_filename
                                    
                                    with open(image_path, 'wb') as f:
                                        f.write(image_bytes)
                                    
                                    node.image_path = str(image_path)
                            except Exception as e:
                                print(f"Error saving node image: {e}")
                        
                        node_manager_instance.nodes[node.id] = node
                    
                    # Save nodes to node_network.json
                    node_manager_instance.save_nodes()
            
            ui.notify(f"Avatar '{current_avatar_name}' saved successfully!", type='positive')
            print(f"[CREATION KIT] Successfully created and switched to avatar '{current_avatar_name}'")
            return True
        else:
            ui.notify("Failed to save avatar", type='error')
            return False
            
    except Exception as e:
        print(f"[CREATION KIT] Error saving character creator data: {e}")
        ui.notify(f"Error saving avatar: {str(e)}", type='error')
        return False

def exit_character_creator_callback():
    """Callback for exiting character creator"""
    global current_page
    current_page = "avatar_creation"
    if main_update_page_content:
        main_update_page_content()
    else:
        ui.notify("Error: Cannot return to main page")

def refresh_character_generation_ui():
    """Refresh character generation UI when avatar changes"""
    try:
        if hasattr(create_character_generation_ui, 'instances') and current_avatar_name in create_character_generation_ui.instances:
            instance = create_character_generation_ui.instances[current_avatar_name]
            if 'load_func' in instance:
                instance['load_func']()
                print(f"[CHARACTER GENERATION] Refreshed UI for avatar '{current_avatar_name}'")
    except Exception as e:
        print(f"[CHARACTER GENERATION] Error refreshing UI: {e}")

def get_available_avatars():
    """Get list of available avatars with proper fallback"""
    available_avatars = []
    
    # Add other saved avatars if avatar manager is available
    if AVATAR_MANAGER_AVAILABLE:
        try:
            saved_avatars = avatar_manager_instance.list_avatars()
            for avatar_info in saved_avatars:
                avatar_name = avatar_info['name']
                if avatar_name and avatar_name not in available_avatars:
                    available_avatars.append(avatar_name)
        except Exception as e:
            print(f"[CREATION KIT] Error loading saved avatars: {e}")
    
    # If no avatars found, add a default
    if not available_avatars:
        available_avatars = ["Darwin"]
    
    available_avatars.sort()  # Sort alphabetically
    return available_avatars

def switch_to_avatar(avatar_name: str):
    """Switch to a specific avatar and update all relevant components"""
    global current_avatar_name
    
    if not avatar_name or avatar_name.strip() == "":
        print("[CREATION KIT] Warning: Cannot switch to empty avatar name")
        return False
    
    old_avatar = current_avatar_name
    current_avatar_name = avatar_name
    
    print(f"[CREATION KIT] Switching from '{old_avatar}' to '{current_avatar_name}'")
    
    # Update avatar dropdown to reflect current selection
    if avatar_select_component:
        available_avatars = get_available_avatars()
        if current_avatar_name not in available_avatars:
            print(f"[CREATION KIT] Warning: Avatar '{current_avatar_name}' not in available list")
            refresh_avatar_selector()
            return False
        
        avatar_select_component.value = current_avatar_name
        avatar_select_component.update()
    
    # Update avatar info display
    update_avatar_info_display()
    
    # Update node manager for the new avatar
    if NODE_MANAGER_AVAILABLE and node_manager_instance:
        print(f"[CREATION KIT] Loading avatar '{current_avatar_name}' into node manager")
        success = load_avatar_into_node_manager(current_avatar_name)
        if not success:
            print(f"[CREATION KIT] Failed to load avatar '{current_avatar_name}' into node manager")
    
    # Refresh current page content for any page that needs to update when avatar changes
    if main_update_page_content:
        if current_page == "node_manager":
            print(f"[CREATION KIT] Refreshing node manager page for avatar '{current_avatar_name}'")
            main_update_page_content()
        elif current_page == "avatar_creation":
            print(f"[CREATION KIT] Refreshing avatar creation page for avatar '{current_avatar_name}'")
            main_update_page_content()
    
    print(f"[CREATION KIT] Successfully switched to avatar: {current_avatar_name}")
    return True

def refresh_avatar_selector():
    """Refresh the avatar selector with current avatars"""
    global avatar_select_component, current_avatar_name
    
    if avatar_select_component:
        available_avatars = get_available_avatars()
        avatar_select_component.options = available_avatars
        
        # Ensure current selection is valid
        if current_avatar_name not in available_avatars:
            if available_avatars:
                current_avatar_name = available_avatars[0]
            else:
                current_avatar_name = "Darwin"
        
        avatar_select_component.value = current_avatar_name
        avatar_select_component.update()
        
        # Update avatar info display
        update_avatar_info_display()
        
        print(f"[CREATION KIT] Refreshed avatar selector. Available: {available_avatars}, Current: {current_avatar_name}")

def update_avatar_info_display():
    """Update the avatar info display"""
    global current_avatar_info_label
    
    if current_avatar_info_label and AVATAR_MANAGER_AVAILABLE:
        try:
            avatar_data = avatar_manager_instance.load_avatar(current_avatar_name)
            if avatar_data:
                node_count = len(avatar_data.get('nodes', []))
                has_portrait = bool(avatar_data.get('portrait_image_path'))
                has_personality = bool(avatar_data.get('personality', '').strip())
                has_description = bool(avatar_data.get('character_description', '').strip())
                
                info_text = f"Avatar: {current_avatar_name} | Nodes: {node_count}"
                if has_portrait:
                    info_text += " | Has Portrait"
                if has_personality:
                    info_text += " | Has Personality"
                if has_description:
                    info_text += " | Has Description"
                
                current_avatar_info_label.text = info_text
            else:
                current_avatar_info_label.text = f"Avatar: {current_avatar_name} (new/empty)"
        except Exception as e:
            current_avatar_info_label.text = f"Avatar: {current_avatar_name} (error loading)"
            print(f"[CREATION KIT] Error updating avatar info: {e}")

def create_main_ui():
    """Create the main Creation Kit interface with page switching"""
    
    global current_page, main_update_page_content, current_avatar_name, avatar_select_component
    global character_creator_instance, current_avatar_info_label
    
    # Initialize managers
    initialize_managers()
    
    # Initialize character creator
    if CHARACTER_CREATOR_AVAILABLE:
        character_creator_instance = CharacterCreator()
    
    # Container for dynamic content
    content_container = ui.column().classes('w-full')
    
    def start_character_creator():
        """Start the character creator workflow"""
        global current_page
        
        if not CHARACTER_CREATOR_AVAILABLE:
            ui.notify("Character creator not available", type='error')
            return
        
        # Reset character creator data
        character_creator_instance.reset_data()
        current_page = "character_creator"
        
        # Update navigation buttons to show none are active
        update_nav_buttons(None)
        update_page_content()
    
    def load_existing_avatar():
        """Load an existing avatar for editing in character creator"""
        if not CHARACTER_CREATOR_AVAILABLE:
            ui.notify("Character creator not available", type='error')
            return
            
        if not current_avatar_name or current_avatar_name.strip() == "":
            ui.notify("Please select an avatar first", type='warning')
            return
            
        if AVATAR_MANAGER_AVAILABLE:
            avatar_data = avatar_manager_instance.load_avatar(current_avatar_name)
            if avatar_data and character_creator_instance.load_from_avatar_data(avatar_data):
                start_character_creator()
                ui.notify(f"Loaded avatar '{current_avatar_name}' for editing")
            else:
                ui.notify(f"Could not load avatar '{current_avatar_name}'", type='warning')
    
    def switch_to_selected_avatar():
        """Switch to the currently selected avatar"""
        # Get the value directly from the dropdown component
        selected_avatar = avatar_select_component.value if avatar_select_component else current_avatar_name
        
        if not selected_avatar or selected_avatar.strip() == "":
            ui.notify("Please select an avatar first", type='warning')
            return
        
        print(f"[CREATION KIT] Switch button clicked, dropdown value: '{selected_avatar}', current: '{current_avatar_name}'")
        
        if selected_avatar != current_avatar_name:
            success = switch_to_avatar(selected_avatar)
            if success:
                ui.notify(f"Switched to avatar: {selected_avatar}")
            else:
                ui.notify(f"Failed to switch to avatar: {selected_avatar}", type='error')
        else:
            ui.notify(f"Already using avatar: {selected_avatar}")
            # Still update the display in case something was out of sync
            update_avatar_info_display()
    
    def refresh_avatar_selector_callback():
        """Refresh the avatar selector with current avatars"""
        refresh_avatar_selector()
    
    def on_avatar_selection_change(e):
        """Handle avatar dropdown selection change"""
        # For NiceGUI select components, try different ways to get the value
        new_avatar = None
        
        # Try different ways to access the new value
        if hasattr(e, 'args') and e.args:
            new_avatar = e.args
        elif hasattr(e, 'value'):
            new_avatar = e.value
        elif hasattr(e, 'sender') and hasattr(e.sender, 'value'):
            new_avatar = e.sender.value
        else:
            # Fallback: get value directly from the component
            new_avatar = avatar_select_component.value if avatar_select_component else "Darwin"
        
        if not new_avatar:
            new_avatar = "Darwin"
            
        print(f"[CREATION KIT] Dropdown changed to: '{new_avatar}' (was: '{current_avatar_name}')")
        print(f"[CREATION KIT] Event object type: {type(e)}, hasattr value: {hasattr(e, 'value')}, hasattr args: {hasattr(e, 'args')}")
        
        if new_avatar != current_avatar_name:
            print(f"[CREATION KIT] Avatar selection changed, switching to: '{new_avatar}'")
            success = switch_to_avatar(new_avatar)
            if success:
                ui.notify(f"Switched to avatar: {new_avatar}")
            else:
                ui.notify(f"Failed to switch to avatar: {new_avatar}", type='error')
        else:
            print(f"[CREATION KIT] Same avatar selected, no change needed")
    
    # App Header with Navigation
    with ui.header().classes('bg-gray-800 bg-blue-800 text-white px-6 py-4'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('Darwin Avatar Creation Kit').classes('text-xl font-bold')
            
            # Right side: Avatar selector and Navigation buttons
            with ui.row().classes('gap-4 items-center'):
                # Avatar selector with load and new buttons
                with ui.row().classes('gap-2 items-center'):
                    avatar_select_component = ui.select(
                        get_available_avatars(),
                        label='Avatar',
                        value=current_avatar_name
                    ).classes('w-48 text-lg bg-blue-500 text-white').props('dense outlined')
                    
                    # Alternative event binding approach - use on_value_change
                    def handle_dropdown_change():
                        new_avatar = avatar_select_component.value
                        print(f"[CREATION KIT] Dropdown value changed to: '{new_avatar}' (was: '{current_avatar_name}')")
                        if new_avatar and new_avatar != current_avatar_name:
                            success = switch_to_avatar(new_avatar)
                            if success:
                                ui.notify(f"Switched to avatar: {new_avatar}")
                            else:
                                ui.notify(f"Failed to switch to avatar: {new_avatar}", type='error')
                    
                    avatar_select_component.on_value_change(handle_dropdown_change)

                    switch_btn = ui.button('Switch', icon='swap_horiz').classes('bg-blue-600 text-white px-2 py-1 text-sm').on('click', switch_to_selected_avatar)
                    edit_btn = ui.button('Edit', icon='edit').classes('bg-green-600 text-white px-2 py-1 text-sm').on('click', load_existing_avatar)
                    new_btn = ui.button('New', icon='add').classes('bg-purple-600 text-white px-2 py-1 text-sm').on('click', start_character_creator)
                    refresh_btn = ui.button('', icon='refresh').classes('bg-gray-600 text-white px-2 py-1 text-sm').on('click', refresh_avatar_selector_callback)
                
                # Navigation buttons containers
                avatar_btn_container = ui.row()
                assets_btn_container = ui.row()
                nodes_btn_container = ui.row()
    
    # Avatar info display bar
    with ui.row().classes('w-full bg-blue-50 px-6 py-2 border-b'):
        current_avatar_info_label = ui.label(f"Avatar: {current_avatar_name}").classes('text-sm font-medium text-blue-800')
    
    def update_nav_buttons(active_page):
        """Update navigation buttons with active state"""
        avatar_btn_container.clear()
        assets_btn_container.clear()
        nodes_btn_container.clear()
        
        with avatar_btn_container:
            btn_classes = 'bg-blue-600 text-white'
            if active_page == "avatar_creation":
                btn_classes += ' ring-2 ring-green-400'
            ui.button('Avatar Creation Kit', icon='face').classes(btn_classes).on('click', switch_to_avatar_page)
        
        with assets_btn_container:
            btn_classes = 'bg-blue-600 text-white'
            if active_page == "supporting_assets":
                btn_classes += ' ring-2 ring-green-400'
            ui.button('Supporting Asset Generation', icon='folder').classes(btn_classes).on('click', switch_to_assets_page)
        
        with nodes_btn_container:
            btn_classes = 'bg-blue-600 text-white'
            if active_page == "node_manager":
                btn_classes += ' ring-2 ring-green-400'
            if NODE_MANAGER_AVAILABLE:
                ui.button('Node Manager', icon='account_tree').classes(btn_classes).on('click', switch_to_nodes_page)
            else:
                ui.button('Node Manager (Unavailable)', icon='account_tree').classes(btn_classes + ' opacity-50').props('disable')
    
    def switch_to_avatar_page():
        global current_page
        current_page = "avatar_creation"
        update_nav_buttons("avatar_creation")
        update_page_content()
    
    def switch_to_assets_page():
        global current_page
        current_page = "supporting_assets"
        update_nav_buttons("supporting_assets")
        update_page_content()
    
    def switch_to_nodes_page():
        global current_page
        current_page = "node_manager"
        update_nav_buttons("node_manager")
        
        # Load current avatar into node manager
        load_avatar_into_node_manager(current_avatar_name)
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
            elif current_page == "character_creator":
                if CHARACTER_CREATOR_AVAILABLE:
                    character_creator_instance.create_page(
                        save_callback=save_character_creator_data_callback,
                        exit_callback=exit_character_creator_callback
                    )
                else:
                    with ui.column().classes('w-full p-6 items-center justify-center'):
                        ui.label('Character Creator Unavailable').classes('text-2xl font-bold text-red-600 mb-4')
                        ui.label('The character_creator.py file could not be loaded.').classes('text-lg text-gray-600 mb-2')
        
        # Update avatar info display whenever page content changes
        update_avatar_info_display()
        
        # Refresh character generation UI if it exists and we're on avatar creation page
        if current_page == "avatar_creation":
            # Use a timer to ensure the UI is fully loaded before refreshing
            ui.timer(0.1, refresh_character_generation_ui, once=True)
    
    # Make update_page_content globally accessible
    main_update_page_content = update_page_content
    
    # Initial setup - make sure we have a valid avatar selected
    available_avatars = get_available_avatars()
    if current_avatar_name not in available_avatars and available_avatars:
        current_avatar_name = available_avatars[0]
    
    # Initialize avatar info display
    update_avatar_info_display()
    
    update_nav_buttons("avatar_creation")
    update_page_content()

def create_node_manager_page():
    """Create the Node Manager page with avatar integration"""
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
        node_manager_instance = NodeManager(get_current_avatar_directory())
    
    # Show current avatar info
    with ui.column().classes('w-full bg-gray-100'):
        # Avatar info header
        with ui.card().classes('w-full p-4 mb-4'):
            with ui.row().classes('w-full justify-between items-center'):
                ui.label(f'Node Manager - {current_avatar_name}').classes('text-2xl font-bold')
                
                with ui.row().classes('gap-2'):
                    ui.button('Save Nodes', icon='save', color='green').on('click', lambda: [
                        node_manager_instance.save_nodes(),
                        sync_nodes_to_avatar(),
                        ui.notify("Nodes saved to avatar"),
                        update_avatar_info_display()  # Refresh info after saving
                    ])
                    ui.button('Reset Nodes', icon='refresh', color='orange').on('click', lambda: [
                        load_avatar_into_node_manager(current_avatar_name),
                        ui.notify("Nodes reset from avatar data"),
                        main_update_page_content()  # Refresh the entire page
                    ])
        
        # Create the node manager UI - full page width
        create_node_manager_ui(node_manager_instance)

def sync_nodes_to_avatar():
    """Sync only avatar-level data to avatar.json (nodes managed separately)"""
    if not AVATAR_MANAGER_AVAILABLE:
        return
    
    try:
        # Load current avatar data (avatar-level info only)
        avatar_data = avatar_manager_instance.load_avatar(current_avatar_name)
        if not avatar_data:
            # Create basic avatar data if none exists
            avatar_data = {
                'name': current_avatar_name,
                'portrait_prompt': '',
                'personality': '',
                'character_description': ''
            }
        
        # Only sync avatar-level data (no nodes)
        avatar_level_data = {
            'name': avatar_data.get('name', current_avatar_name),
            'portrait_prompt': avatar_data.get('portrait_prompt', ''),
            'personality': avatar_data.get('personality', ''),
            'character_description': avatar_data.get('character_description', '')
        }
        
        # Preserve existing portrait and metadata
        if 'portrait_image_path' in avatar_data:
            avatar_level_data['portrait_image_path'] = avatar_data['portrait_image_path']
        if 'metadata' in avatar_data:
            avatar_level_data['metadata'] = avatar_data['metadata']
        
        # Save updated avatar data (this will save only avatar.json)
        success = avatar_manager_instance.save_avatar(avatar_level_data)
        if success:
            print(f"[CREATION KIT] Synced avatar info for '{current_avatar_name}'")
            print(f"[CREATION KIT] Avatar info: avatar.json | Node data: node_network.json")
        else:
            print(f"[CREATION KIT] Failed to sync avatar info")
    
    except Exception as e:
        print(f"[CREATION KIT] Error syncing avatar data: {e}")

def get_current_avatar_directory():
    """Get the directory for the currently selected avatar"""
    if AVATAR_MANAGER_AVAILABLE and current_avatar_name and current_avatar_name.strip():
        return str(avatar_manager_instance.get_avatar_directory(current_avatar_name))
    else:
        # Fallback to stream directory if avatar manager not available
        return OUTPUT_DIR

def create_portrait_creator_ui():
    """Create the Portrait Creator column UI - shortened for 900px height"""
    
    with ui.column().classes('w-full p-6 gap-4'):
        
        # Column Header
        ui.label('Portrait Creator').classes('text-2xl font-bold text-center mb-3')
        
        # Instruction Box
        with ui.card().classes('w-full p-3 bg-blue-50'):
            ui.label('Instructions:').classes('font-semibold mb-1')
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
        ).classes('w-full mb-3 text-lg text-gray-900').props('outlined dense')
        
        # Image Display/Drop Zone
        with ui.card().classes('w-full aspect-square border-2 border-dashed border-gray-300 hover:border-blue-400 transition-colors'):
            with ui.column().classes('w-full h-full justify-center items-center p-3'):
                
                # Image display area
                image_display = ui.image().classes('max-w-full max-h-full object-contain hidden')
                
                # Drop zone content (shown when no image)
                drop_zone_content = ui.column().classes('justify-center items-center text-center gap-2')
                with drop_zone_content:
                    ui.icon('cloud_upload', size='2rem').classes('text-gray-400')
                    ui.label('Drag & Drop Image Here').classes('text-md font-medium text-gray-600')
                    ui.label('or click to browse').classes('text-sm text-gray-400')
        
        # Action Buttons Row
        with ui.row().classes('w-full gap-2'):
            generate_btn = ui.button('Generate Portrait', icon='auto_awesome').classes('flex-1 bg-green-600 text-white')
            clear_btn = ui.button('Clear', icon='clear').classes('bg-gray-500 text-white')

def create_video_creator_ui():
    """Create the Video Creator column UI - shortened for 900px height"""
    
    with ui.column().classes('w-full p-6 gap-4'):
        
        # Column Header
        ui.label('Video Creator').classes('text-2xl font-bold text-center mb-3')
        
        ui.label('Node').classes('text-xl font-bold mb-1')
        node_select = ui.select(
            ['main', 'pipe', 'newspaper', 'phone', 'standingMansion', 'standingMansionSmoke', 'standingBeach', 'standingBeachSmoke'],
            value='main'
        ).classes('w-full mb-3 text-lg text-gray-900').props('outlined dense')
        
        # === IMG2VID Section ===
        with ui.card().classes('w-full p-3'):
            ui.label('Image to Video').classes('text-lg font-semibold mb-2')
            
            # Instruction for img2vid
            with ui.card().classes('w-full p-2 bg-green-50'):
                ui.label('Convert static images into animated videos').classes('text-sm text-gray-700')
            
            # Prompt input for img2vid
            img2vid_prompt = ui.textarea(
                label='Animation Prompt',
                placeholder='Describe the movement or animation you want...'
            ).classes('w-full mb-2').props('outlined rows=2 filled')
            
            # Action button for img2vid
            ui.button('Generate Video from Image', icon='play_circle').classes('w-full bg-green-600 text-white')
        
        # === VID2VID Section ===
        with ui.card().classes('w-full p-3'):
            ui.label('Video to Video').classes('text-lg font-semibold mb-2')
            
            # Instruction for vid2vid
            with ui.card().classes('w-full p-2 bg-purple-50'):
                ui.label('Transform existing videos with new styles or effects').classes('text-sm text-gray-700')
            
            # Prompt input for vid2vid
            vid2vid_prompt = ui.textarea(
                label='Transformation Prompt',
                placeholder='Describe how to transform the video...'
            ).classes('w-full mb-2').props('outlined rows=2 filled')
            
            # Action button for vid2vid
            ui.button('Transform Video', icon='transform').classes('w-full bg-purple-600 text-white')

def create_character_generation_ui():
    """Create the Character Generation column UI - functional with save/load"""
    
    with ui.column().classes('w-full p-6 gap-4'):
        
        # Column Header
        ui.label('Character Generation').classes('text-2xl font-bold text-center mb-3')
        
        # Current Avatar Info
        with ui.card().classes('w-full p-3 bg-blue-50'):
            ui.label(f'Editing: {current_avatar_name}').classes('font-semibold mb-1')
            ui.label('Describe your avatar character in detail. This description will be saved to your avatar.').classes('text-sm text-gray-700')
        
        # Character Description Input
        character_input = ui.textarea(
            label='Avatar Character Description',
            placeholder='Describe your avatar character in detail...\n\nExample: A wise elderly professor with gray hair, wearing Victorian-era clothing, kind eyes, and a gentle smile. Should appear scholarly and approachable with a passion for scientific discovery.'
        ).classes('w-full').props('outlined rows=12 filled')
        
        # Load current avatar's description
        def load_character_description():
            """Load the current avatar's character description"""
            if AVATAR_MANAGER_AVAILABLE and current_avatar_name:
                try:
                    avatar_data = avatar_manager_instance.load_avatar(current_avatar_name)
                    if avatar_data and 'character_description' in avatar_data:
                        character_input.value = avatar_data['character_description']
                        print(f"[CHARACTER GENERATION] Loaded description for '{current_avatar_name}': {len(avatar_data['character_description'])} characters")
                    else:
                        character_input.value = ""
                        print(f"[CHARACTER GENERATION] No description found for '{current_avatar_name}'")
                except Exception as e:
                    print(f"[CHARACTER GENERATION] Error loading description: {e}")
                    character_input.value = ""
        
        # Save character description
        def save_character_description():
            """Save the character description to the current avatar"""
            if not AVATAR_MANAGER_AVAILABLE:
                ui.notify("Avatar manager not available", type='error')
                return
            
            if not current_avatar_name or current_avatar_name.strip() == "":
                ui.notify("No avatar selected", type='error')
                return
            
            try:
                # Load current avatar data
                avatar_data = avatar_manager_instance.load_avatar(current_avatar_name)
                if not avatar_data:
                    # Create basic avatar data if none exists
                    avatar_data = {
                        'name': current_avatar_name,
                        'portrait_prompt': '',
                        'personality': '',
                        'character_description': ''
                    }
                
                # Update character description
                avatar_data['character_description'] = character_input.value or ""
                
                # Save updated avatar data
                success = avatar_manager_instance.save_avatar(avatar_data)
                if success:
                    ui.notify(f"Character description saved for '{current_avatar_name}'!", type='positive')
                    print(f"[CHARACTER GENERATION] Saved description for '{current_avatar_name}': {len(character_input.value)} characters")
                    
                    # Update avatar info display
                    update_avatar_info_display()
                else:
                    ui.notify("Failed to save character description", type='error')
                    
            except Exception as e:
                print(f"[CHARACTER GENERATION] Error saving description: {e}")
                ui.notify(f"Error saving description: {str(e)}", type='error')
        
        # Clear description
        def clear_character_description():
            """Clear the character description"""
            character_input.value = ""
            ui.notify("Description cleared (not saved yet)")
        
        # Action buttons
        with ui.row().classes('w-full gap-2 mt-4'):
            ui.button('Save Description', icon='save').classes('flex-1 bg-green-600 text-white').on('click', save_character_description)
            ui.button('Clear', icon='clear').classes('bg-gray-500 text-white').on('click', clear_character_description)
        
        # Status info
        with ui.card().classes('w-full p-3 bg-gray-50 mt-4'):
            ui.label('Status').classes('font-semibold mb-1')
            status_label = ui.label('Ready to edit character description').classes('text-sm text-gray-600')
            
            def update_status():
                """Update the status based on current content"""
                char_count = len(character_input.value) if character_input.value else 0
                if char_count > 0:
                    status_label.text = f'Description length: {char_count} characters (unsaved changes)'
                else:
                    status_label.text = 'No description entered'
            
            # Update status when text changes
            character_input.on('input', lambda: update_status())
        
        # Load description when the UI is created
        load_character_description()
        
        # Store reference for global access
        if not hasattr(create_character_generation_ui, 'instances'):
            create_character_generation_ui.instances = {}
        create_character_generation_ui.instances[current_avatar_name] = {
            'input': character_input,
            'load_func': load_character_description
        }

def create_placeholder_column_1():
    """Create first placeholder column for second row"""
    
    with ui.column().classes('w-full p-6 gap-4'):
        
        # Column Header
        ui.label('Placeholder Column 1').classes('text-2xl font-bold text-center mb-4')
        
        # Placeholder content
        with ui.card().classes('w-full p-4 bg-gray-50'):
            ui.label('Future Feature').classes('font-semibold mb-2')
            ui.label('This column is reserved for future functionality.').classes('text-sm text-gray-700')
        
        # Placeholder form elements
        ui.input('Placeholder Input').classes('w-full mb-3').props('outlined')
        
        ui.textarea(
            label='Placeholder Text Area',
            placeholder='This is a placeholder for future content...'
        ).classes('w-full mb-3').props('outlined rows=5')
        
        ui.button('Placeholder Action', icon='settings').classes('w-full bg-gray-600 text-white')

def create_placeholder_column_2():
    """Create second placeholder column for second row"""
    
    with ui.column().classes('w-full p-6 gap-4'):
        
        # Column Header
        ui.label('Placeholder Column 2').classes('text-2xl font-bold text-center mb-4')
        
        # Placeholder content
        with ui.card().classes('w-full p-4 bg-gray-50'):
            ui.label('Coming Soon').classes('font-semibold mb-2')
            ui.label('Additional avatar creation tools will be added here.').classes('text-sm text-gray-700')
        
        # Placeholder controls
        ui.select(
            ['Option 1', 'Option 2', 'Option 3'],
            label='Placeholder Select',
            value='Option 1'
        ).classes('w-full mb-3').props('outlined')
        
        with ui.row().classes('w-full gap-2 mb-3'):
            ui.checkbox('Placeholder Option 1')
            ui.checkbox('Placeholder Option 2')
        
        ui.button('Placeholder Function', icon='extension').classes('w-full bg-gray-600 text-white')

def create_placeholder_column_3():
    """Create third placeholder column for second row"""
    
    with ui.column().classes('w-full p-6 gap-4'):
        
        # Column Header
        ui.label('Placeholder Column 3').classes('text-2xl font-bold text-center mb-4')
        
        # Placeholder content
        with ui.card().classes('w-full p-4 bg-gray-50'):
            ui.label('Under Development').classes('font-semibold mb-2')
            ui.label('Advanced avatar customization features will be implemented here.').classes('text-sm text-gray-700')
        
        # Placeholder interface elements
        ui.label('Configuration Settings').classes('text-lg font-semibold mb-2')
        
        with ui.card().classes('w-full p-3 mb-3'):
            ui.label('Setting Category 1').classes('font-medium mb-1')
            ui.slider(min=0, max=100, value=50).classes('w-full')
        
        with ui.card().classes('w-full p-3 mb-3'):
            ui.label('Setting Category 2').classes('font-medium mb-1')
            ui.slider(min=0, max=100, value=75).classes('w-full')
        
        ui.button('Apply Settings', icon='check').classes('w-full bg-gray-600 text-white')

def create_avatar_creation_page():
    """Create the Avatar Creation page with two rows of columns"""
    
    # Main Content Area - Vertical scrolling with two rows
    with ui.scroll_area().classes('w-full min-h-screen bg-gray-100'):
        with ui.column().classes('p-6 gap-6'):
            
            # FIRST ROW - Original 3 columns with fixed height
            ui.label('Avatar Creation Tools').classes('text-3xl font-bold text-center mb-4')
            
            with ui.row().classes('gap-6 justify-center').style('min-width: fit-content; flex-wrap: nowrap;'):
                
                # Portrait Creator Column - FIXED 400px width x 900px height
                with ui.card().classes('').style('width: 400px; height: 900px; flex-shrink: 0; overflow-y: auto;'):
                    create_portrait_creator_ui()
                
                # Video Creator Column - FIXED 400px width x 900px height  
                with ui.card().classes('').style('width: 400px; height: 900px; flex-shrink: 0; overflow-y: auto;'):
                    create_video_creator_ui()
                
                # Character Generation Column - FIXED 400px width x 900px height
                with ui.card().classes('').style('width: 400px; height: 900px; flex-shrink: 0; overflow-y: auto;'):
                    create_character_generation_ui()
            
            # SECOND ROW - New 3 placeholder columns with same dimensions
            ui.label('Additional Tools').classes('text-3xl font-bold text-center mb-4 mt-8')
            
            with ui.row().classes('gap-6 justify-center').style('min-width: fit-content; flex-wrap: nowrap;'):
                
                # Placeholder Column 1 - FIXED 400px width x 900px height
                with ui.card().classes('').style('width: 400px; height: 900px; flex-shrink: 0; overflow-y: auto;'):
                    create_placeholder_column_1()
                
                # Placeholder Column 2 - FIXED 400px width x 900px height
                with ui.card().classes('').style('width: 400px; height: 900px; flex-shrink: 0; overflow-y: auto;'):
                    create_placeholder_column_2()
                
                # Placeholder Column 3 - FIXED 400px width x 900px height
                with ui.card().classes('').style('width: 400px; height: 900px; flex-shrink: 0; overflow-y: auto;'):
                    create_placeholder_column_3()

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
            with ui.card().classes('min-h-96').style('width: 400px; flex-shrink: 0;'):
                create_asset_search_ui()
            
            # Asset Organization Column
            with ui.card().classes('min-h-96').style('width: 400px; flex-shrink: 0;'):
                create_asset_organization_ui()

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
    
    if AVATAR_MANAGER_AVAILABLE:
        print(f"[CREATION KIT] Avatar Manager: Available")
    else:
        print(f"[CREATION KIT] Avatar Manager: Unavailable (avatar_manager.py not found)")
    
    if CHARACTER_CREATOR_AVAILABLE:
        print(f"[CREATION KIT] Character Creator: Available")
    else:
        print(f"[CREATION KIT] Character Creator: Unavailable (character_creator.py not found)")
    
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
        
        /* SVG canvas styling */
        svg {
            border: 1px solid #ccc;
            border-radius: 8px;
        }
        
        /* Node styling */
        .node-selected {
            stroke: #ff6b35;
            stroke-width: 3px;
        }
        
        /* Connection line styling */
        .connection-line {
            stroke: #3b82f6;
            stroke-width: 2px;
            marker-end: url(#arrowhead);
        }
        
        /* Canvas background */
        .canvas-background {
            background-image: 
                linear-gradient(rgba(0,0,0,.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0,0,0,.1) 1px, transparent 1px);
            background-size: 20px 20px;
        }
        
        /* Character Creator specific styling */
        .character-creator-step {
            min-height: 600px;
        }
        
        /* Gallery-style navigation */
        .step-content {
            animation: fadeIn 0.3s ease-in-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        /* Node grid styling */
        .node-grid-item {
            transition: transform 0.2s ease;
        }
        
        .node-grid-item:hover {
            transform: scale(1.02);
        }
        
        /* Upload area styling */
        .upload-area {
            border: 2px dashed #d1d5db;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .upload-area:hover {
            border-color: #3b82f6;
            background-color: #f8fafc;
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