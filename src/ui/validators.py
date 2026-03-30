import re
from pathlib import Path
from typing import Tuple


class Validators:
    """Validadores de input."""
    
    @staticmethod
    def validate_file_exists(path: str) -> Tuple[bool, str]:
        """Valida se arquivo existe."""
        if not path:
            return False, "Caminho vazio"
        
        if not Path(path).exists():
            return False, f"Arquivo não encontrado: {path}"
        
        if not Path(path).is_file():
            return False, f"Não é um arquivo: {path}"
        
        return True, ""
    
    @staticmethod
    def validate_directory_exists(path: str, create_if_not: bool = False) -> Tuple[bool, str]:
        """Valida se diretório existe."""
        if not path:
            return False, "Caminho vazio"
        
        path_obj = Path(path)
        
        if not path_obj.exists():
            if create_if_not:
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                    return True, ""
                except Exception as e:
                    return False, f"Erro ao criar diretório: {e}"
            return False, f"Diretório não encontrado: {path}"
        
        if not path_obj.is_dir():
            return False, f"Não é um diretório: {path}"
        
        return True, ""
    
    @staticmethod
    def validate_video_file(path: str) -> Tuple[bool, str]:
        """Valida se arquivo é vídeo."""
        valid, error = Validators.validate_file_exists(path)
        if not valid:
            return False, error
        
        video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpeg', '.mpg'}
        ext = Path(path).suffix.lower()
        
        if ext not in video_extensions:
            return False, f"Extensão não suportada: {ext}"
        
        return True, ""
    
    @staticmethod
    def validate_codec(codec: str) -> Tuple[bool, str]:
        """Valida codec de vídeo."""
        valid_codecs = ['hevc_nvenc', 'h264_nvenc', 'av1_nvenc']
        
        if codec.lower() not in valid_codecs:
            return False, f"Codec inválido. Opções: {', '.join(valid_codecs)}"
        
        return True, ""
    
    @staticmethod
    def validate_cq(cq: str, codec: str = 'hevc_nvenc') -> Tuple[bool, str]:
        """Valida valor CQ (Constant Quality)."""
        try:
            cq_int = int(cq)
            
            ranges = {
                'hevc_nvenc': (1, 51),
                'h264_nvenc': (1, 51),
                'av1_nvenc': (1, 63)
            }
            
            min_cq, max_cq = ranges.get(codec, (1, 51))
            
            if cq_int < min_cq or cq_int > max_cq:
                return False, f"CQ deve estar entre {min_cq} e {max_cq} para {codec}"
            
            return True, ""
        except ValueError:
            return False, "CQ deve ser um número inteiro"
    
    @staticmethod
    def validate_bitrate(bitrate: str) -> Tuple[bool, str]:
        """Valida formato de bitrate."""
        if not bitrate:
            return True, ""
        
        pattern = r'^\d+[KMG]?$'
        if not re.match(pattern, bitrate, re.IGNORECASE):
            return False, "Bitrate deve estar no formato: 10M, 5000K, etc."
        
        return True, ""
    
    @staticmethod
    def validate_resolution(resolution: str) -> Tuple[bool, str]:
        """Valida resolução."""
        if not resolution:
            return True, ""
        
        valid_resolutions = ['480', '720', '1080', '1440', '2160', '4k']
        
        if resolution.lower() not in valid_resolutions:
            return False, f"Resoluções válidas: {', '.join(valid_resolutions)}"
        
        return True, ""
    
    @staticmethod
    def validate_preset(preset: str) -> Tuple[bool, str]:
        """Valida preset NVENC."""
        valid_presets = ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7']
        
        if preset.lower() not in valid_presets:
            return False, f"Presets válidos: {', '.join(valid_presets)} (p1=más rápido, p7=más lento)"
        
        return True, ""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Valida formato de email."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False, "Formato de email inválido"
        
        return True, ""
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """Valida formato de URL."""
        pattern = r'^https?://[^\s]+$'
        
        if not re.match(pattern, url):
            return False, "URL deve começar com http:// ou https://"
        
        return True, ""
    
    @staticmethod
    def validate_profile_name(name: str) -> Tuple[bool, str]:
        """Valida nome de perfil."""
        if not name or len(name.strip()) < 3:
            return False, "Nome deve ter pelo menos 3 caracteres"
        
        if len(name) > 50:
            return False, "Nome deve ter no máximo 50 caracteres"
        
        return True, ""
    
    @staticmethod
    def validate_disk_space(path: str, required_gb: float) -> Tuple[bool, str]:
        """Valida espaço em disco disponível."""
        try:
            import psutil
            disk_usage = psutil.disk_usage(path)
            free_gb = disk_usage.free / (1024 ** 3)
            
            if free_gb < required_gb:
                return False, f"Espaço insuficiente: {free_gb:.1f} GB disponíveis, {required_gb} GB necessários"
            
            return True, ""
        except ImportError:
            return True, ""
        except Exception as e:
            return False, f"Erro ao verificar espaço: {e}"
