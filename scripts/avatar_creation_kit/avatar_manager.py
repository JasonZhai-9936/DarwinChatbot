# avatar_manager.py - Avatar Management System for Avatar Creation Kit
import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

class AvatarManager:
    """Manages avatar data persistence and file organization"""
    
    def __init__(self, scripts_dir: str):
        self.scripts_dir = Path(scripts_dir)
        self.project_root = self.scripts_dir.parent.parent  # Go up to DarwinChatbot/
        self.avatars_dir = self.project_root / "avatars"
        
        # Ensure avatars directory exists
        self.avatars_dir.mkdir(exist_ok=True)
        
        print(f"[AVATAR MANAGER] Initialized")
        print(f"[AVATAR MANAGER] Project root: {self.project_root}")
        print(f"[AVATAR MANAGER] Avatars directory: {self.avatars_dir}")
    
    def get_avatar_directory(self, avatar_name: str) -> Path:
        """Get the directory path for a specific avatar"""
        # Sanitize avatar name for file system
        safe_name = self._sanitize_filename(avatar_name)
        return self.avatars_dir / safe_name
    
    def _sanitize_filename(self, name: str) -> str:
        """Convert name to safe filename"""
        import re
        # Replace spaces with underscores, remove special chars, lowercase
        safe_name = re.sub(r'[^\w\s-]', '', name)
        safe_name = re.sub(r'[-\s]+', '_', safe_name)
        return safe_name.lower().strip('_')
    
    def save_avatar(self, avatar_data: Dict[str, Any]) -> bool:
        """Save complete avatar data to disk"""
        try:
            avatar_name = avatar_data.get('name', 'unnamed_avatar')
            avatar_dir = self.get_avatar_directory(avatar_name)
            
            # Create avatar directory structure
            avatar_dir.mkdir(exist_ok=True)
            (avatar_dir / "images").mkdir(exist_ok=True)
            (avatar_dir / "nodes").mkdir(exist_ok=True)
            (avatar_dir / "assets").mkdir(exist_ok=True)
            
            # Process and save images
            processed_data = self._process_avatar_images(avatar_data, avatar_dir)
            
            # Add metadata
            processed_data['metadata'] = {
                'created': datetime.now().isoformat(),
                'last_modified': datetime.now().isoformat(),
                'version': '1.0',
                'avatar_id': str(uuid.uuid4())
            }
            
            # Save main avatar.json
            avatar_json_path = avatar_dir / "avatar.json"
            with open(avatar_json_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
            # Save node network data for node manager compatibility
            self._save_node_network_data(processed_data, avatar_dir)
            
            print(f"[AVATAR MANAGER] Saved avatar '{avatar_name}' to {avatar_dir}")
            return True
            
        except Exception as e:
            print(f"[AVATAR MANAGER] Error saving avatar: {e}")
            return False
    
    def _process_avatar_images(self, avatar_data: Dict[str, Any], avatar_dir: Path) -> Dict[str, Any]:
        """Process and save all images, updating paths in data"""
        processed_data = avatar_data.copy()
        
        # Process portrait image
        if 'portrait_image' in processed_data and processed_data['portrait_image']:
            portrait_path = self._save_image_data(
                processed_data['portrait_image'], 
                avatar_dir / "images" / "portrait.png"
            )
            if portrait_path:
                processed_data['portrait_image_path'] = str(portrait_path.relative_to(avatar_dir))
            # Remove base64 data to keep JSON clean
            processed_data.pop('portrait_image', None)
        
        # Process node images
        if 'nodes' in processed_data:
            for i, node in enumerate(processed_data['nodes']):
                if hasattr(node, '__dict__'):
                    node_dict = node.__dict__
                else:
                    node_dict = node
                
                if 'image_data' in node_dict and node_dict['image_data']:
                    image_path = self._save_image_data(
                        node_dict['image_data'],
                        avatar_dir / "nodes" / f"node_{i}_{node_dict.get('name', 'unnamed')}.png"
                    )
                    if image_path:
                        node_dict['image_path'] = str(image_path.relative_to(avatar_dir))
                    # Remove base64 data
                    node_dict.pop('image_data', None)
                
                # Ensure node has required fields
                if 'id' not in node_dict:
                    node_dict['id'] = f"node_{i}"
                if 'x' not in node_dict:
                    node_dict['x'] = 100 + (i * 150)
                if 'y' not in node_dict:
                    node_dict['y'] = 100 + (i % 3) * 150
                if 'connections' not in node_dict:
                    node_dict['connections'] = []
        
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
    
    def _save_node_network_data(self, avatar_data: Dict[str, Any], avatar_dir: Path):
        """Save node network data in format compatible with node manager"""
        try:
            nodes_dict = {}
            connections = []
            
            if 'nodes' in avatar_data:
                for node_data in avatar_data['nodes']:
                    if hasattr(node_data, '__dict__'):
                        node_dict = node_data.__dict__.copy()
                    else:
                        node_dict = node_data.copy()
                    
                    node_id = node_dict['id']
                    
                    # Convert relative path to absolute for node manager
                    if 'image_path' in node_dict and node_dict['image_path']:
                        absolute_path = avatar_dir / node_dict['image_path']
                        node_dict['image_path'] = str(absolute_path)
                    
                    nodes_dict[node_id] = node_dict
            
            # Create basic connections if nodes exist (you can enhance this logic)
            node_ids = list(nodes_dict.keys())
            for i in range(len(node_ids) - 1):
                connections.append((node_ids[i], node_ids[i + 1]))
                # Update node connection lists
                if node_ids[i] in nodes_dict:
                    if 'connections' not in nodes_dict[node_ids[i]]:
                        nodes_dict[node_ids[i]]['connections'] = []
                    if node_ids[i + 1] not in nodes_dict[node_ids[i]]['connections']:
                        nodes_dict[node_ids[i]]['connections'].append(node_ids[i + 1])
                
                if node_ids[i + 1] in nodes_dict:
                    if 'connections' not in nodes_dict[node_ids[i + 1]]:
                        nodes_dict[node_ids[i + 1]]['connections'] = []
                    if node_ids[i] not in nodes_dict[node_ids[i + 1]]['connections']:
                        nodes_dict[node_ids[i + 1]]['connections'].append(node_ids[i])
            
            node_network_data = {
                'nodes': nodes_dict,
                'connections': connections
            }
            
            # Save to node_network.json for node manager compatibility
            node_network_path = avatar_dir / "node_network.json"
            with open(node_network_path, 'w', encoding='utf-8') as f:
                json.dump(node_network_data, f, indent=2)
            
            print(f"[AVATAR MANAGER] Saved node network data with {len(nodes_dict)} nodes")
            
        except Exception as e:
            print(f"[AVATAR MANAGER] Error saving node network data: {e}")
    
    def load_avatar(self, avatar_name: str) -> Optional[Dict[str, Any]]:
        """Load complete avatar data from disk"""
        try:
            avatar_dir = self.get_avatar_directory(avatar_name)
            avatar_json_path = avatar_dir / "avatar.json"
            
            if not avatar_json_path.exists():
                print(f"[AVATAR MANAGER] Avatar '{avatar_name}' not found")
                return None
            
            with open(avatar_json_path, 'r', encoding='utf-8') as f:
                avatar_data = json.load(f)
            
            # Update last accessed time
            if 'metadata' not in avatar_data:
                avatar_data['metadata'] = {}
            avatar_data['metadata']['last_accessed'] = datetime.now().isoformat()
            
            # Convert relative paths to absolute for use in app
            avatar_data = self._resolve_avatar_paths(avatar_data, avatar_dir)
            
            print(f"[AVATAR MANAGER] Loaded avatar '{avatar_name}'")
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
        
        # Resolve node image paths
        if 'nodes' in avatar_data:
            for node in avatar_data['nodes']:
                if 'image_path' in node and node['image_path']:
                    if not os.path.isabs(node['image_path']):
                        full_path = avatar_dir / node['image_path']
                        if full_path.exists():
                            node['image_path'] = str(full_path)
        
        return avatar_data
    
    def list_avatars(self) -> List[Dict[str, Any]]:
        """List all available avatars with metadata"""
        avatars = []
        
        try:
            for avatar_dir in self.avatars_dir.iterdir():
                if avatar_dir.is_dir():
                    avatar_json_path = avatar_dir / "avatar.json"
                    if avatar_json_path.exists():
                        try:
                            with open(avatar_json_path, 'r', encoding='utf-8') as f:
                                avatar_data = json.load(f)
                            
                            avatars.append({
                                'name': avatar_data.get('name', avatar_dir.name),
                                'directory': avatar_dir.name,
                                'path': str(avatar_dir),
                                'metadata': avatar_data.get('metadata', {}),
                                'has_portrait': 'portrait_image_path' in avatar_data,
                                'node_count': len(avatar_data.get('nodes', [])),
                                'has_personality': bool(avatar_data.get('personality', '').strip())
                            })
                        except Exception as e:
                            print(f"[AVATAR MANAGER] Error reading avatar in {avatar_dir}: {e}")
            
            # Sort by last modified date
            avatars.sort(key=lambda x: x.get('metadata', {}).get('last_modified', ''), reverse=True)
            
        except Exception as e:
            print(f"[AVATAR MANAGER] Error listing avatars: {e}")
        
        return avatars
    
    def delete_avatar(self, avatar_name: str) -> bool:
        """Delete an avatar and all its data"""
        try:
            avatar_dir = self.get_avatar_directory(avatar_name)
            if avatar_dir.exists():
                shutil.rmtree(avatar_dir)
                print(f"[AVATAR MANAGER] Deleted avatar '{avatar_name}'")
                return True
            return False
        except Exception as e:
            print(f"[AVATAR MANAGER] Error deleting avatar '{avatar_name}': {e}")
            return False
    
    def duplicate_avatar(self, source_name: str, new_name: str) -> bool:
        """Create a copy of an existing avatar"""
        try:
            source_dir = self.get_avatar_directory(source_name)
            target_dir = self.get_avatar_directory(new_name)
            
            if not source_dir.exists():
                print(f"[AVATAR MANAGER] Source avatar '{source_name}' not found")
                return False
            
            if target_dir.exists():
                print(f"[AVATAR MANAGER] Target avatar '{new_name}' already exists")
                return False
            
            # Copy directory
            shutil.copytree(source_dir, target_dir)
            
            # Update avatar.json with new name and metadata
            avatar_json_path = target_dir / "avatar.json"
            if avatar_json_path.exists():
                with open(avatar_json_path, 'r', encoding='utf-8') as f:
                    avatar_data = json.load(f)
                
                avatar_data['name'] = new_name
                avatar_data['metadata'] = {
                    'created': datetime.now().isoformat(),
                    'last_modified': datetime.now().isoformat(),
                    'version': '1.0',
                    'avatar_id': str(uuid.uuid4()),
                    'duplicated_from': source_name
                }
                
                with open(avatar_json_path, 'w', encoding='utf-8') as f:
                    json.dump(avatar_data, f, indent=2, ensure_ascii=False)
            
            print(f"[AVATAR MANAGER] Duplicated avatar '{source_name}' to '{new_name}'")
            return True
            
        except Exception as e:
            print(f"[AVATAR MANAGER] Error duplicating avatar: {e}")
            return False
    
    def export_avatar(self, avatar_name: str, export_path: str) -> bool:
        """Export avatar to a zip file"""
        try:
            import zipfile
            
            avatar_dir = self.get_avatar_directory(avatar_name)
            if not avatar_dir.exists():
                return False
            
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in avatar_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(avatar_dir)
                        zipf.write(file_path, arcname)
            
            print(f"[AVATAR MANAGER] Exported avatar '{avatar_name}' to {export_path}")
            return True
            
        except Exception as e:
            print(f"[AVATAR MANAGER] Error exporting avatar: {e}")
            return False
    
    def import_avatar(self, import_path: str, avatar_name: str = None) -> bool:
        """Import avatar from a zip file"""
        try:
            import zipfile
            
            with zipfile.ZipFile(import_path, 'r') as zipf:
                # Try to find avatar.json to get the name
                temp_dir = Path(import_path).parent / "temp_import"
                zipf.extractall(temp_dir)
                
                avatar_json_path = temp_dir / "avatar.json"
                if avatar_json_path.exists():
                    with open(avatar_json_path, 'r', encoding='utf-8') as f:
                        avatar_data = json.load(f)
                    
                    imported_name = avatar_name or avatar_data.get('name', 'imported_avatar')
                    target_dir = self.get_avatar_directory(imported_name)
                    
                    # Move from temp to final location
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    shutil.move(temp_dir, target_dir)
                    
                    # Update metadata
                    avatar_data['name'] = imported_name
                    avatar_data['metadata']['imported'] = datetime.now().isoformat()
                    
                    with open(target_dir / "avatar.json", 'w', encoding='utf-8') as f:
                        json.dump(avatar_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"[AVATAR MANAGER] Imported avatar as '{imported_name}'")
                    return True
                
                # Clean up temp directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    
        except Exception as e:
            print(f"[AVATAR MANAGER] Error importing avatar: {e}")
            
        return False