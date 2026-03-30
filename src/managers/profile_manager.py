import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime


class ProfileManager:
    """Gerenciador de perfis de encoding."""
    
    DEFAULT_PROFILES: Dict[str, Dict[str, Any]] = {
        "filmes_4k_hevc": {
            "name": "Filmes 4K HEVC",
            "description": "Alta qualidade para filmes 4K - CQ 18, resolução original, HDR preservado",
            "codec": "hevc_nvenc",
            "cq": "18",
            "preset": "p5",
            "resolution": None,
            "hdr_to_sdr": False,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "filmes_4k_h264": {
            "name": "Filmes 4K H264",
            "description": "Compatibilidade máxima para filmes 4K - CQ 20, HDR convertido para SDR",
            "codec": "h264_nvenc",
            "cq": "20",
            "preset": "p5",
            "resolution": None,
            "hdr_to_sdr": True,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "filmes_1080p_hevc": {
            "name": "Filmes 1080p HEVC",
            "description": "Qualidade balanceada para filmes 1080p - CQ 20, HDR preservado",
            "codec": "hevc_nvenc",
            "cq": "20",
            "preset": "p5",
            "resolution": "1080",
            "hdr_to_sdr": False,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "filmes_1080p_h264": {
            "name": "Filmes 1080p H264",
            "description": "Compatibilidade para filmes 1080p - CQ 21, HDR convertido para SDR",
            "codec": "h264_nvenc",
            "cq": "21",
            "preset": "p5",
            "resolution": "1080",
            "hdr_to_sdr": True,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "filmes_720p_hevc": {
            "name": "Filmes 720p HEVC",
            "description": "Arquivos menores para filmes 720p - CQ 22, HDR convertido para SDR",
            "codec": "hevc_nvenc",
            "cq": "22",
            "preset": "p4",
            "resolution": "720",
            "hdr_to_sdr": True,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "filmes_720p_h264": {
            "name": "Filmes 720p H264",
            "description": "Compatibilidade máxima para TVs antigas - CQ 23, HDR convertido para SDR",
            "codec": "h264_nvenc",
            "cq": "23",
            "preset": "p5",
            "resolution": "720",
            "hdr_to_sdr": True,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "series_4k_hevc": {
            "name": "Series 4K HEVC",
            "description": "Qualidade para séries 4K - CQ 22, resolução original, HDR preservado",
            "codec": "hevc_nvenc",
            "cq": "22",
            "preset": "p5",
            "resolution": None,
            "hdr_to_sdr": False,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "series_4k_h264": {
            "name": "Series 4K H264",
            "description": "Compatibilidade para séries 4K - CQ 24, HDR convertido para SDR",
            "codec": "h264_nvenc",
            "cq": "24",
            "preset": "p5",
            "resolution": None,
            "hdr_to_sdr": True,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "series_1080p_hevc": {
            "name": "Series 1080p HEVC",
            "description": "Balanceado para séries 1080p - CQ 24, HDR preservado",
            "codec": "hevc_nvenc",
            "cq": "24",
            "preset": "p5",
            "resolution": "1080",
            "hdr_to_sdr": False,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "series_1080p_h264": {
            "name": "Series 1080p H264",
            "description": "Compatibilidade para séries 1080p - CQ 25, HDR convertido para SDR",
            "codec": "h264_nvenc",
            "cq": "25",
            "preset": "p5",
            "resolution": "1080",
            "hdr_to_sdr": True,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "series_720p_hevc": {
            "name": "Series 720p HEVC",
            "description": "Arquivos leves para séries 720p - CQ 26, HDR convertido para SDR",
            "codec": "hevc_nvenc",
            "cq": "26",
            "preset": "p4",
            "resolution": "720",
            "hdr_to_sdr": True,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "series_720p_h264": {
            "name": "Series 720p H264",
            "description": "Máxima compressão para séries 720p - CQ 27, HDR convertido para SDR",
            "codec": "h264_nvenc",
            "cq": "27",
            "preset": "p5",
            "resolution": "720",
            "hdr_to_sdr": True,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "animacao_1080p_hevc": {
            "name": "Animação 1080p HEVC",
            "description": "Otimizado para animação/desenhos - CQ 18, menos detalhes, áreas lisas",
            "codec": "hevc_nvenc",
            "cq": "18",
            "preset": "p4",
            "resolution": "1080",
            "hdr_to_sdr": False,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "animacao_720p_h264": {
            "name": "Animação 720p H264",
            "description": "Compatibilidade para animação 720p - CQ 20, HDR convertido para SDR",
            "codec": "h264_nvenc",
            "cq": "20",
            "preset": "p5",
            "resolution": "720",
            "hdr_to_sdr": True,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "documentario_1080p_hevc": {
            "name": "Documentário 1080p HEVC",
            "description": "Otimizado para documentários - CQ 24, conteúdo estático",
            "codec": "hevc_nvenc",
            "cq": "24",
            "preset": "p5",
            "resolution": "1080",
            "hdr_to_sdr": False,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
            "created_at": "2024-01-01T00:00:00"
        },
        "documentario_720p_h264": {
            "name": "Documentário 720p H264",
            "description": "Compatibilidade para documentários 720p - CQ 26, conteúdo estático",
            "codec": "h264_nvenc",
            "cq": "26",
            "preset": "p5",
            "resolution": "720",
            "hdr_to_sdr": True,
            "deinterlace": False,
            "plex_compatible": True,
            "two_pass": False,
            "audio_tracks": None,
            "subtitle_burn": False,
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
            if not pid.startswith('_') and isinstance(data, dict) and 'name' in data
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
