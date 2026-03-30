import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
from ..core.hw_detector import HardwareDetector, HardwareCapabilities


class ProfileManager:
    """Gerenciador de perfis de encoding."""
    
    DEFAULT_PROFILES: Dict[str, Dict[str, Any]] = {
        # === NVIDIA GPU (NVENC) ===
        "nvidia_filmes_4k_hevc": {
            "name": "NVIDIA Filmes 4K HEVC",
            "description": "Alta qualidade para filmes 4K - CQ 18, resolução original, HDR preservado",
            "codec": "hevc_nvenc", "cq": "18", "preset": "p5", "resolution": None,
            "hdr_to_sdr": False, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "nvidia_gpu"
        },
        "nvidia_filmes_4k_h264": {
            "name": "NVIDIA Filmes 4K H264",
            "description": "Compatibilidade máxima para filmes 4K - CQ 20, HDR convertido para SDR",
            "codec": "h264_nvenc", "cq": "20", "preset": "p5", "resolution": None,
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "nvidia_gpu"
        },
        "nvidia_filmes_1080p_hevc": {
            "name": "NVIDIA Filmes 1080p HEVC",
            "description": "Qualidade balanceada para filmes 1080p - CQ 20, HDR preservado",
            "codec": "hevc_nvenc", "cq": "20", "preset": "p5", "resolution": "1080",
            "hdr_to_sdr": False, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "nvidia_gpu"
        },
        "nvidia_filmes_1080p_h264": {
            "name": "NVIDIA Filmes 1080p H264",
            "description": "Compatibilidade para filmes 1080p - CQ 21, HDR convertido para SDR",
            "codec": "h264_nvenc", "cq": "21", "preset": "p5", "resolution": "1080",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "nvidia_gpu"
        },
        "nvidia_filmes_720p_hevc": {
            "name": "NVIDIA Filmes 720p HEVC",
            "description": "Arquivos menores para filmes 720p - CQ 22, HDR convertido para SDR",
            "codec": "hevc_nvenc", "cq": "22", "preset": "p4", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "nvidia_gpu"
        },
        "nvidia_filmes_720p_h264": {
            "name": "NVIDIA Filmes 720p H264",
            "description": "Compatibilidade máxima para TVs antigas - CQ 23, HDR convertido para SDR",
            "codec": "h264_nvenc", "cq": "23", "preset": "p5", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "nvidia_gpu"
        },
        "nvidia_series_4k_hevc": {
            "name": "NVIDIA Series 4K HEVC",
            "description": "Qualidade para séries 4K - CQ 22, resolução original, HDR preservado",
            "codec": "hevc_nvenc", "cq": "22", "preset": "p5", "resolution": None,
            "hdr_to_sdr": False, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "nvidia_gpu"
        },
        "nvidia_series_4k_h264": {
            "name": "NVIDIA Series 4K H264",
            "description": "Compatibilidade para séries 4K - CQ 24, HDR convertido para SDR",
            "codec": "h264_nvenc", "cq": "24", "preset": "p5", "resolution": None,
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "nvidia_gpu"
        },
        "nvidia_series_1080p_hevc": {
            "name": "NVIDIA Series 1080p HEVC",
            "description": "Balanceado para séries 1080p - CQ 24, HDR preservado",
            "codec": "hevc_nvenc", "cq": "24", "preset": "p5", "resolution": "1080",
            "hdr_to_sdr": False, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "nvidia_gpu"
        },
        "nvidia_series_1080p_h264": {
            "name": "NVIDIA Series 1080p H264",
            "description": "Compatibilidade para séries 1080p - CQ 25, HDR convertido para SDR",
            "codec": "h264_nvenc", "cq": "25", "preset": "p5", "resolution": "1080",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "nvidia_gpu"
        },
        "nvidia_series_720p_hevc": {
            "name": "NVIDIA Series 720p HEVC",
            "description": "Arquivos leves para séries 720p - CQ 26, HDR convertido para SDR",
            "codec": "hevc_nvenc", "cq": "26", "preset": "p4", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "nvidia_gpu"
        },
        "nvidia_series_720p_h264": {
            "name": "NVIDIA Series 720p H264",
            "description": "Máxima compressão para séries 720p - CQ 27, HDR convertido para SDR",
            "codec": "h264_nvenc", "cq": "27", "preset": "p5", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "nvidia_gpu"
        },
        # === AMD GPU (AMF) ===
        "amd_gpu_filmes_1080p_hevc": {
            "name": "AMD GPU Filmes 1080p HEVC",
            "description": "Qualidade para filmes 1080p - AMD AMF, CQ 20, HDR preservado",
            "codec": "hevc_amf", "cq": "20", "preset": "quality", "resolution": "1080",
            "hdr_to_sdr": False, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_gpu"
        },
        "amd_gpu_filmes_1080p_h264": {
            "name": "AMD GPU Filmes 1080p H264",
            "description": "Compatibilidade para filmes 1080p - AMD AMF, CQ 21",
            "codec": "h264_amf", "cq": "21", "preset": "quality", "resolution": "1080",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_gpu"
        },
        "amd_gpu_filmes_720p_hevc": {
            "name": "AMD GPU Filmes 720p HEVC",
            "description": "Arquivos menores 720p - AMD AMF, CQ 22",
            "codec": "hevc_amf", "cq": "22", "preset": "balanced", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_gpu"
        },
        "amd_gpu_filmes_720p_h264": {
            "name": "AMD GPU Filmes 720p H264",
            "description": "Compatibilidade 720p - AMD AMF, CQ 23",
            "codec": "h264_amf", "cq": "23", "preset": "balanced", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_gpu"
        },
        "amd_gpu_series_1080p_hevc": {
            "name": "AMD GPU Series 1080p HEVC",
            "description": "Balanceado séries 1080p - AMD AMF, CQ 24",
            "codec": "hevc_amf", "cq": "24", "preset": "balanced", "resolution": "1080",
            "hdr_to_sdr": False, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_gpu"
        },
        "amd_gpu_series_1080p_h264": {
            "name": "AMD GPU Series 1080p H264",
            "description": "Compatibilidade séries 1080p - AMD AMF, CQ 25",
            "codec": "h264_amf", "cq": "25", "preset": "balanced", "resolution": "1080",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_gpu"
        },
        "amd_gpu_series_720p_hevc": {
            "name": "AMD GPU Series 720p HEVC",
            "description": "Arquivos leves 720p - AMD AMF, CQ 26",
            "codec": "hevc_amf", "cq": "26", "preset": "speed", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_gpu"
        },
        "amd_gpu_series_720p_h264": {
            "name": "AMD GPU Series 720p H264",
            "description": "Máxima compressão 720p - AMD AMF, CQ 27",
            "codec": "h264_amf", "cq": "27", "preset": "speed", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_gpu"
        },
        # === Intel iGPU (QSV) ===
        "intel_igpu_filmes_1080p_hevc": {
            "name": "Intel iGPU Filmes 1080p HEVC",
            "description": "Qualidade filmes 1080p - Intel QSV, CQ 20, HDR preservado",
            "codec": "hevc_qsv", "cq": "20", "preset": "balanced", "resolution": "1080",
            "hdr_to_sdr": False, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "intel_igpu"
        },
        "intel_igpu_filmes_1080p_h264": {
            "name": "Intel iGPU Filmes 1080p H264",
            "description": "Compatibilidade filmes 1080p - Intel QSV, CQ 21",
            "codec": "h264_qsv", "cq": "21", "preset": "balanced", "resolution": "1080",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "intel_igpu"
        },
        "intel_igpu_filmes_720p_hevc": {
            "name": "Intel iGPU Filmes 720p HEVC",
            "description": "Arquivos menores 720p - Intel QSV, CQ 22",
            "codec": "hevc_qsv", "cq": "22", "preset": "fast", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "intel_igpu"
        },
        "intel_igpu_filmes_720p_h264": {
            "name": "Intel iGPU Filmes 720p H264",
            "description": "Compatibilidade 720p - Intel QSV, CQ 23",
            "codec": "h264_qsv", "cq": "23", "preset": "fast", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "intel_igpu"
        },
        "intel_igpu_series_1080p_hevc": {
            "name": "Intel iGPU Series 1080p HEVC",
            "description": "Balanceado séries 1080p - Intel QSV, CQ 24",
            "codec": "hevc_qsv", "cq": "24", "preset": "balanced", "resolution": "1080",
            "hdr_to_sdr": False, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "intel_igpu"
        },
        "intel_igpu_series_1080p_h264": {
            "name": "Intel iGPU Series 1080p H264",
            "description": "Compatibilidade séries 1080p - Intel QSV, CQ 25",
            "codec": "h264_qsv", "cq": "25", "preset": "balanced", "resolution": "1080",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "intel_igpu"
        },
        "intel_igpu_series_720p_hevc": {
            "name": "Intel iGPU Series 720p HEVC",
            "description": "Arquivos leves 720p - Intel QSV, CQ 26",
            "codec": "hevc_qsv", "cq": "26", "preset": "fast", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "intel_igpu"
        },
        "intel_igpu_series_720p_h264": {
            "name": "Intel iGPU Series 720p H264",
            "description": "Máxima compressão 720p - Intel QSV, CQ 27",
            "codec": "h264_qsv", "cq": "27", "preset": "fast", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "intel_igpu"
        },
        # === AMD iGPU (APU AMF) ===
        "amd_igpu_filmes_1080p_hevc": {
            "name": "AMD iGPU Filmes 1080p HEVC",
            "description": "Qualidade filmes 1080p - AMD APU AMF, CQ 20, HDR preservado",
            "codec": "hevc_amf", "cq": "20", "preset": "quality", "resolution": "1080",
            "hdr_to_sdr": False, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_igpu"
        },
        "amd_igpu_filmes_1080p_h264": {
            "name": "AMD iGPU Filmes 1080p H264",
            "description": "Compatibilidade filmes 1080p - AMD APU AMF, CQ 21",
            "codec": "h264_amf", "cq": "21", "preset": "quality", "resolution": "1080",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_igpu"
        },
        "amd_igpu_filmes_720p_hevc": {
            "name": "AMD iGPU Filmes 720p HEVC",
            "description": "Arquivos menores 720p - AMD APU AMF, CQ 22",
            "codec": "hevc_amf", "cq": "22", "preset": "balanced", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_igpu"
        },
        "amd_igpu_filmes_720p_h264": {
            "name": "AMD iGPU Filmes 720p H264",
            "description": "Compatibilidade 720p - AMD APU AMF, CQ 23",
            "codec": "h264_amf", "cq": "23", "preset": "balanced", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_igpu"
        },
        "amd_igpu_series_1080p_hevc": {
            "name": "AMD iGPU Series 1080p HEVC",
            "description": "Balanceado séries 1080p - AMD APU AMF, CQ 24",
            "codec": "hevc_amf", "cq": "24", "preset": "balanced", "resolution": "1080",
            "hdr_to_sdr": False, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_igpu"
        },
        "amd_igpu_series_1080p_h264": {
            "name": "AMD iGPU Series 1080p H264",
            "description": "Compatibilidade séries 1080p - AMD APU AMF, CQ 25",
            "codec": "h264_amf", "cq": "25", "preset": "balanced", "resolution": "1080",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_igpu"
        },
        "amd_igpu_series_720p_hevc": {
            "name": "AMD iGPU Series 720p HEVC",
            "description": "Arquivos leves 720p - AMD APU AMF, CQ 26",
            "codec": "hevc_amf", "cq": "26", "preset": "speed", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_igpu"
        },
        "amd_igpu_series_720p_h264": {
            "name": "AMD iGPU Series 720p H264",
            "description": "Máxima compressão 720p - AMD APU AMF, CQ 27",
            "codec": "h264_amf", "cq": "27", "preset": "speed", "resolution": "720",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "amd_igpu"
        },
        # === CPU (libx265/libx264) ===
        "cpu_qualidade_filmes_1080p_hevc": {
            "name": "CPU Qualidade Filmes 1080p HEVC",
            "description": "Máxima qualidade CPU - libx265 CRF 18, slow preset",
            "codec": "libx265", "cq": "18", "preset": "slow", "resolution": "1080",
            "hdr_to_sdr": False, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "cpu"
        },
        "cpu_qualidade_filmes_1080p_h264": {
            "name": "CPU Qualidade Filmes 1080p H264",
            "description": "Máxima qualidade CPU - libx264 CRF 18, slow preset",
            "codec": "libx264", "cq": "18", "preset": "slow", "resolution": "1080",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "cpu"
        },
        "cpu_qualidade_series_1080p_hevc": {
            "name": "CPU Qualidade Series 1080p HEVC",
            "description": "Qualidade CPU séries - libx265 CRF 20, medium preset",
            "codec": "libx265", "cq": "20", "preset": "medium", "resolution": "1080",
            "hdr_to_sdr": False, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "cpu"
        },
        "cpu_qualidade_series_1080p_h264": {
            "name": "CPU Qualidade Series 1080p H264",
            "description": "Qualidade CPU séries - libx264 CRF 20, medium preset",
            "codec": "libx264", "cq": "20", "preset": "medium", "resolution": "1080",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "cpu"
        },
        "cpu_rapido_filmes_1080p_hevc": {
            "name": "CPU Rápido Filmes 1080p HEVC",
            "description": "Encoding rápido CPU - libx265 CRF 22, veryfast preset",
            "codec": "libx265", "cq": "22", "preset": "veryfast", "resolution": "1080",
            "hdr_to_sdr": False, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "cpu"
        },
        "cpu_rapido_filmes_1080p_h264": {
            "name": "CPU Rápido Filmes 1080p H264",
            "description": "Encoding rápido CPU - libx264 CRF 22, veryfast preset",
            "codec": "libx264", "cq": "22", "preset": "veryfast", "resolution": "1080",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "cpu"
        },
        "cpu_rapido_series_1080p_hevc": {
            "name": "CPU Rápido Series 1080p HEVC",
            "description": "Rápido séries CPU - libx265 CRF 24, veryfast preset",
            "codec": "libx265", "cq": "24", "preset": "veryfast", "resolution": "1080",
            "hdr_to_sdr": False, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "cpu"
        },
        "cpu_rapido_series_1080p_h264": {
            "name": "CPU Rápido Series 1080p H264",
            "description": "Rápido séries CPU - libx264 CRF 24, veryfast preset",
            "codec": "libx264", "cq": "24", "preset": "veryfast", "resolution": "1080",
            "hdr_to_sdr": True, "deinterlace": False, "plex_compatible": True, "two_pass": False,
            "hardware_category": "cpu"
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
    
    def get_profiles_by_hardware_category(self, category: str) -> List[Dict[str, Any]]:
        """Filtra perfis por categoria de hardware."""
        return [
            {"id": pid, **data}
            for pid, data in self._profiles.items()
            if not pid.startswith('_') and isinstance(data, dict) 
            and data.get('hardware_category') == category
        ]
    
    def get_profiles_for_codec(self, codec: str) -> List[Dict[str, Any]]:
        """Filtra perfis por codec."""
        return [
            {"id": pid, **data}
            for pid, data in self._profiles.items()
            if not pid.startswith('_') and isinstance(data, dict) 
            and data.get('codec') == codec
        ]
    
    def get_recommended_profiles(self, hardware_detector: HardwareDetector, content_type: str = "filmes", resolution: str = "1080") -> List[Dict[str, Any]]:
        """Retorna perfis recomendados baseados no hardware detectado."""
        caps = hardware_detector.detect()
        profile_ids = caps.get_recommended_profiles() if caps else []
        
        recommended_profiles = []
        for profile_id in profile_ids:
            profile = self.get_profile(profile_id)
            if profile:
                recommended_profiles.append({
                    "id": profile_id,
                    **profile
                })
        
        return recommended_profiles
    
    def validate_profile_for_hardware(self, profile_id: str, hardware_detector: HardwareDetector) -> tuple[bool, str]:
        """Valida se perfil é compatível com hardware detectado."""
        profile = self.get_profile(profile_id)
        if not profile:
            return (False, f"Perfil não encontrado: {profile_id}")
        
        codec = profile.get('codec', '')
        caps = hardware_detector.detect()
        
        codec_available = codec in (caps.available_codecs if caps else [])
        
        if not codec_available:
            return (False, f"Codec '{codec}' não disponível no sistema")
        
        return (True, f"Perfil '{profile_id}' compatível com hardware")
    
    def get_hardware_detection_summary(self) -> Dict[str, Any]:
        """Retorna resumo da detecção de hardware e perfis disponíveis."""
        detector = HardwareDetector()
        caps = detector.detect()
        
        hw_info = caps.to_dict() if caps else {}
        
        categories = {
            "nvidia_gpu": len([p for p in self.list_profiles() if p.get('hardware_category') == 'nvidia_gpu']),
            "amd_gpu": len([p for p in self.list_profiles() if p.get('hardware_category') == 'amd_gpu']),
            "intel_igpu": len([p for p in self.list_profiles() if p.get('hardware_category') == 'intel_igpu']),
            "amd_igpu": len([p for p in self.list_profiles() if p.get('hardware_category') == 'amd_igpu']),
            "cpu": len([p for p in self.list_profiles() if p.get('hardware_category') == 'cpu'])
        }
        
        return {
            "hardware": hw_info,
            "profiles_by_category": categories,
            "total_profiles": len(self.list_profiles())
        }
