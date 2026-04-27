"""
Client management module for Kharōn webapp.

Handles client registry operations, client data management, and badge generation.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from copy import deepcopy

import config


@dataclass
class Client:
    """Client data model."""
    id: str
    name: str
    short_name: str
    description: str
    color: str
    icon: str
    contact_email: str
    contact_name: str
    active: bool = True


class ClientManager:
    """Client management class with registry operations."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize ClientManager.
        
        Args:
            config_path: Path to clients registry YAML file. If None, uses config.CLIENTS_REGISTRY_PATH
        """
        self.config_path = config_path or config.CLIENTS_REGISTRY_PATH
        self._clients: Dict[str, Client] = {}
        self._cache_valid = False
        
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_yaml(self) -> Dict:
        """Load clients from YAML file.
        
        Returns:
            Dict containing clients data
            
        Raises:
            FileNotFoundError: If registry file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in registry file: {e}") from e
    
    def _save_yaml(self, data: Dict) -> None:
        """Save clients to YAML file.
        
        Args:
            data: Dict containing clients data to save
            
        Raises:
            IOError: If file write fails
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        except IOError as e:
            raise IOError(f"Failed to save registry file: {e}") from e
    
    def load_clients(self) -> Dict[str, Client]:
        """Load all clients from registry.
        
        Returns:
            Dict of Client objects keyed by client ID
            
        Raises:
            ValueError: If YAML parsing fails
            IOError: If file operations fail
        """
        try:
            data = self._load_yaml()
            self._clients = {}
            
            clients_list = data.get('clients', []) if isinstance(data, dict) else []
            self._clients = {}
            
            for client_data in clients_list:
                if not isinstance(client_data, dict):
                    continue
                client_id = client_data.get('id', '')
                if not client_id:
                    continue
                client_obj = Client(
                    id=client_id,
                    name=client_data.get('name', ''),
                    short_name=client_data.get('short_name', ''),
                    description=client_data.get('description', ''),
                    color=client_data.get('color', '#374151'),
                    icon=client_data.get('icon', '🏢'),
                    contact_email=client_data.get('contact_email', ''),
                    contact_name=client_data.get('contact_name', ''),
                    active=client_data.get('active', True)
                )
                self._clients[client_id] = client_obj
            
            self._cache_valid = True
            return deepcopy(self._clients)
            
        except (ValueError, IOError) as e:
            raise
    
    def get_client(self, client_id: str) -> Optional[Client]:
        """Get a specific client by ID.
        
        Args:
            client_id: The client identifier
            
        Returns:
            Client object or None if not found
        """
        if not self._cache_valid:
            self.load_clients()
        
        return deepcopy(self._clients.get(client_id))
    
    def get_active_clients(self) -> List[Client]:
        """Get all active clients.
        
        Returns:
            List of active Client objects
        """
        if not self._cache_valid:
            self.load_clients()
        
        return [client for client in self._clients.values() if client.active]
    
    def generate_badge(self, client_id: str) -> str:
        """Generate HTML badge for a client.
        
        Args:
            client_id: The client identifier
            
        Returns:
            HTML badge string
            
        Raises:
            ValueError: If client not found
        """
        client = self.get_client(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")
        
        return self.generate_badge_html(client)
    
    def generate_badge_html(self, client: Client) -> str:
        """Generate styled HTML badge for a client.
        
        Args:
            client: Client object
            
        Returns:
            HTML badge string
        """
        return (
            f'<span style="'
            f"background-color: {client.color}; "
            f"color: white; "
            f"padding: 2px 8px; "
            f"border-radius: 12px; "
            f"font-size: 12px; "
            f'font-weight: bold;">'
            f"{client.icon} {client.short_name}"
            f"</span>"
        )
    
    def get_client_scripts(self, client_id: str, scripts_registry: Path) -> List[Dict]:
        """Get scripts associated with a client.
        
        Args:
            client_id: The client identifier
            scripts_registry: Path to scripts registry YAML file
            
        Returns:
            List of script dictionaries associated with the client
            
        Raises:
            ValueError: If client not found
            IOError: If registry file operations fail
            yaml.YAMLError: If YAML parsing fails
        """
        client = self.get_client(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")
        
        try:
            # Load scripts registry
            with open(scripts_registry, 'r', encoding='utf-8') as f:
                scripts_data = yaml.safe_load(f) or {}
            
            # Get scripts for this client
            client_scripts = scripts_data.get(client_id, [])
            return deepcopy(client_scripts)
            
        except (IOError, yaml.YAMLError) as e:
            raise ValueError(f"Failed to load scripts registry: {e}") from e
    
    def create_client(self, client_data: Dict) -> Client:
        """Create a new client and add to registry.
        
        Args:
            client_data: Dict containing client data
            
        Returns:
            Created Client object
            
        Raises:
            ValueError: If client data is invalid or client ID already exists
            IOError: If file operations fail
        """
        # Validate required fields
        required_fields = ['id', 'name', 'short_name', 'description', 'color', 'icon', 'contact_email', 'contact_name']
        for field in required_fields:
            if field not in client_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Check if client ID already exists
        self.load_clients()  # Ensure cache is loaded
        if client_data['id'] in self._clients:
            raise ValueError(f"Client {client_data['id']} already exists")
        
        # Create client object
        client = Client(**client_data)
        
        try:
            registry_data = self._load_yaml()
            registry_data[client.id] = asdict(client)
            self._save_yaml(registry_data)
            
            self._clients[client.id] = client
            self._cache_valid = True
            
            return deepcopy(client)
            
        except (ValueError, IOError) as e:
            raise
    
    def update_client(self, client_id: str, client_data: Dict) -> Client:
        """Update an existing client.
        
        Args:
            client_id: The client identifier
            client_data: Dict containing updated client data
            
        Returns:
            Updated Client object
            
        Raises:
            ValueError: If client not found or data invalid
            IOError: If file operations fail
        """
        # Load existing clients
        self.load_clients()
        
        if client_id not in self._clients:
            raise ValueError(f"Client {client_id} not found")
        
        for field, value in client_data.items():
            if hasattr(existing_client, field):
                setattr(existing_client, field, value)
        
        try:
            registry_data = self._load_yaml()
            registry_data[client_id] = asdict(existing_client)
            self._save_yaml(registry_data)
            
            self._clients[client_id] = existing_client
            
            return deepcopy(existing_client)
            
        except (ValueError, IOError) as e:
            raise
    
    def delete_client(self, client_id: str) -> bool:
        """Delete a client from registry.
        
        Args:
            client_id: The client identifier
            
        Returns:
            True if client was deleted, False if not found
            
        Raises:
            IOError: If file operations fail
        """
        # Load existing clients
        self.load_clients()
        
        if client_id not in self._clients:
            return False
        
        try:
            registry_data = self._load_yaml()
            if client_id in registry_data:
                del registry_data[client_id]
                self._save_yaml(registry_data)
                
                del self._clients[client_id]
                self._cache_valid = True
                
                return True
            
        except (ValueError, IOError) as e:
            raise IOError(f"Failed to delete client {client_id}: {e}") from e
        
        return False
    
    def reload_cache(self) -> None:
        """Force reload of client registry from file."""
        self._cache_valid = False
        self.load_clients()
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status information.
        
        Returns:
            Dict with cache status information
        """
        return {
            "cache_valid": self._cache_valid,
            "loaded_clients": len(self._clients),
            "config_path": str(self.config_path),
            "config_exists": self.config_path.exists()
        }