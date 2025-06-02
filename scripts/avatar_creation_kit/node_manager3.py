# node_manager.py - Updated Node Manager with Avatar Integration
import os
import json
from pathlib import Path
from nicegui import ui
from typing import Dict, List, Tuple, Optional, Callable
import random

class Node:
    """Represents a single node in the node network"""
    
    def __init__(self, node_id: str, name: str, x: float, y: float, image_path: str = None):
        self.id = node_id
        self.name = name
        self.x = x
        self.y = y
        self.image_path = image_path
        self.connections: List[str] = []  # List of connected node IDs
        self.prompt = ""  # Add prompt field for avatar integration
    
    def to_dict(self):
        """Convert node to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'image_path': self.image_path,
            'connections': self.connections,
            'prompt': self.prompt
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create node from dictionary"""
        node = cls(data['id'], data['name'], data['x'], data['y'], data.get('image_path'))
        node.connections = data.get('connections', [])
        node.prompt = data.get('prompt', '')
        return node

class NodeManager:
    """Manages the node network and provides visualization with avatar integration"""
    
    def __init__(self, output_dir: str, auto_save_callback: Callable = None):
        self.output_dir = output_dir
        self.nodes: Dict[str, Node] = {}
        self.connections: List[Tuple[str, str]] = []
        self.canvas_width = 1000
        self.canvas_height = 600
        self.node_size = 80
        self.selected_node_id = None
        self.connecting_mode = False
        self.connection_start_id = None
        self.auto_save_callback = auto_save_callback  # Callback to sync with avatar manager
        
        # Load existing nodes if they exist
        self.load_nodes()
    
    def set_auto_save_callback(self, callback: Callable):
        """Set callback function for auto-saving to avatar manager"""
        self.auto_save_callback = callback
    
    def _trigger_auto_save(self):
        """Trigger auto-save callback if set"""
        if self.auto_save_callback:
            try:
                self.auto_save_callback()
            except Exception as e:
                print(f"[NODE MANAGER] Error in auto-save callback: {e}")
    
    def save_nodes(self):
        """Save nodes to JSON file"""
        save_path = os.path.join(self.output_dir, 'node_network.json')
        data = {
            'nodes': {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            'connections': self.connections
        }
        
        os.makedirs(self.output_dir, exist_ok=True)
        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[NODE MANAGER] Saved {len(self.nodes)} nodes to {save_path}")
        
        # Trigger auto-save to avatar manager
        self._trigger_auto_save()
    
    def load_nodes(self):
        """Load nodes from JSON file"""
        save_path = os.path.join(self.output_dir, 'node_network.json')
        if os.path.exists(save_path):
            try:
                with open(save_path, 'r') as f:
                    data = json.load(f)
                
                # Load nodes
                self.nodes.clear()
                for node_id, node_data in data.get('nodes', {}).items():
                    self.nodes[node_id] = Node.from_dict(node_data)
                
                # Load connections
                self.connections = data.get('connections', [])
                
                print(f"[NODE MANAGER] Loaded {len(self.nodes)} nodes from {save_path}")
                
            except Exception as e:
                print(f"[NODE MANAGER] Error loading nodes: {e}")
    
    def load_from_avatar_data(self, nodes_data: List[Dict]):
        """Load nodes from avatar data format"""
        try:
            self.nodes.clear()
            self.connections.clear()
            
            for node_data in nodes_data:
                node = Node.from_dict(node_data)
                self.nodes[node.id] = node
            
            # Rebuild connections from node connection lists
            for node_id, node in self.nodes.items():
                for conn_id in node.connections:
                    if conn_id in self.nodes:
                        connection = (node_id, conn_id)
                        reverse_connection = (conn_id, node_id)
                        if connection not in self.connections and reverse_connection not in self.connections:
                            self.connections.append(connection)
            
            print(f"[NODE MANAGER] Loaded {len(self.nodes)} nodes from avatar data")
            
        except Exception as e:
            print(f"[NODE MANAGER] Error loading from avatar data: {e}")
    
    def create_node(self, name: str, x: float, y: float) -> str:
        """Create a new node and return its ID"""
        node_id = f"node_{len(self.nodes) + 1}"
        self.nodes[node_id] = Node(node_id, name, x, y)
        self.save_nodes()
        return node_id
    
    def delete_node(self, node_id: str):
        """Delete a node and all its connections"""
        if node_id in self.nodes:
            # Remove all connections involving this node
            self.connections = [(a, b) for a, b in self.connections if a != node_id and b != node_id]
            
            # Remove from other nodes' connection lists
            for node in self.nodes.values():
                if node_id in node.connections:
                    node.connections.remove(node_id)
            
            # Delete the node
            del self.nodes[node_id]
            self.save_nodes()
    
    def move_node(self, node_id: str, x: float, y: float):
        """Move a node to new coordinates"""
        if node_id in self.nodes:
            self.nodes[node_id].x = x
            self.nodes[node_id].y = y
            self.save_nodes()
    
    def connect_nodes(self, node1_id: str, node2_id: str):
        """Create a connection between two nodes"""
        if node1_id in self.nodes and node2_id in self.nodes and node1_id != node2_id:
            # Add connection if it doesn't exist
            connection = (node1_id, node2_id)
            reverse_connection = (node2_id, node1_id)
            
            if connection not in self.connections and reverse_connection not in self.connections:
                self.connections.append(connection)
                
                # Update node connection lists
                self.nodes[node1_id].connections.append(node2_id)
                self.nodes[node2_id].connections.append(node1_id)
                
                self.save_nodes()
                return True
        return False
    
    def disconnect_nodes(self, node1_id: str, node2_id: str):
        """Remove connection between two nodes"""
        connection = (node1_id, node2_id)
        reverse_connection = (node2_id, node1_id)
        
        if connection in self.connections:
            self.connections.remove(connection)
        if reverse_connection in self.connections:
            self.connections.remove(reverse_connection)
        
        # Update node connection lists
        if node1_id in self.nodes and node2_id in self.nodes[node1_id].connections:
            self.nodes[node1_id].connections.remove(node2_id)
        if node2_id in self.nodes and node1_id in self.nodes[node2_id].connections:
            self.nodes[node2_id].connections.remove(node1_id)
        
        self.save_nodes()
    
    def update_node_image(self, node_id: str, image_path: str):
        """Update the image for a node"""
        if node_id in self.nodes:
            self.nodes[node_id].image_path = image_path
            self.save_nodes()
    
    def update_node_name(self, node_id: str, name: str):
        """Update the name of a node"""
        if node_id in self.nodes:
            self.nodes[node_id].name = name
            self.save_nodes()
    
    def update_node_prompt(self, node_id: str, prompt: str):
        """Update the prompt for a node"""
        if node_id in self.nodes:
            self.nodes[node_id].prompt = prompt
            self.save_nodes()

def create_node_manager_ui(node_manager: NodeManager):
    """Create the Node Manager UI with avatar integration features"""
    
    # Global UI state
    canvas_container = None
    node_info_container = None
    connection_status_label = None
    
    def refresh_canvas():
        """Refresh the canvas visualization"""
        if canvas_container:
            canvas_container.clear()
            with canvas_container:
                draw_canvas()
    
    def draw_canvas():
        """Draw the node canvas with HTML/CSS"""
        
        # Create canvas with relative positioning
        with ui.element('div').classes('relative border-2 border-gray-300 bg-white rounded-lg').style(
            f'width: {node_manager.canvas_width}px; height: {node_manager.canvas_height}px; '
            'background-image: radial-gradient(circle at 1px 1px, rgba(0,0,0,.15) 1px, transparent 0); '
            'background-size: 20px 20px; overflow: hidden;'
        ):
            
            # Draw connections as lines
            for connection in node_manager.connections:
                node1_id, node2_id = connection
                if node1_id in node_manager.nodes and node2_id in node_manager.nodes:
                    node1 = node_manager.nodes[node1_id]
                    node2 = node_manager.nodes[node2_id]
                    
                    x1 = node1.x + node_manager.node_size/2
                    y1 = node1.y + node_manager.node_size/2
                    x2 = node2.x + node_manager.node_size/2
                    y2 = node2.y + node_manager.node_size/2
                    
                    # Calculate line angle and length
                    import math
                    angle = math.atan2(y2 - y1, x2 - x1)
                    length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    
                    # Draw connection line
                    ui.element('div').classes('absolute bg-blue-500').style(
                        f'left: {x1}px; top: {y1}px; '
                        f'width: {length}px; height: 3px; '
                        f'transform: rotate({angle}rad); '
                        f'transform-origin: 0 50%; '
                        f'z-index: 1;'
                    )
            
            # Draw nodes
            for node_id, node in node_manager.nodes.items():
                is_selected = node_id == node_manager.selected_node_id
                
                # Node container
                with ui.element('div').classes('absolute').style(
                    f'left: {node.x}px; top: {node.y}px; '
                    f'width: {node_manager.node_size}px; height: {node_manager.node_size}px; '
                    f'z-index: 10;'
                ):
                    # Check if node has an image
                    has_image = node.image_path and os.path.exists(node.image_path)
                    
                    if has_image:
                        # Node with image - create clickable image container
                        border_color = 'border-red-500' if is_selected else 'border-blue-600'
                        border_width = 'border-4' if is_selected else 'border-2'
                        
                        with ui.element('div').classes(
                            f'w-full h-full rounded-full overflow-hidden {border_color} {border_width} '
                            'hover:scale-110 transition-transform duration-200 cursor-pointer relative'
                        ).on('click', lambda n_id=node_id: handle_node_click(n_id)):
                            
                            # Display the actual image
                            ui.image(node.image_path).classes(
                                'w-full h-full object-cover'
                            ).style('border-radius: inherit;')
                            
                            # Selection overlay
                            if is_selected:
                                ui.element('div').classes(
                                    'absolute inset-0 bg-orange-400 bg-opacity-30 rounded-full'
                                )
                    
                    else:
                        # Node without image - show colored circle with icon
                        node_color = 'bg-orange-400 border-red-500' if is_selected else 'bg-blue-400 border-blue-600'
                        border_width = 'border-4' if is_selected else 'border-2'
                        
                        node_btn = ui.button('', icon='person').classes(
                            f'w-full h-full rounded-full {node_color} {border_width} '
                            'hover:scale-110 transition-transform duration-200 text-white'
                        ).style('min-width: 0; padding: 0;')
                        
                        # Add click handler
                        node_btn.on('click', lambda n_id=node_id: handle_node_click(n_id))
                    
                    # Node label
                    ui.label(node.name).classes(
                        'absolute -bottom-6 left-1/2 transform -translate-x-1/2 '
                        'text-xs font-semibold text-gray-700 whitespace-nowrap bg-white px-1 rounded'
                    )
    
    def handle_node_click(node_id: str):
        """Handle node click events"""
        if node_manager.connecting_mode:
            # Handle connection mode
            if node_manager.connection_start_id is None:
                node_manager.connection_start_id = node_id
                ui.notify(f"Connection started from {node_manager.nodes[node_id].name}")
                update_connection_status()
            else:
                # Complete connection
                if node_manager.connect_nodes(node_manager.connection_start_id, node_id):
                    ui.notify(f"Connected {node_manager.nodes[node_manager.connection_start_id].name} to {node_manager.nodes[node_id].name}")
                    refresh_canvas()
                else:
                    ui.notify("Connection already exists or invalid")
                node_manager.connection_start_id = None
                update_connection_status()
        else:
            # Select node
            select_node(node_id)
    
    def select_node(node_id: str):
        """Select a node and show its properties"""
        node_manager.selected_node_id = node_id
        refresh_canvas()
        update_node_info()
    
    def update_node_info():
        """Update the node information panel with avatar integration"""
        if node_info_container and node_manager.selected_node_id:
            node_info_container.clear()
            node = node_manager.nodes[node_manager.selected_node_id]
            
            with node_info_container:
                ui.label(f'Selected Node: {node.name}').classes('text-lg font-bold mb-3')
                
                # Node name input
                name_input = ui.input('Node Name', value=node.name).classes('w-full mb-3')
                ui.button('Update Name', icon='edit').on('click', 
                    lambda: update_node_name(name_input.value)).classes('w-full mb-3 bg-blue-600 text-white')
                
                # Node prompt input (new for avatar integration)
                prompt_input = ui.textarea(
                    'Node Prompt/Description', 
                    value=node.prompt,
                    placeholder='Enter a prompt or description for this node...'
                ).classes('w-full mb-3').props('outlined rows=3')
                ui.button('Update Prompt', icon='edit').on('click', 
                    lambda: update_node_prompt(prompt_input.value)).classes('w-full mb-3 bg-green-600 text-white')
                
                # Position info
                ui.label(f'Position: ({int(node.x)}, {int(node.y)})').classes('text-sm text-gray-600 mb-2')
                
                # Image section
                ui.separator().classes('mb-3')
                ui.label('Node Image').classes('font-semibold mb-2')
                
                # Current image display
                if node.image_path and os.path.exists(node.image_path):
                    ui.image(node.image_path).classes('w-24 h-24 object-cover rounded border mb-2')
                    ui.label(f'Current: {os.path.basename(node.image_path)}').classes('text-xs text-gray-600 mb-2')
                else:
                    ui.label('No image assigned').classes('text-sm text-gray-500 mb-2')
                
                # File browser (simplified)
                ui.upload(
                    label='Upload Image',
                    on_upload=lambda e: handle_image_upload(e, node_manager.selected_node_id),
                    max_file_size=10_000_000,
                    max_files=1
                ).classes('w-full mb-3').props('accept="image/*"')
                
                # Connection info
                ui.separator().classes('mb-3')
                ui.label('Connections').classes('font-semibold mb-2')
                ui.label(f'Connected to: {len(node.connections)} nodes').classes('text-sm mb-2')
                
                if node.connections:
                    for conn_id in node.connections:
                        if conn_id in node_manager.nodes:
                            conn_node = node_manager.nodes[conn_id]
                            with ui.row().classes('w-full justify-between items-center mb-1'):
                                ui.label(conn_node.name).classes('text-sm')
                                ui.button('Disconnect', icon='link_off', color='red').props('size=sm').on('click',
                                    lambda c_id=conn_id: disconnect_and_refresh(node_manager.selected_node_id, c_id))
                
                # Actions
                ui.separator().classes('mb-3')
                with ui.row().classes('w-full gap-2'):
                    ui.button('Move Random', icon='shuffle', color='orange').on('click', move_node_random).classes('flex-1')
                    ui.button('Delete Node', icon='delete', color='red').on('click', delete_selected_node).classes('flex-1')
        else:
            # Show default message
            if node_info_container:
                node_info_container.clear()
                with node_info_container:
                    ui.label('Node Properties').classes('text-lg font-semibold mb-3')
                    ui.label('Click on a node to view and edit its properties').classes('text-sm text-gray-500 text-center')
    
    def update_node_name(new_name: str):
        """Update the selected node's name"""
        if node_manager.selected_node_id and new_name.strip():
            node_manager.update_node_name(node_manager.selected_node_id, new_name.strip())
            refresh_canvas()
            update_node_info()
            ui.notify(f"Node renamed to '{new_name}'")
    
    def update_node_prompt(new_prompt: str):
        """Update the selected node's prompt"""
        if node_manager.selected_node_id:
            node_manager.update_node_prompt(node_manager.selected_node_id, new_prompt)
            ui.notify("Node prompt updated")
    
    def move_node_random():
        """Move selected node to random position"""
        if node_manager.selected_node_id:
            x = random.randint(50, node_manager.canvas_width - node_manager.node_size - 50)
            y = random.randint(50, node_manager.canvas_height - node_manager.node_size - 50)
            node_manager.move_node(node_manager.selected_node_id, x, y)
            refresh_canvas()
            update_node_info()
            ui.notify("Node moved to random position")
    
    def disconnect_and_refresh(node1_id: str, node2_id: str):
        """Disconnect nodes and refresh display"""
        node_manager.disconnect_nodes(node1_id, node2_id)
        refresh_canvas()
        update_node_info()
        ui.notify("Nodes disconnected")
    
    def delete_selected_node():
        """Delete the currently selected node"""
        if node_manager.selected_node_id:
            node_name = node_manager.nodes[node_manager.selected_node_id].name
            node_manager.delete_node(node_manager.selected_node_id)
            node_manager.selected_node_id = None
            refresh_canvas()
            update_node_info()
            ui.notify(f"Node '{node_name}' deleted")
    
    def handle_image_upload(event, node_id: str):
        """Handle image upload for a node"""
        if event.content and node_id in node_manager.nodes:
            # Save uploaded file
            filename = f"node_{node_id}_{event.name}"
            filepath = os.path.join(node_manager.output_dir, filename)
            
            try:
                with open(filepath, 'wb') as f:
                    f.write(event.content.read())
                
                # Update node image path
                node_manager.update_node_image(node_id, filepath)
                
                # Force refresh of canvas and node info
                ui.timer(0.1, lambda: [refresh_canvas(), update_node_info()], once=True)
                
                ui.notify(f"Image uploaded and assigned to node")
            except Exception as e:
                ui.notify(f"Error uploading image: {e}")
                print(f"[NODE MANAGER] Error uploading image: {e}")
    
    def create_new_node():
        """Create a new node at a random position"""
        x = random.randint(50, node_manager.canvas_width - node_manager.node_size - 50)
        y = random.randint(50, node_manager.canvas_height - node_manager.node_size - 50)
        node_id = node_manager.create_node(f"Node {len(node_manager.nodes) + 1}", x, y)
        refresh_canvas()
        ui.notify(f"Created new node: {node_manager.nodes[node_id].name}")
    
    def toggle_connection_mode():
        """Toggle connection mode on/off"""
        node_manager.connecting_mode = not node_manager.connecting_mode
        node_manager.connection_start_id = None  # Reset connection state
        update_connection_status()
        ui.notify(f"Connection mode: {'ON' if node_manager.connecting_mode else 'OFF'}")
    
    def update_connection_status():
        """Update connection status label"""
        if connection_status_label:
            if node_manager.connecting_mode:
                if node_manager.connection_start_id:
                    start_name = node_manager.nodes[node_manager.connection_start_id].name
                    connection_status_label.text = f"Connection Mode: ON - Select target for '{start_name}'"
                else:
                    connection_status_label.text = "Connection Mode: ON - Select first node"
            else:
                connection_status_label.text = "Connection Mode: OFF"
    
    def clear_all_nodes():
        """Clear all nodes after confirmation"""
        with ui.dialog() as dialog, ui.card():
            ui.label('Are you sure you want to clear all nodes?').classes('text-lg mb-4')
            ui.label('This action cannot be undone.').classes('text-sm text-red-600 mb-4')
            with ui.row().classes('w-full gap-2'):
                ui.button('Cancel', color='gray').on('click', dialog.close)
                ui.button('Clear All', color='red').on('click', lambda: [
                    node_manager.nodes.clear(),
                    setattr(node_manager, 'connections', []),
                    setattr(node_manager, 'selected_node_id', None),
                    node_manager.save_nodes(),
                    refresh_canvas(),
                    update_node_info(),
                    dialog.close(),
                    ui.notify("All nodes cleared")
                ])
        dialog.open()
    
    def import_nodes_from_avatar():
        """Import nodes from currently selected avatar"""
        ui.notify("This feature will be implemented when integrated with avatar manager")
    
    def export_nodes_to_avatar():
        """Export current nodes to avatar"""
        node_manager.save_nodes()
        ui.notify("Nodes saved and will be synced to avatar")
    
    # Main UI Layout
    with ui.column().classes('w-full p-6 gap-4'):
        
        # Header with avatar integration info
        with ui.row().classes('w-full justify-between items-center mb-4'):
            ui.label('Node Manager').classes('text-3xl font-bold')
            
            # Avatar integration buttons
            with ui.row().classes('gap-2'):
                ui.button('Import from Avatar', icon='download', color='blue').on('click', import_nodes_from_avatar)
                ui.button('Export to Avatar', icon='upload', color='green').on('click', export_nodes_to_avatar)
        
        # Stats row
        with ui.row().classes('w-full gap-4 mb-4 justify-center'):
            ui.label(f'Nodes: {len(node_manager.nodes)}').classes('text-lg font-semibold bg-blue-100 px-3 py-1 rounded')
            ui.label(f'Connections: {len(node_manager.connections)}').classes('text-lg font-semibold bg-green-100 px-3 py-1 rounded')
        
        # Controls Row
        with ui.row().classes('w-full gap-4 mb-4'):
            ui.button('Add Node', icon='add_circle', color='green').on('click', create_new_node)
            ui.button('Connection Mode', icon='link', color='blue').on('click', toggle_connection_mode)
            ui.button('Save Network', icon='save', color='orange').on('click', lambda: [node_manager.save_nodes(), ui.notify("Network saved")])
            ui.button('Clear All', icon='clear_all', color='red').on('click', clear_all_nodes)
        
        # Connection mode status
        connection_status_label = ui.label('Connection Mode: OFF').classes('text-sm font-semibold text-center mb-4')
        
        # Main content area
        with ui.row().classes('w-full gap-6'):
            
            # Canvas area
            with ui.card().classes('flex-1'):
                ui.label('Node Canvas').classes('text-lg font-semibold mb-3')
                ui.label('Click empty space to create nodes, click nodes to select them').classes('text-sm text-gray-600 mb-3')
                
                # Canvas container
                canvas_container = ui.column().classes('w-full')
            
            # Node Info Panel
            with ui.card().classes('w-80'):
                node_info_container = ui.column().classes('w-full')
    
    # Initial setup
    update_connection_status()
    update_node_info()
    refresh_canvas()
    
    # Create some sample nodes if none exist
    if len(node_manager.nodes) == 0:
        node_manager.create_node("Main", 200, 150)
        node_manager.create_node("Secondary", 400, 300)
        node_manager.create_node("Output", 600, 200)
        refresh_canvas()