# character_creator.py - Fixed Character Creator Component
import os
import base64
from nicegui import ui
from typing import Dict, List, Optional, Any

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

class CharacterCreator:
    """Character Creator component with state management"""
    
    def __init__(self):
        self.step = 1
        self.data = {
            'name': '',
            'portrait_prompt': '',
            'portrait_image': None,
            'nodes': [],
            'personality': ''
        }
        # Store UI component references to update them when navigating
        self.ui_refs = {}
    
    def reset_data(self):
        """Reset character creator data"""
        self.data = {
            'name': '',
            'portrait_prompt': '',
            'portrait_image': None,
            'nodes': [],
            'personality': ''
        }
        self.step = 1
        self.ui_refs = {}
    
    def update_data(self, key, value):
        """Update character creator data"""
        self.data[key] = value
        print(f"[CHARACTER CREATOR] Updated {key}: {value}")  # Debug logging
    
    def load_from_avatar_data(self, avatar_data):
        """Load existing avatar data into character creator"""
        try:
            # Reset character creator data
            self.data = {
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
                        self.data['portrait_image'] = f"data:{image_type};base64,{base64_data}"
            
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
                
                self.data['nodes'].append(node)
            
            print(f"[CHARACTER CREATOR] Loaded avatar data: {self.data['name']}")
            return True
            
        except Exception as e:
            print(f"[CHARACTER CREATOR] Error loading avatar data: {e}")
            return False

    def create_step1(self):
        """Character Creator Step 1: Name and Portrait"""
        
        with ui.column().classes('w-full gap-4'):
            # Section header
            ui.label('Character Identity').classes('text-xl font-bold text-blue-600 mb-2')
            
            # Section 1: Character Name
            with ui.card().classes('w-full p-4'):
                ui.label('Character Name').classes('text-lg font-bold mb-1')
                
                with ui.card().classes('w-full p-3 bg-blue-50 mb-3'):
                    ui.label('Enter a name for your new avatar character').classes('text-sm text-gray-700')
                
                # Fixed: Use bind_value to properly connect the input to our data
                name_input = ui.input(
                    label='Avatar Name',
                    placeholder='Enter character name...',
                    value=self.data['name']
                ).classes('w-full text-lg').props('outlined')
                
                # Store reference and bind properly
                self.ui_refs['name_input'] = name_input
                
                # Use bind_value for two-way binding
                def update_name():
                    self.data['name'] = name_input.value
                    print(f"[CHARACTER CREATOR] Name updated to: '{name_input.value}'")
                
                # Bind on multiple events to catch all changes
                name_input.on_value_change(update_name)
                name_input.on('input', update_name)
                name_input.on('change', update_name)
            
            # Section 2: Portrait Generation
            with ui.card().classes('w-full p-4'):
                ui.label('Character Portrait').classes('text-lg font-bold mb-1')
                
                with ui.card().classes('w-full p-3 bg-green-50 mb-3'):
                    ui.label('Generate a portrait using AI or upload an existing image').classes('text-sm text-gray-700')
                
                # Portrait prompt input
                portrait_prompt = ui.textarea(
                    label='Portrait Description',
                    placeholder='Describe your character\'s appearance... Example: A wise elderly scientist with gray hair, wearing a Victorian-era coat, kind eyes, and a thoughtful expression',
                    value=self.data['portrait_prompt']
                ).classes('w-full mb-3').props('outlined rows=4 filled')
                
                # Store reference and bind properly
                self.ui_refs['portrait_prompt'] = portrait_prompt
                
                def update_portrait_prompt():
                    self.data['portrait_prompt'] = portrait_prompt.value
                
                portrait_prompt.on_value_change(update_portrait_prompt)
                portrait_prompt.on('input', update_portrait_prompt)
                
                # Generate button right after AI prompt
                ui.button('Generate Portrait from AI', icon='auto_awesome').classes('w-full bg-green-600 text-white mb-4')
                
                # Single drag & drop area for image upload
                image_container = ui.column().classes('w-full')
                
                def refresh_image_display():
                    image_container.clear()
                    with image_container:
                        if self.data['portrait_image']:
                            # Show uploaded image
                            with ui.card().classes('w-full p-4 border-2 border-green-500'):
                                ui.image(self.data['portrait_image']).classes('w-full max-h-64 object-contain rounded')
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
                    self.data['portrait_image'] = None
                    refresh_image_display()
                    ui.notify("Portrait image removed")
                
                def handle_portrait_upload_and_refresh(event):
                    if event.content:
                        # Create a data URL for the image
                        file_content = event.content.read()
                        file_type = event.type or 'image/png'
                        base64_content = base64.b64encode(file_content).decode()
                        self.data['portrait_image'] = f"data:{file_type};base64,{base64_content}"
                        refresh_image_display()
                        ui.notify("Portrait uploaded successfully!")
                
                # Initial display
                refresh_image_display()

    def create_step2(self):
        """Character Creator Step 2: Node Creation"""
        
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
                            self.data['nodes'].append(new_node)
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
                    if self.data['nodes']:
                        with ui.card().classes('w-full p-4'):
                            ui.label(f'Created Nodes ({len(self.data["nodes"])})').classes('text-lg font-semibold mb-4')
                            
                            with ui.grid(columns=2).classes('w-full gap-4'):
                                for i, node in enumerate(self.data['nodes']):
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
                if 0 <= index < len(self.data['nodes']):
                    deleted_node = self.data['nodes'].pop(index)
                    refresh_nodes_display()
                    ui.notify(f"Deleted node: {deleted_node.name}")
            
            # Initial display
            refresh_nodes_display()

    def create_step3(self):
        """Character Creator Step 3: Personality"""
        
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
                    value=self.data['personality']
                ).classes('w-full').props('outlined rows=12 filled')
                
                # Store reference and bind properly
                self.ui_refs['personality_input'] = personality_input
                
                def update_personality():
                    self.data['personality'] = personality_input.value
                    # Force refresh summary when personality changes
                    ui.timer(0.1, refresh_summary, once=True)
                
                personality_input.on_value_change(update_personality)
                personality_input.on('input', update_personality)
            
            # Character Summary
            with ui.card().classes('w-full p-4 bg-blue-50'):
                ui.label('Character Summary').classes('text-lg font-bold mb-1')
                
                summary_container = ui.column().classes('w-full')
                
                def refresh_summary():
                    summary_container.clear()
                    with summary_container:
                        print(f"[CHARACTER CREATOR] Summary - Name: '{self.data['name']}', Portrait: {bool(self.data['portrait_image'])}, Nodes: {len(self.data['nodes'])}, Personality: {len(self.data['personality'])} chars")
                        
                        # Name
                        with ui.row().classes('w-full items-center mb-2'):
                            ui.icon('person', size='1.5rem').classes('text-blue-600 mr-2')
                            ui.label('Name:').classes('font-semibold mr-2')
                            name_text = self.data['name'] if self.data['name'] and self.data['name'].strip() else 'Not set'
                            ui.label(name_text).classes('text-gray-700')
                        
                        # Portrait
                        with ui.row().classes('w-full items-center mb-2'):
                            ui.icon('portrait', size='1.5rem').classes('text-blue-600 mr-2')
                            ui.label('Portrait:').classes('font-semibold mr-2')
                            if self.data['portrait_image']:
                                ui.label('Image uploaded').classes('text-green-600')
                            elif self.data['portrait_prompt'] and self.data['portrait_prompt'].strip():
                                ui.label('AI prompt ready').classes('text-blue-600')
                            else:
                                ui.label('Not set').classes('text-gray-700')
                        
                        # Nodes
                        with ui.row().classes('w-full items-center mb-2'):
                            ui.icon('account_tree', size='1.5rem').classes('text-blue-600 mr-2')
                            ui.label('Nodes:').classes('font-semibold mr-2')
                            ui.label(f'{len(self.data["nodes"])} created').classes('text-gray-700')
                        
                        # Personality
                        with ui.row().classes('w-full items-center mb-2'):
                            ui.icon('psychology', size='1.5rem').classes('text-blue-600 mr-2')
                            ui.label('Personality:').classes('font-semibold mr-2')
                            if self.data['personality'] and self.data['personality'].strip():
                                ui.label(f'{len(self.data["personality"])} characters').classes('text-gray-700')
                            else:
                                ui.label('Not set').classes('text-gray-700')
                
                refresh_summary()

    def save_current_step_data(self):
        """Save data from current step before navigating"""
        try:
            if self.step == 1 and 'name_input' in self.ui_refs:
                self.data['name'] = self.ui_refs['name_input'].value or ''
                if 'portrait_prompt' in self.ui_refs:
                    self.data['portrait_prompt'] = self.ui_refs['portrait_prompt'].value or ''
            elif self.step == 3 and 'personality_input' in self.ui_refs:
                self.data['personality'] = self.ui_refs['personality_input'].value or ''
            
            print(f"[CHARACTER CREATOR] Saved step {self.step} data: name='{self.data['name']}'")
        except Exception as e:
            print(f"[CHARACTER CREATOR] Error saving step data: {e}")

    def create_page(self, save_callback=None, exit_callback=None):
        """Create the Character Creator page with step navigation"""
        
        # Define navigation functions
        def previous_step():
            if self.step > 1:
                # Save current form values before navigating
                self.save_current_step_data()
                self.step -= 1
                update_step_content()
        
        def next_step():
            # Save current form values before navigating
            self.save_current_step_data()
            
            if self.step < 3:
                self.step += 1
                update_step_content()
            elif self.step == 3:
                # Finish character creation
                finish_character_creation()
        
        def finish_character_creation():
            # Final save of current form data
            self.save_current_step_data()
            
            print(f"[CHARACTER CREATOR] Finishing with data: {self.data}")
            
            # Validate required fields
            if not self.data['name'] or not self.data['name'].strip():
                ui.notify("Please enter a character name", type='error')
                return
            
            # Save the character using callback
            if save_callback and save_callback(self.data):
                if exit_callback:
                    exit_callback()
            else:
                ui.notify("Failed to save character. Please try again.", type='error')
        
        def exit_character_creator():
            self.step = 1
            if exit_callback:
                exit_callback()
            else:
                ui.notify("Error: Cannot return to main page")
        
        # Main Content Area - Centered
        with ui.column().classes('w-full min-h-screen bg-gray-100 flex items-center justify-center p-6'):
            
            # Character Creator Card - Fixed width
            with ui.card().classes('w-full max-w-2xl').style('width: 600px; min-height: 700px;'):
                with ui.column().classes('w-full p-6 gap-6'):
                    
                    # Header with step indicator
                    with ui.column().classes('w-full items-center mb-2'):
                        ui.label('Character Creator').classes('text-3xl font-bold text-blue-700 mb-1')
                        
                        # Step progress indicator
                        with ui.row().classes('gap-2 items-center mb-1'):
                            for i in range(1, 4):
                                if i == self.step:
                                    ui.element('div').classes('w-3 h-3 rounded-full bg-blue-600')
                                else:
                                    ui.element('div').classes('w-3 h-3 rounded-full bg-gray-300')
                                if i < 3:
                                    ui.element('div').classes('w-8 h-0.5 bg-gray-300')
                        
                        step_label = ui.label(f'Step {self.step} of 3').classes('text-lg font-semibold text-gray-600')
                    
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
                self.ui_refs.clear()  # Clear old references
                
                with content_container:
                    if self.step == 1:
                        self.create_step1()
                    elif self.step == 2:
                        self.create_step2()
                    elif self.step == 3:
                        self.create_step3()
                
                # Update navigation buttons
                back_btn.props(f'disable={self.step == 1}')
                
                if self.step == 3:
                    next_btn.set_text('Finish & Save')
                    next_btn.props('icon=save')
                else:
                    next_btn.set_text('Next')
                    next_btn.props('icon=arrow_forward')
                
                step_label.set_text(f'Step {self.step} of 3')
            
            # Initial content load
            update_step_content()