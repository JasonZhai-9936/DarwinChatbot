# avatar_manager.py - Fixed Avatar Management System
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

class AvatarManager:
    """Simplified avatar management - avatar.json for general info only, node_network.json for nodes"""
    
    def __init__(self, scripts_dir: str):
        self.scripts_dir = Path(scripts_dir)
        self.project_root = self.scripts_dir.parent.parent  # Go up to DarwinChatbot/
        self.avatars_dir = self.project_root / "avatars"
        
        # Ensure avatars directory exists
        self.avatars_dir.mkdir(exist_ok=True)
        
        print(f"[AVATAR MANAGER] Initialized")
        print(f"[AVATAR MANAGER] Avatars directory: {self.avatars_dir}")
    
    def get_avatar_directory(self, avatar_name: str) -> Path:
        """Get the directory path for a specific avatar"""
        safe_name = self._sanitize_filename(avatar_name)
        return self.avatars_dir / safe_name
    
    def _sanitize_filename(self, name: str) -> str:
        """Convert name to safe filename"""
        import re
        safe_name = re.sub(r'[^\w\s-]', '', name)
        safe_name = re.sub(r'[-\s]+', '_', safe_name)
        return safe_name.lower().strip('_')
    
    def save_avatar(self, avatar_data: Dict[str, Any]) -> bool:
        """Save avatar-level data only (no nodes) to avatar.json"""
        try:
            avatar_name = avatar_data.get('name', 'unnamed_avatar')
            avatar_dir = self.get_avatar_directory(avatar_name)
            
            # Create avatar directory structure
            avatar_dir.mkdir(exist_ok=True)
            (avatar_dir / "images").mkdir(exist_ok=True)
            (avatar_dir / "nodes").mkdir(exist_ok=True)
            
            # Process avatar-level data only (exclude nodes)
            processed_data = self._process_avatar_level_data(avatar_data, avatar_dir)
            
            # Add/update metadata
            if 'metadata' not in processed_data:
                processed_data['metadata'] = {
                    'created': datetime.now().isoformat(),
                    'version': '1.0'
                }
            processed_data['metadata']['last_modified'] = datetime.now().isoformat()
            
            # Add reference to node data file
            processed_data['node_file'] = 'node_network.json'
            
            # Save avatar.json (without node data)
            avatar_json_path = avatar_dir / "avatar.json"
            with open(avatar_json_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
            print(f"[AVATAR MANAGER] Saved avatar info for '{avatar_name}' to {avatar_dir}")
            print(f"[AVATAR MANAGER] Node data managed separately in node_network.json")
            return True
            
        except Exception as e:
            print(f"[AVATAR MANAGER] Error saving avatar: {e}")
            return False
    
    def _process_avatar_level_data(self, avatar_data: Dict[str, Any], avatar_dir: Path) -> Dict[str, Any]:
        """Process only avatar-level data (name, portrait, personality, character_description)"""
        processed_data = {
            'name': avatar_data.get('name', 'unnamed_avatar'),
            'portrait_prompt': avatar_data.get('portrait_prompt', ''),
            'personality': avatar_data.get('personality', ''),
            'character_description': avatar_data.get('character_description', ''),  # Added this field
        }
        
        # Process portrait image if provided
        if 'portrait_image' in avatar_data and avatar_data['portrait_image']:
            portrait_path = self._save_image_data(
                avatar_data['portrait_image'], 
                avatar_dir / "images" / "portrait.png"
            )
            if portrait_path:
                processed_data['portrait_image_path'] = str(portrait_path.relative_to(avatar_dir))
        
        # Preserve existing portrait path if no new image provided
        elif 'portrait_image_path' in avatar_data:
            processed_data['portrait_image_path'] = avatar_data['portrait_image_path']
        
        # Copy metadata if it exists
        if 'metadata' in avatar_data:
            processed_data['metadata'] = avatar_data['metadata'].copy()
        
        return processed_data
    
    def _save_image_data(self, image_data: str, target_path: Path) -> Optional[Path]:
        """Save base64 image data to file"""
        try:
            if image_data.startswith('data:'):
                # Extract base64 data from data URL
                header, data = image_data.split(',', 1)
                import base64
                image_bytes = base64.b64decode(data)
            else:
                # Assume it's already base64
                import base64
                image_bytes = base64.b64decode(image_data)
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'wb') as f:
                f.write(image_bytes)
            
            return target_path
            
        except Exception as e:
            print(f"[AVATAR MANAGER] Error saving image to {target_path}: {e}")
            return None
    
    def load_avatar(self, avatar_name: str) -> Optional[Dict[str, Any]]:
        """Load avatar data from avatar.json and node_network.json"""
        try:
            avatar_dir = self.get_avatar_directory(avatar_name)
            avatar_json_path = avatar_dir / "avatar.json"
            
            if not avatar_json_path.exists():
                print(f"[AVATAR MANAGER] Avatar '{avatar_name}' not found")
                return None
            
            # Load avatar-level data
            with open(avatar_json_path, 'r', encoding='utf-8') as f:
                avatar_data = json.load(f)
            
            # Load node data from node_network.json if it exists
            node_network_path = avatar_dir / "node_network.json"
            if node_network_path.exists():
                with open(node_network_path, 'r', encoding='utf-8') as f:
                    node_data = json.load(f)
                
                # Add nodes to avatar data for compatibility
                avatar_data['nodes'] = list(node_data.get('nodes', {}).values())
                avatar_data['grid_size'] = node_data.get('grid_size', 9)
            else:
                avatar_data['nodes'] = []
                avatar_data['grid_size'] = 9
            
            # Convert relative paths to absolute for use in app
            avatar_data = self._resolve_avatar_paths(avatar_data, avatar_dir)
            
            print(f"[AVATAR MANAGER] Loaded avatar '{avatar_name}' (avatar info + node data)")
            return avatar_data
            
        except Exception as e:
            print(f"[AVATAR MANAGER] Error loading avatar '{avatar_name}': {e}")
            return None
    
    def _resolve_avatar_paths(self, avatar_data: Dict[str, Any], avatar_dir: Path) -> Dict[str, Any]:
        """Convert relative paths to absolute paths"""
        # Resolve portrait image path
        if 'portrait_image_path' in avatar_data:
            full_path = avatar_dir / avatar_data['portrait_image_path']
            if full_path.exists():
                avatar_data['portrait_image_path'] = str(full_path)
        
        # Resolve node image paths (for compatibility)
        if 'nodes' in avatar_data:
            for node in avatar_data['nodes']:
                if 'image_path' in node and node['image_path']:
                    if not os.path.isabs(node['image_path']):
                        full_path = avatar_dir / node['image_path']
                        if full_path.exists():
                            node['image_path'] = str(full_path)
        
        return avatar_data
    
    def list_avatars(self) -> List[Dict[str, Any]]:
        """List all available avatars with basic info"""
        avatars = []
        
        try:
            for avatar_dir in self.avatars_dir.iterdir():
                if avatar_dir.is_dir():
                    avatar_json_path = avatar_dir / "avatar.json"
                    if avatar_json_path.exists():
                        try:
                            with open(avatar_json_path, 'r', encoding='utf-8') as f:
                                avatar_data = json.load(f)
                            
                            # Get node count from node_network.json if exists
                            node_count = 0
                            node_network_path = avatar_dir / "node_network.json"
                            if node_network_path.exists():
                                with open(node_network_path, 'r', encoding='utf-8') as f:
                                    node_data = json.load(f)
                                    node_count = len(node_data.get('nodes', {}))
                            
                            avatars.append({
                                'name': avatar_data.get('name', avatar_dir.name),
                                'directory': avatar_dir.name,
                                'path': str(avatar_dir),
                                'has_portrait': 'portrait_image_path' in avatar_data,
                                'has_personality': bool(avatar_data.get('personality', '').strip()),
                                'has_description': bool(avatar_data.get('character_description', '').strip()),  # Added this
                                'node_count': node_count
                            })
                        except Exception as e:
                            print(f"[AVATAR MANAGER] Error reading avatar in {avatar_dir}: {e}")
            
            # Sort alphabetically
            avatars.sort(key=lambda x: x['name'])
            
        except Exception as e:
            print(f"[AVATAR MANAGER] Error listing avatars: {e}")
        
        return avatars