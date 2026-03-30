import os
import re
from pathlib import Path
from typing import Optional


class PathUtils:
    """Utilitários para manipulação de caminhos."""
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """Normaliza caminho para formato do sistema operacional."""
        if not path:
            return path
        
        path = path.strip()
        
        if path.startswith('/mnt/'):
            wsl_path = path[5:]
            drive_letter = wsl_path[0].upper()
            rest = wsl_path[2:].replace('/', '\\')
            return f"{drive_letter}:\\{rest}"
        
        if path.startswith('/'):
            parts = path.split('/')
            if len(parts) >= 3:
                drive_letter = parts[1].upper()
                if drive_letter.endswith(':'):
                    drive_letter = drive_letter[0]
                rest = '\\'.join(parts[2:])
                return f"{drive_letter}:\\{rest}"
        
        return os.path.normpath(path)
    
    @staticmethod
    def to_wsl_path(windows_path: str) -> str:
        """Converte caminho Windows para formato WSL."""
        if not windows_path:
            return windows_path
        
        windows_path = windows_path.strip()
        
        drive_match = re.match(r'^([A-Za-z]):[\\/](.*)$', windows_path)
        if drive_match:
            drive = drive_match.group(1).lower()
            rest = drive_match.group(2).replace('\\', '/')
            return f"/mnt/{drive}/{rest}"
        
        return windows_path
    
    @staticmethod
    def is_absolute_path(path: str) -> bool:
        """Verifica se caminho é absoluto."""
        return os.path.isabs(PathUtils.normalize_path(path))
    
    @staticmethod
    def ensure_directory(directory: str) -> bool:
        """Cria diretório se não existir."""
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_safe_filename(filename: str, max_length: int = 255) -> str:
        """Gera nome de arquivo seguro."""
        unsafe_chars = r'<>:"/\|?*'
        safe_name = filename
        
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')
        
        safe_name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', safe_name)
        safe_name = safe_name.strip('. ')
        
        if len(safe_name) > max_length:
            name, ext = os.path.splitext(safe_name)
            max_name_length = max_length - len(ext)
            safe_name = name[:max_name_length] + ext
        
        return safe_name if safe_name else 'unnamed_file'
    
    @staticmethod
    def generate_output_path(
        input_path: str,
        output_dir: str,
        suffix: Optional[str] = None,
        extension: Optional[str] = None
    ) -> str:
        """Gera caminho de output baseado no input."""
        input_path = PathUtils.normalize_path(input_path)
        input_file = Path(input_path)
        
        stem = input_file.stem
        ext = extension or input_file.suffix
        
        if suffix:
            output_filename = f"{stem}{suffix}{ext}"
        else:
            output_filename = f"{stem}{ext}"
        
        output_filename = PathUtils.get_safe_filename(output_filename)
        
        output_path = Path(output_dir) / output_filename
        
        counter = 1
        while output_path.exists():
            output_filename = f"{stem}{suffix or ''}_{counter}{ext}"
            output_filename = PathUtils.get_safe_filename(output_filename)
            output_path = Path(output_dir) / output_filename
            counter += 1
        
        return str(output_path)
    
    @staticmethod
    def get_relative_path(path: str, base: str) -> str:
        """Retorna caminho relativo."""
        try:
            return str(Path(path).relative_to(base))
        except ValueError:
            return path
    
    @staticmethod
    def join_paths(*paths: str) -> str:
        """Junta múltiplos caminhos."""
        normalized = [PathUtils.normalize_path(p) for p in paths]
        return str(Path(*normalized))
    
    @staticmethod
    def get_file_size(path: str) -> int:
        """Retorna tamanho do arquivo em bytes."""
        try:
            return Path(path).stat().st_size
        except Exception:
            return 0
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Formata tamanho em formato legível."""
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"  # type: ignore[misc]
            size /= 1024.0
        return f"{size:.2f} PB"
