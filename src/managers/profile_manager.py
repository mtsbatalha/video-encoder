import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime


class ProfileManager:
    """Gerenciador de perfis de encoding."""
    
    DEFAULT_PROFILES: Dict[str, Dict[str, Any]] = {
        "filmes_4k_hevc": {
            "name": "Filmes 4K HEVC",
            "description": "Alta qualidade para filmes 4K",
            "codec": "hevc_nvenc",
            "cq": "18",
            "preset": "p5",
            "resolution": None,
            "hdr_to_sdr": False,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "series_1080p_hevc": {
            "name": "Series 1080p HEVC",
            "description": "Qualidade balanceada para series",
            "codec": "hevc_nvenc",
            "cq": "24",
            "preset": "p5",
            "resolution": "1080",
            "hdr_to_sdr": False,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "tv_720p_h264": {
            "name": "TV Antiga 720p H264",
            "description": "Compatibilidade com TVs antigas",
            "codec": "h264_nvenc",
            "cq": "23",
            "preset": "p5",
            "resolution": "720",
            "hdr_to_sdr": False,
            "deinterlace": True,
            "plex_compatible": True,
            "two_pass": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "animacao_1080p_hevc": {
            "name": "Animação 1080p HEVC",
            "description": "Otimizado para desenhos animados",
            "codec": "hevc_nvenc",
            "cq": "20",
            "preset": "p4",
            "resolution": "1080",
            "hdr_to_sdr": False,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "av1_4k_quality": {
            "name": "AV1 4K Quality",
            "description": "Codec AV1 para máxima eficiência",
            "codec": "av1_nvenc",
            "cq": "22",
            "preset": "p4",
            "resolution": None,
            "hdr_to_sdr": False,
            "deinterlace": False,
            "plex_compatible": False,
            "two_pass": False,
            "created_at": "2024-01-01T00:00:00"
        }
    }
    
    def __init__(self, profiles_dir: Optional[str] = None):
        self.profiles_dir = Path(profiles_dir) if profiles_dir else Path(__file__).parent.parent.parent / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self._profiles_file = self.profiles_dir / "profiles.json"
        self._profiles: Dict[str, Dict[str, Any]] = {}
        self.load()
    
    def load(self) -> Dict[str, Dict[str, Any]]:
        """Carrega perfis do arquivo."""
        if self._profiles_file.exists():
            try:
                with open(self._profiles_file, 'r', encoding='utf-8') as f:
                    self._profiles = json.load(f)
            except Exception:
                self._profiles = self.DEFAULT_PROFILES.copy()
        else:
            self._profiles = self.DEFAULT_PROFILES.copy()
            self.save()
        
        return self._profiles.copy()
    
    def save(self) -> bool:
        """Salva perfis no arquivo."""
        try:
            with open(self._profiles_file, 'w', encoding='utf-8') as f:
                json.dump(self._profiles, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Obtém perfil por ID."""
        return self._profiles.get(profile_id)
    
    def get_profile_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Obtém perfil por nome (case-insensitive)."""
        for profile_id, profile in self._profiles.items():
            if profile.get('name', '').lower() == name.lower():
                return profile
        return None
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """Retorna lista de todos os perfis."""
        return [
            {"id": pid, **data}
            for pid, data in self._profiles.items()
        ]
    
    def create_profile(
        self,
        name: str,
        codec: str = 'hevc_nvenc',
        cq: Optional[str] = None,
        bitrate: Optional[str] = None,
        preset: str = 'p5',
        resolution: Optional[str] = None,
        two_pass: bool = False,
        hdr_to_sdr: bool = False,
        deinterlace: bool = False,
        plex_compatible: bool = True,
        description: str = ''
    ) -> str:
        """Cria novo perfil."""
        profile_id = f"{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self._profiles[profile_id] = {
            "name": name,
            "description": description,
            "codec": codec,
            "cq": cq,
            "bitrate": bitrate,
            "preset": preset,
            "resolution": resolution,
            "two_pass": two_pass,
            "hdr_to_sdr": hdr_to_sdr,
            "deinterlace": deinterlace,
            "plex_compatible": plex_compatible,
            "created_at": datetime.now().isoformat()
        }
        
        self.save()
        return profile_id
    
    def update_profile(self, profile_id: str, **kwargs) -> bool:
        """Atualiza perfil existente."""
        if profile_id not in self._profiles:
            return False
        
        self._profiles[profile_id].update(kwargs)
        return self.save()
    
    def delete_profile(self, profile_id: str) -> bool:
        """Exclui perfil."""
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            return self.save()
        return False
    
    def export_profile(self, profile_id: str, output_path: str) -> bool:
        """Exporta perfil para arquivo JSON."""
        if profile_id not in self._profiles:
            return False
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({profile_id: self._profiles[profile_id]}, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def import_profile(self, input_path: str) -> bool:
        """Importa perfil de arquivo JSON."""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                imported = json.load(f)
            
            for profile_id, profile_data in imported.items():
                self._profiles[profile_id] = profile_data
            
            return self.save()
        except Exception:
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reseta perfis para padrões."""
        self._profiles = self.DEFAULT_PROFILES.copy()
        return self.save()
