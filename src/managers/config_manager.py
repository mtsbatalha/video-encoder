import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, List


class ConfigManager:
    """Gerenciador de configuração centralizada."""
    
    DEFAULT_CONFIG = {
        "app_name": "Fabrica de Conversão NVENC Pro v2.0",
        "version": "2.0.0",
        "ffmpeg": {
            "path": None,
            "ffprobe_path": None,
            "timeout_seconds": 3600,
            "hw_monitoring": True,
            "hw_monitoring_interval": 1
        },
        "directories": {
            "watch_folders": [],
            "profiles": "profiles",
            "jobs": "jobs",
            "logs": "logs",
            "stats": "stats"
        },
        "encoding": {
            "max_concurrent": 2,
            "priority": "normal",
            "auto_cleanup": True,
            "disk_space_min_gb": 10,
            "retry_attempts": 2,
            "retry_delay_seconds": 30
        },
        "monitoring": {
            "gpu_enabled": True,
            "cpu_enabled": True,
            "disk_enabled": True,
            "temperature_warning": 85,
            "gpu_memory_warning_percent": 90
        },
        "notifications": {
            "enabled": False,
            "email": {
                "smtp_server": None,
                "smtp_port": None,
                "from_email": None,
                "to_email": None,
                "password": None
            },
            "webhook": {
                "url": None,
                "method": "POST"
            }
        },
        "ui": {
            "theme": "default",
            "show_progress_bar": True,
            "show_resource_monitor": True,
            "language": "pt-BR"
        },
        "logging": {
            "level": "INFO",
            "file_rotation_mb": 10,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "recurrent_folders": []
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path(__file__).parent.parent.parent / "config.json"
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> Dict[str, Any]:
        """Carrega configuração do arquivo."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception:
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            self._config = self.DEFAULT_CONFIG.copy()
        
        return self._config
    
    def save(self) -> bool:
        """Salva configuração no arquivo."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtém valor da configuração usando notação dot."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """Define valor da configuração usando notação dot."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        return True
    
    def get_all(self) -> Dict[str, Any]:
        """Retorna configuração completa."""
        return self._config.copy()
    
    def get_watch_folders(self) -> List[Dict[str, Any]]:
        """Retorna lista de pastas watch configuradas."""
        return self.get('directories.watch_folders', [])
    
    def add_watch_folder(self, folder: Dict[str, Any]) -> bool:
        """Adiciona pasta watch."""
        folders = self.get_watch_folders()
        folders.append(folder)
        self.set('directories.watch_folders', folders)
        return self.save()
    
    def remove_watch_folder(self, index: int) -> bool:
        """Remove pasta watch por índice."""
        folders = self.get_watch_folders()
        if 0 <= index < len(folders):
            folders.pop(index)
            self.set('directories.watch_folders', folders)
            return self.save()
        return False
    
    def reset_to_defaults(self) -> bool:
        """Reseta configuração para padrões."""
        self._config = self.DEFAULT_CONFIG.copy()
        return self.save()
    
    def _generate_uuid(self) -> str:
        """Gera um UUID v4 para identificação única."""
        return str(uuid.uuid4())
    
    def get_recurrent_folders(self) -> List[Dict[str, Any]]:
        """Retorna lista de pastas recorrentes configuradas."""
        return self.get('recurrent_folders', [])
    
    def add_recurrent_folder(self, folder: Dict[str, Any]) -> bool:
        """Adiciona pasta recorrente."""
        # Gera ID único se não fornecido
        if 'id' not in folder:
            folder['id'] = self._generate_uuid()
        
        # Define valores padrão se não fornecidos
        if 'created_at' not in folder:
            folder['created_at'] = datetime.now().isoformat() + 'Z'
        if 'last_run' not in folder:
            folder['last_run'] = None
        if 'total_processed' not in folder:
            folder['total_processed'] = 0
        if 'enabled' not in folder:
            folder['enabled'] = True
        
        folders = self.get_recurrent_folders()
        folders.append(folder)
        self.set('recurrent_folders', folders)
        return self.save()
    
    def remove_recurrent_folder(self, index: int) -> bool:
        """Remove pasta recorrente por índice."""
        folders = self.get_recurrent_folders()
        if 0 <= index < len(folders):
            folders.pop(index)
            self.set('recurrent_folders', folders)
            return self.save()
        return False
    
    def update_recurrent_folder(self, folder_id: str, updates: Dict[str, Any]) -> bool:
        """Atualiza pasta recorrente pelo ID."""
        folders = self.get_recurrent_folders()
        for i, folder in enumerate(folders):
            if folder.get('id') == folder_id:
                # Atualiza apenas os campos fornecidos, mantendo os outros intactos
                updated_folder = {**folder, **updates}
                folders[i] = updated_folder
                self.set('recurrent_folders', folders)
                return self.save()
        return False
