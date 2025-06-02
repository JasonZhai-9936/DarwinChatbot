# avatar_creation_kit.py - Avatar Creation Kit for Darwin AI (Updated with Avatar Manager)
# Location: Darwinchatbot/scripts/avatar_creation_kit/avatar_creation_kit.py

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
current_page = "avatar_creation"  # Track current page
node_manager_instance = None
avatar_manager_instance = None
current_avatar_name = "Darwin"  # Currently selected avatar
main_update_page_content = None  # Global reference to the main update function

# Character Creator State
character_creator_step = 1
character_creator_data = {
    'name': '',
    'portrait_prompt': '',
    'portrait_image': None,
    'nodes': [],
    'personality': ''
}

class CharacterNode:
    """Simple class to represent nodes in character creation"""
    def __init__(self, name, prompt="", image_path=None, image_data=None):
        self.name = name
        self.prompt = prompt
        self.image_path = image_path
        self.image_data = image_data  # For storing base64 image data
        self.id = f"node_{name.lower().replace(' ', '_')}"
        self.x = 100
        self.y = 100
        self.connections = []

def initialize_managers():
    """Initialize the avatar and node managers"""
    global avatar_manager_instance, node_manager_instance
    
    if AVATAR_MANAGER_AVAILABLE and avatar_manager_instance is None:
        avatar_manager_instance = AvatarManager(SCRIPT_DIR)
    
    if NODE_MANAGER_AVAILABLE and node_manager_instance is None:
        # When loading a specific avatar, we'll update the output directory
        node_manager_instance = NodeManager(OUTPUT_DIR)

def load_avatar_into_node_manager(avatar_name: str):
    """Load avatar data into the node manager"""
    global node_manager_instance
    
    if not (AVATAR_MANAGER_AVAILABLE and NODE_MANAGER_AVAILABLE):
        return False
    
    try:
        avatar_data = avatar_manager_instance.load_avatar(avatar_name)
        if not avatar_data:
            return False
        
        # Update node manager's output directory to avatar-specific path
        avatar_dir = avatar_manager_instance.get_avatar_directory(avatar_name)
        node_manager_instance.output_dir = str(avatar_dir)
        
        # Load nodes from avatar data
        node_manager_instance.nodes.clear()
        node_manager_instance.connections.clear()
        
        nodes_data = avatar_data.get('nodes', [])
        for node_data in nodes_data:
            from node_manager import Node
            node = Node(
                node_data.get('id', f"node_{len(node_manager_instance.nodes)}"),
                node_data.get('name', 'Unnamed'),
                node_data.get('x', 100),
                node_data.get('y', 100),
                node_data.get('image_path')
            )
            node.connections = node_data.get('connections', [])
            node_manager_instance.nodes[node.id] = node
        
        # Load connections
        for node_id, node in node_manager_instance.nodes.items():
            for conn_id in node.connections:
                if conn_id in node_manager_instance.nodes:
                    connection = (node_id, conn_id)
                    reverse_connection = (conn_id, node_id)
                    if connection not in node_manager_instance.connections and reverse_connection not in node_manager_instance.connections:
                        node_manager_instance.connections.append(connection)
        
        print(f"[CREATION KIT] Loaded {len(node_manager_instance.nodes)} nodes for avatar '{avatar_name}'")
        return True
        
    except Exception as e:
        print(f"[CREATION KIT] Error loading avatar into node manager: {e}")
        return False

def save_character_creator_data():
    """Save character creator data as a new avatar"""
    global character_creator_data, current_avatar_name
    
    if not AVATAR_MANAGER_AVAILABLE:
        ui.notify("Avatar manager not available", type='error')
        return False
    
    try:
        # Prepare avatar data for saving
        avatar_data = {
            'name': character_creator_data['name'],
            'portrait_prompt': character_creator_data['portrait_prompt'],
            'personality': character_creator_data['personality'],
            'nodes': []
        }
        
        # Add portrait image if exists
        if character_creator_data['portrait_image']:
            avatar_data['portrait_image'] = character_creator_data['portrait_image']
        
        # Convert CharacterNode objects to dictionaries
        for node in character_creator_data['nodes']:
            node_dict = {
                'id': getattr(node, 'id', f"node_{node.name.lower().replace(' ', '_')}"),
                'name': node.name,
                'prompt': node.prompt,
                'x': getattr(node, 'x', 100),
                'y': getattr(node, 'y', 100),
                'connections': getattr(node, 'connections', [])
            }
            
            # Add image data if exists
            if hasattr(node, 'image_data') and node.image_data:
                node_dict['image_data'] = node.image_data
            elif hasattr(node, 'image_path') and node.image_path:
                node_dict['image_path'] = node.image_path
            
            avatar_data['nodes'].append(node_dict)
        
        # Save the avatar
        success = avatar_manager_instance.save_avatar(avatar_data)
        
        if success:
            # Update current avatar name
            current_avatar_name = character_creator_data['name']
            ui.notify(f"Avatar '{current_avatar_name}' saved successfully!", type='positive')
            return True
        else:
            ui.notify("Failed to save avatar", type='error')
            return False
            
    except Exception as e:
        print(f"[CREATION KIT] Error saving character creator data: {e}")
        ui.notify(f"Error saving avatar: {str(e)}", type='error')
        return False

def load_avatar_into_character_creator(avatar_name: str):
    """Load existing avatar data into character creator"""
    global character_creator_data
    
    if not AVATAR_MANAGER_AVAILABLE:
        return False
    
    try:
        avatar_data = avatar_manager_instance.load_avatar(avatar_name)
        if not avatar_data:
            return False
        
        # Reset character creator data
        character_creator_data = {
            'name': avatar_data.get('name', ''),
            'portrait_prompt': avatar_data.get('portrait_prompt', ''),
            'portrait_image': None,
            'nodes': [],
            'personality': avatar_data.get('personality', '')
        }
        
        # Load portrait image if exists
        if 'portrait_image_path' in avatar_data:
            portrait_path = avatar_data['portrait_image_path']
            if os.path.exists(portrait_path):
                # Convert image to base64 for display
                with open(portrait_path, 'rb') as f:
                    image_data = f.read()
                    image_type = 'image/png'  # Assume PNG for now
                    base64_data = base64.b64encode(image_data).decode()
                    character_creator_data['portrait_image'] = f"data:{image_type};base64,{base64_data}"
        
        # Load nodes
        for node_data in avatar_data.get('nodes', []):
            node = CharacterNode(
                name=node_data.get('name', 'Unnamed'),
                prompt=node_data.get('prompt', '')
            )
            
            # Load node image if exists
            if 'image_path' in node_data and node_data['image_path']:
                if os.path.exists(node_data['image_path']):
                    with open(node_data['image_path'], 'rb') as f:
                        image_data = f.read()
                        image_type = 'image/png'
                        base64_data = base64.b64encode(image_data).decode()
                        node.image_data = f"data:{image_type};base64,{base64_data}"
                        node.image_path = node_data['image_path']
            
            # Set node properties
            node.id = node_data.get('id', f"node_{node.name.lower().replace(' ', '_')}")
            node.x = node_data.get('x', 100)
            node.y = node_data.get('y', 100)
            node.connections = node_data.get('connections', [])
            
            character_creator_data['nodes'].append(node)
        
        print(f"[CREATION KIT] Loaded avatar '{avatar_name}' into character creator")
        return True
        
    except Exception as e:
        print(f"[CREATION KIT] Error loading avatar into character creator: {e}")
        return False

def create_avatar_selector_ui():
    """Create avatar selector with load/save functionality"""
    global current_avatar_name
    
    available_avatars = ['Darwin', 'Einstein', 'Newton', 'Tesla']
    
    # Add saved avatars if avatar manager is available
    if AVATAR_MANAGER_AVAILABLE:
        try:
            saved_avatars = avatar_manager_instance.list_avatars()
            for avatar_info in saved_avatars:
                if avatar_info['name'] not in available_avatars:
                    available_avatars.append(avatar_info['name'])
        except Exception as e:
            print(f"[CREATION KIT] Error loading saved avatars: {e}")
    
    return available_avatars

# [Previous UI creation functions remain the same until create_character_creator_step1...]

def create_character_creator_step1():
    """Character Creator Step 1: Name and Portrait"""
    global character_creator_data
    
    with ui.column().classes('w-full gap-4'):
        # Section header
        ui.label('Character Identity').classes('text-xl font-bold text-blue-600 mb-2')
        
        # Section 1: Character Name
        with ui.card().classes('w-full p-4'):
            ui.label('Character Name').classes('text-lg font-bold mb-1')
            
            with ui.card().classes('w-full p-3 bg-blue-50 mb-3'):
                ui.label('Enter a name for your new avatar character').classes('text-sm text-gray-700')
            
            name_input = ui.input(
                label='Avatar Name',
                placeholder='Enter character name...',
                value=character_creator_data['name']
            ).classes('w-full text-lg').props('outlined')
            
            name_input.on('value-changed', lambda e: update_character_data('name', e.value))
        
        # Section 2: Portrait Generation
        with ui.card().classes('w-full p-4'):
            ui.label('Character Portrait').classes('text-lg font-bold mb-1')
            
            with ui.card().classes('w-full p-3 bg-green-50 mb-3'):
                ui.label('Generate a portrait using AI or upload an existing image').classes('text-sm text-gray-700')
            
            # Portrait prompt input
            portrait_prompt = ui.textarea(
                label='Portrait Description',
                placeholder='Describe your character\'s appearance... Example: A wise elderly scientist with gray hair, wearing a Victorian-era coat, kind eyes, and a thoughtful expression',
                value=character_creator_data['portrait_prompt']
            ).classes('w-full mb-3').props('outlined rows=4 filled')
            
            portrait_prompt.on('value-changed', lambda e: update_character_data('portrait_prompt', e.value))
            
            # Generate button right after AI prompt
            ui.button('Generate Portrait from AI', icon='auto_awesome').classes('w-full bg-green-600 text-white mb-4')
            
            # Single drag & drop area for image upload
            image_container = ui.column().classes('w-full')
            
            def refresh_image_display():
                image_container.clear()
                with image_container:
                    if character_creator_data['portrait_image']:
                        # Show uploaded image
                        with ui.card().classes('w-full p-4 border-2 border-green-500'):
                            ui.image(character_creator_data['portrait_image']).classes('w-full max-h-64 object-contain rounded')
                            ui.button('Remove Image', icon='delete', color='red').classes('w-full mt-2').on('click', lambda: clear_portrait_and_refresh())
                    else:
                        # Show drag & drop zone
                        with ui.card().classes('w-full aspect-video border-2 border-dashed border-gray-300 hover:border-blue-400 transition-colors cursor-pointer'):
                            with ui.column().classes('w-full h-full justify-center items-center p-4'):
                                ui.icon('cloud_upload', size='3rem').classes('text-gray-400')
                                ui.label('Drag & Drop Portrait Here').classes('text-lg font-medium text-gray-600')
                                ui.label('or click to browse').classes('text-sm text-gray-400')
                                
                                # Hidden file input for click-to-browse functionality
                                file_input = ui.upload(
                                    on_upload=lambda e: handle_portrait_upload_and_refresh(e),
                                    max_file_size=10_000_000,
                                    max_files=1,
                                    auto_upload=True
                                ).classes('hidden').props('accept="image/*"')
                                
                                # Make the entire card clickable
                                ui.run_javascript(f"""
                                    const card = document.querySelector('.cursor-pointer');
                                    if (card) {{
                                        card.addEventListener('click', () => {{
                                            const input = card.querySelector('input[type="file"]');
                                            if (input) input.click();
                                        }});
                                    }}
                                """)
            
            def clear_portrait_and_refresh():
                character_creator_data['portrait_image'] = None
                refresh_image_display()
                ui.notify("Portrait image removed")
            
            def handle_portrait_upload_and_refresh(event):
                if event.content:
                    # Create a data URL for the image
                    import base64
                    file_content = event.content.read()
                    file_type = event.type or 'image/png'
                    base64_content = base64.b64encode(file_content).decode()
                    character_creator_data['portrait_image'] = f"data:{file_type};base64,{base64_content}"
                    refresh_image_display()
                    ui.notify("Portrait uploaded successfully!")
            
            # Initial display
            refresh_image_display()

def create_character_creator_step2():
    """Character Creator Step 2: Node Creation"""
    global character_creator_data
    
    with ui.column().classes('w-full gap-4'):
        # Section header
        ui.label('Create Nodes/Keyframes').classes('text-xl font-bold text-blue-600 mb-2')
        
        # Node Creation Section
        with ui.card().classes('w-full p-4'):
            ui.label('Node Creator').classes('text-lg font-bold mb-1')
            
            with ui.card().classes('w-full p-3 bg-purple-50 mb-3'):
                ui.label('Create nodes (keyframes) for your character. Each node represents a different pose, expression, or scene for img2vid generation.').classes('text-sm text-gray-700')
            
            # New node creation form
            with ui.card().classes('w-full p-4 bg-gray-50 mb-3'):
                ui.label('Add New Node').classes('text-lg font-semibold mb-3')
                
                with ui.row().classes('w-full gap-4 mb-3'):
                    new_node_name = ui.input(
                        label='Node Name',
                        placeholder='e.g., Standing, Sitting, Talking...'
                    ).classes('flex-1').props('outlined')
                    
                    add_node_btn = ui.button('Add Node', icon='add').classes('bg-purple-600 text-white')
                
                new_node_prompt = ui.textarea(
                    label='Node Description (Optional)',
                    placeholder='Describe this pose/expression or enter AI generation prompt...'
                ).classes('w-full mb-3').props('outlined rows=2')
                
                # Current uploaded image for new node (stored temporarily)
                current_node_image_data = {'data': None}
                
                # Image upload for new node
                node_image_container = ui.column().classes('w-full')
                
                def refresh_node_image_display():
                    node_image_container.clear()
                    with node_image_container:
                        if current_node_image_data['data']:
                            # Show uploaded image
                            with ui.card().classes('w-full p-3 border-2 border-purple-500 mb-3'):
                                ui.image(current_node_image_data['data']).classes('w-full h-32 object-cover rounded')
                                ui.button('Remove Image', icon='delete', color='red').classes('w-full mt-2').on('click', lambda: clear_node_image_and_refresh())
                        else:
                            # Show drag & drop zone
                            with ui.card().classes('w-full h-32 border-2 border-dashed border-gray-300 hover:border-purple-400 transition-colors cursor-pointer mb-3'):
                                with ui.column().classes('w-full h-full justify-center items-center'):
                                    ui.icon('add_photo_alternate', size='2rem').classes('text-gray-400')
                                    ui.label('Upload Node Image (Optional)').classes('text-sm text-gray-500')
                                    ui.label('Drag & drop or click to browse').classes('text-xs text-gray-400')
                                    
                                    # Hidden file input for click-to-browse functionality
                                    file_input = ui.upload(
                                        on_upload=lambda e: handle_node_image_upload_inline(e),
                                        max_file_size=10_000_000,
                                        max_files=1,
                                        auto_upload=True
                                    ).classes('hidden').props('accept="image/*"')
                                    
                                    # Make the entire card clickable
                                    ui.run_javascript(f"""
                                        setTimeout(() => {{
                                            const cards = document.querySelectorAll('.cursor-pointer');
                                            const card = cards[cards.length - 1]; // Get the last one (most recent)
                                            if (card && !card.hasEventListener) {{
                                                card.hasEventListener = true;
                                                card.addEventListener('click', () => {{
                                                    const input = card.querySelector('input[type="file"]');
                                                    if (input) input.click();
                                                }});
                                            }}
                                        }}, 100);
                                    """)
                
                def clear_node_image_and_refresh():
                    current_node_image_data['data'] = None
                    refresh_node_image_display()
                    ui.notify("Node image removed")
                
                def handle_node_image_upload_inline(event):
                    if event.content:
                        # Create a data URL for the image
                        import base64
                        file_content = event.content.read()
                        file_type = event.type or 'image/png'
                        base64_content = base64.b64encode(file_content).decode()
                        current_node_image_data['data'] = f"data:{file_type};base64,{base64_content}"
                        refresh_node_image_display()
                        ui.notify("Image uploaded for new node")
                
                # Initial display
                refresh_node_image_display()
                
                # Add node button functionality
                def add_new_node():
                    if new_node_name.value.strip():
                        new_node = CharacterNode(
                            name=new_node_name.value.strip(),
                            prompt=new_node_prompt.value,
                            image_data=current_node_image_data['data']
                        )
                        character_creator_data['nodes'].append(new_node)
                        new_node_name.value = ''
                        new_node_prompt.value = ''
                        current_node_image_data['data'] = None
                        refresh_node_image_display()
                        refresh_nodes_display()
                        ui.notify(f"Added node: {new_node.name}")
                
                add_node_btn.on('click', add_new_node)
        
        # Existing nodes display
        nodes_container = ui.column().classes('w-full')
        
        def refresh_nodes_display():
            nodes_container.clear()
            with nodes_container:
                if character_creator_data['nodes']:
                    with ui.card().classes('w-full p-4'):
                        ui.label(f'Created Nodes ({len(character_creator_data["nodes"])})').classes('text-lg font-semibold mb-4')
                        
                        with ui.grid(columns=2).classes('w-full gap-4'):
                            for i, node in enumerate(character_creator_data['nodes']):
                                with ui.card().classes('p-4 border'):
                                    # Node header
                                    with ui.row().classes('w-full justify-between items-center mb-3'):
                                        ui.label(node.name).classes('font-semibold text-lg')
                                        ui.button('', icon='delete', color='red').props('size=sm').on('click', lambda idx=i: delete_node(idx))
                                    
                                    # Node image
                                    if hasattr(node, 'image_data') and node.image_data:
                                        ui.image(node.image_data).classes('w-full h-24 object-cover rounded mb-2')
                                    elif hasattr(node, 'image_path') and node.image_path:
                                        ui.image(node.image_path).classes('w-full h-24 object-cover rounded mb-2')
                                    else:
                                        with ui.card().classes('w-full h-24 bg-gray-100 flex items-center justify-center'):
                                            ui.icon('image', size='2rem').classes('text-gray-400')
                                    
                                    # Node prompt
                                    if node.prompt:
                                        ui.label(node.prompt[:100] + ('...' if len(node.prompt) > 100 else '')).classes('text-sm text-gray-600')
                                    else:
                                        ui.label('No description').classes('text-sm text-gray-400 italic')
                else:
                    with ui.card().classes('w-full p-8 text-center'):
                        ui.icon('account_tree', size='4rem').classes('text-gray-300 mb-4')
                        ui.label('No nodes created yet').classes('text-lg text-gray-500 mb-2')
                        ui.label('Use the form above to create your first node').classes('text-sm text-gray-400')
        
        def delete_node(index):
            if 0 <= index < len(character_creator_data['nodes']):
                deleted_node = character_creator_data['nodes'].pop(index)
                refresh_nodes_display()
                ui.notify(f"Deleted node: {deleted_node.name}")
        
        # Initial display
        refresh_nodes_display()

def create_character_creator_step3():
    """Character Creator Step 3: Personality"""
    global character_creator_data
    
    with ui.column().classes('w-full gap-4'):
        # Section header
        ui.label('Character Personality').classes('text-xl font-bold text-blue-600 mb-2')
        
        # Personality Section
        with ui.card().classes('w-full p-4'):
            ui.label('Avatar Personality').classes('text-lg font-bold mb-1')
            
            with ui.card().classes('w-full p-3 bg-orange-50 mb-3'):
                ui.label('Define how your character behaves, speaks, and interacts. This will guide the AI in generating appropriate responses and mannerisms.').classes('text-sm text-gray-700')
            
            personality_input = ui.textarea(
                label='Character Personality & Behavior',
                placeholder='Describe your avatar character in detail...\n\nExample: A wise and patient educator who speaks thoughtfully and deliberately. Has a gentle demeanor but passionate about scientific discovery. Uses analogies from nature to explain complex concepts. Occasionally shows dry humor and has a habit of stroking his beard when thinking deeply.',
                value=character_creator_data['personality']
            ).classes('w-full').props('outlined rows=12 filled')
            
            personality_input.on('value-changed', lambda e: update_character_data('personality', e.value))
        
        # Character Summary
        with ui.card().classes('w-full p-4 bg-blue-50'):
            ui.label('Character Summary').classes('text-lg font-bold mb-1')
            
            summary_container = ui.column().classes('w-full')
            
            def refresh_summary():
                summary_container.clear()
                with summary_container:
                    # Name
                    with ui.row().classes('w-full items-center mb-2'):
                        ui.icon('person', size='1.5rem').classes('text-blue-600 mr-2')
                        ui.label('Name:').classes('font-semibold mr-2')
                        ui.label(character_creator_data['name'] or 'Not set').classes('text-gray-700')
                    
                    # Portrait
                    with ui.row().classes('w-full items-center mb-2'):
                        ui.icon('portrait', size='1.5rem').classes('text-blue-600 mr-2')
                        ui.label('Portrait:').classes('font-semibold mr-2')
                        if character_creator_data['portrait_image']:
                            ui.label('Image uploaded').classes('text-green-600')
                        elif character_creator_data['portrait_prompt']:
                            ui.label('AI prompt ready').classes('text-blue-600')
                        else:
                            ui.label('Not set').classes('text-gray-700')
                    
                    # Nodes
                    with ui.row().classes('w-full items-center mb-2'):
                        ui.icon('account_tree', size='1.5rem').classes('text-blue-600 mr-2')
                        ui.label('Nodes:').classes('font-semibold mr-2')
                        ui.label(f'{len(character_creator_data["nodes"])} created').classes('text-gray-700')
                    
                    # Personality
                    with ui.row().classes('w-full items-center mb-2'):
                        ui.icon('psychology', size='1.5rem').classes('text-blue-600 mr-2')
                        ui.label('Personality:').classes('font-semibold mr-2')
                        if character_creator_data['personality']:
                            ui.label(f'{len(character_creator_data["personality"])} characters').classes('text-gray-700')
                        else:
                            ui.label('Not set').classes('text-gray-700')
            
            refresh_summary()
            
            # Refresh summary when personality changes
            personality_input.on('value-changed', lambda e: refresh_summary())

def create_character_creator_page():
    """Create the Character Creator page with step navigation in a centered column"""
    global character_creator_step
    
    # Define navigation functions first
    def previous_step():
        global character_creator_step
        if character_creator_step > 1:
            character_creator_step -= 1
            update_step_content()
    
    def next_step():
        global character_creator_step
        if character_creator_step < 3:
            character_creator_step += 1
            update_step_content()
        elif character_creator_step == 3:
            # Finish character creation
            finish_character_creation()
    
    def finish_character_creation():
        # Save the character using avatar manager
        if save_character_creator_data():
            exit_character_creator()
        else:
            ui.notify("Failed to save character. Please try again.", type='error')
    
    def exit_character_creator():
        global current_page, character_creator_step
        character_creator_step = 1
        current_page = "avatar_creation"
        if main_update_page_content:
            main_update_page_content()
        else:
            ui.notify("Error: Cannot return to main page")
    
    # Main Content Area - Similar to other pages but centered
    with ui.column().classes('w-full min-h-screen bg-gray-100 flex items-center justify-center p-6'):
        
        # Character Creator Card - Fixed width like other columns
        with ui.card().classes('w-full max-w-2xl').style('width: 600px; min-height: 700px;'):
            with ui.column().classes('w-full p-6 gap-6'):
                
                # Header with step indicator
                with ui.column().classes('w-full items-center mb-2'):
                    ui.label('Character Creator').classes('text-3xl font-bold text-blue-700 mb-1')
                    
                    # Step progress indicator
                    with ui.row().classes('gap-2 items-center mb-1'):
                        for i in range(1, 4):
                            if i == character_creator_step:
                                ui.element('div').classes('w-3 h-3 rounded-full bg-blue-600')
                            elif i < character_creator_step:
                                ui.element('div').classes('w-3 h-3 rounded-full bg-green-500')
                            else:
                                ui.element('div').classes('w-3 h-3 rounded-full bg-gray-300')
                            if i < 3:
                                ui.element('div').classes('w-8 h-0.5 bg-gray-300')
                    
                    step_label = ui.label(f'Step {character_creator_step} of 3').classes('text-lg font-semibold text-gray-600')
                
                # Content area
                content_container = ui.column().classes('w-full flex-1')
                
                # Navigation buttons at bottom
                with ui.row().classes('w-full justify-between items-center mt-6 pt-4 border-t border-gray-200'):
                    with ui.row().classes('gap-2'):
                        back_btn = ui.button('Back', icon='arrow_back').classes('bg-gray-500 text-white').on('click', previous_step)
                        ui.button('Exit', icon='close').classes('bg-red-500 text-white').on('click', exit_character_creator)
                    
                    next_btn = ui.button('Next', icon='arrow_forward').classes('bg-blue-600 text-white').on('click', next_step)
        
        def update_step_content():
            content_container.clear()
            with content_container:
                if character_creator_step == 1:
                    create_character_creator_step1()
                elif character_creator_step == 2:
                    create_character_creator_step2()
                elif character_creator_step == 3:
                    create_character_creator_step3()
            
            # Update navigation buttons
            back_btn.props(f'disable={character_creator_step == 1}')
            
            if character_creator_step == 3:
                next_btn.set_text('Finish & Save')
                next_btn.props('icon=save')
            else:
                next_btn.set_text('Next')
                next_btn.props('icon=arrow_forward')
            
            step_label.set_text(f'Step {character_creator_step} of 3')
        
        # Initial content load
        update_step_content()

def update_character_data(key, value):
    """Update character creator data"""
    global character_creator_data
    character_creator_data[key] = value

def create_main_ui():
    """Create the main Creation Kit interface with page switching"""
    
    global current_page, main_update_page_content, current_avatar_name
    
    # Initialize managers
    initialize_managers()
    
    # Container for dynamic content
    content_container = ui.column().classes('w-full')
    
    def start_character_creator():
        """Start the character creator workflow"""
        global current_page, character_creator_step, character_creator_data
        
        # Reset character creator data
        character_creator_data = {
            'name': '',
            'portrait_prompt': '',
            'portrait_image': None,
            'nodes': [],
            'personality': ''
        }
        character_creator_step = 1
        current_page = "character_creator"
        
        # Update navigation buttons to show none are active
        create_avatar_button(active=False)
        create_assets_button(active=False)
        create_nodes_button(active=False)
        
        update_page_content()
    
    def load_existing_avatar():
        """Load an existing avatar for editing"""
        if load_avatar_into_character_creator(current_avatar_name):
            start_character_creator()
            ui.notify(f"Loaded avatar '{current_avatar_name}' for editing")
        else:
            ui.notify(f"Could not load avatar '{current_avatar_name}'", type='warning')
    
    def refresh_avatar_selector():
        """Refresh the avatar selector with current avatars"""
        available_avatars = create_avatar_selector_ui()
        avatar_select.options = available_avatars
        avatar_select.update()
    
    # App Header with Navigation
    with ui.header().classes('bg-gray-800 bg-blue-800 text-white px-6 py-4'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('Darwin Avatar Creation Kit').classes('text-xl font-bold')
            
            # Right side: Avatar selector and Navigation buttons
            with ui.row().classes('gap-4 items-center'):
                # Avatar selector with load and new buttons
                with ui.row().classes('gap-2 items-center'):
                    avatar_select = ui.select(
                        create_avatar_selector_ui(),
                        label='Avatar',
                        value=current_avatar_name
                    ).classes('w-48 text-lg bg-blue-500 text-white').props('dense outlined')
                    
                    # Update current avatar when selection changes
                    avatar_select.on('update:model-value', lambda e: update_current_avatar(e.value))

                    load_btn = ui.button('Load', icon='download').classes('bg-green-600 text-white px-2 py-1 text-sm').on('click', load_existing_avatar)
                    new_btn = ui.button('New', icon='add').classes('bg-purple-600 text-white px-2 py-1 text-sm').on('click', start_character_creator)
                    refresh_btn = ui.button('', icon='refresh').classes('bg-gray-600 text-white px-2 py-1 text-sm').on('click', refresh_avatar_selector)
                
                # Navigation buttons
                avatar_btn_container = ui.row()
                assets_btn_container = ui.row()
                nodes_btn_container = ui.row()
    
    def update_current_avatar(new_avatar_name):
        """Update the current avatar selection"""
        global current_avatar_name
        current_avatar_name = new_avatar_name
        
        # If we're on the node manager page, reload it with the new avatar
        if current_page == "node_manager":
            load_avatar_into_node_manager(current_avatar_name)
            update_page_content()
    
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
                create_character_creator_page()
    
    # Make update_page_content globally accessible
    main_update_page_content = update_page_content
    
    # Initial setup
    create_avatar_button(active=True)
    create_assets_button(active=False)
    create_nodes_button(active=False)
    update_page_content()

# [Keep all the other UI creation functions the same - create_portrait_creator_ui, create_video_creator_ui, etc.]

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
        node_manager_instance = NodeManager(OUTPUT_DIR)
    
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
                        ui.notify("Nodes saved to avatar")
                    ])
                    ui.button('Reset Nodes', icon='refresh', color='orange').on('click', lambda: [
                        load_avatar_into_node_manager(current_avatar_name),
                        ui.notify("Nodes reset from avatar data")
                    ])
        
        # Create the node manager UI - full page width
        create_node_manager_ui(node_manager_instance)

def sync_nodes_to_avatar():
    """Sync current node manager state back to avatar data"""
    if not (AVATAR_MANAGER_AVAILABLE and NODE_MANAGER_AVAILABLE):
        return
    
    try:
        # Load current avatar data
        avatar_data = avatar_manager_instance.load_avatar(current_avatar_name)
        if not avatar_data:
            ui.notify("Could not load avatar data for syncing", type='warning')
            return
        
        # Update nodes in avatar data
        avatar_data['nodes'] = []
        for node_id, node in node_manager_instance.nodes.items():
            node_dict = {
                'id': node.id,
                'name': node.name,
                'x': node.x,
                'y': node.y,
                'connections': node.connections.copy(),
                'prompt': ''  # Node manager doesn't store prompts, so keep existing or empty
            }
            
            # Copy image path if exists
            if node.image_path:
                node_dict['image_path'] = node.image_path
            
            avatar_data['nodes'].append(node_dict)
        
        # Save updated avatar data
        success = avatar_manager_instance.save_avatar(avatar_data)
        if success:
            print(f"[CREATION KIT] Synced {len(avatar_data['nodes'])} nodes to avatar '{current_avatar_name}'")
        else:
            ui.notify("Failed to sync nodes to avatar", type='error')
    
    except Exception as e:
        print(f"[CREATION KIT] Error syncing nodes to avatar: {e}")
        ui.notify(f"Error syncing nodes: {str(e)}", type='error')

# Keep the remaining UI creation functions from your original code
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
            with ui.card().classes('min-h-96').style('width: 400px; flex-shrink: 0;'):
                create_asset_search_ui()
            
            # Asset Organization Column
            with ui.card().classes('min-h-96').style('width: 400px; flex-shrink: 0;'):
                create_asset_organization_ui()

def create_avatar_creation_page():
    """Create the Avatar Creation page with horizontal scrolling columns"""
    
    # Main Content Area - Horizontal scrolling container
    with ui.scroll_area().classes('w-full min-h-screen bg-gray-100'):
        with ui.row().classes('p-6 gap-6').style('min-width: fit-content; flex-wrap: nowrap;'):
            
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
    
    if AVATAR_MANAGER_AVAILABLE:
        print(f"[CREATION KIT] Avatar Manager: Available")
    else:
        print(f"[CREATION KIT] Avatar Manager: Unavailable (avatar_manager.py not found)")
    
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