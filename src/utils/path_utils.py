import os
import re
from pathlib import Path
from typing import Optional, Tuple
from enum import Enum

# Import tardio para evitar circular dependency
def _get_file_utils():
    from .file_utils import FileUtils
    return FileUtils


class RemoteProtocol(Enum):
    """Protocolos remotos suportados."""
    LOCAL = "local"
    SSHFS = "sshfs"
    SMB = "smb"
    NFS = "nfs"
    MOUNTED = "mounted"
    UNC = "unc"


class PathUtils:
    """Utilitários para manipulação de caminhos."""
    
    # Padrões para detecção de caminhos remotos
    SSHFS_PATTERN = re.compile(r'^ssh://[^@]+@[^/]+/.+')
    SMB_PATTERN = re.compile(r'^smb://[^/]+/.+')
    NFS_PATTERN = re.compile(r'^nfs://[^/]+/.+')
    UNC_PATTERN = re.compile(r'^\\\\[^\\]+\\[^\\]+')
    MOUNTED_PATTERN = re.compile(r'^mounted://.+')
    
    @staticmethod
    def is_remote_path(path: str) -> bool:
        """
        Verifica se o caminho é um caminho remoto.
        
        Args:
            path: Caminho a ser verificado.
            
        Returns:
            True se o caminho é remoto, False caso contrário.
        """
        if not path:
            return False
        
        path = path.strip()
        
        # Verifica padrões de URL
        if path.startswith('ssh://'):
            return True
        if path.startswith('smb://'):
            return True
        if path.startswith('nfs://'):
            return True
        if path.startswith('mounted://'):
            return True
        
        # Verifica caminho UNC Windows
        if path.startswith('\\\\'):
            return True
        
        return False
    
    @staticmethod
    def get_protocol(path: str) -> Optional[RemoteProtocol]:
        """
        Identifica o protocolo do caminho remoto.
        
        Args:
            path: Caminho a ser verificado.
            
        Returns:
            RemoteProtocol ou None se for caminho local.
        """
        if not path:
            return None
        
        path = path.strip()
        
        if path.startswith('ssh://'):
            return RemoteProtocol.SSHFS
        if path.startswith('smb://'):
            return RemoteProtocol.SMB
        if path.startswith('nfs://'):
            return RemoteProtocol.NFS
        if path.startswith('mounted://'):
            return RemoteProtocol.MOUNTED
        if path.startswith('\\\\'):
            return RemoteProtocol.UNC
        
        return RemoteProtocol.LOCAL
    
    @staticmethod
    def parse_remote_path(path: str) -> dict:
        """
        Analisa um caminho remoto e extrai componentes.
        
        Args:
            path: Caminho remoto a ser analisado.
            
        Returns:
            Dicionário com componentes do caminho.
        """
        if not PathUtils.is_remote_path(path):
            return {'error': 'Caminho não é remoto'}
        
        protocol = PathUtils.get_protocol(path)
        
        if protocol == RemoteProtocol.SSHFS:
            # ssh://user@host:port/path
            pattern = re.compile(r'^ssh://(?P<user>[^@]+)@(?P<host>[^:/]+)(?::(?P<port>\d+))?(?P<path>/.*)$')
            match = pattern.match(path)
            if match:
                return {
                    'protocol': 'sshfs',
                    'user': match.group('user'),
                    'host': match.group('host'),
                    'port': int(match.group('port')) if match.group('port') else 22,
                    'path': match.group('path')
                }
        
        elif protocol == RemoteProtocol.SMB:
            # smb://host/share/path
            pattern = re.compile(r'^smb://(?P<host>[^/]+)/(?P<share>[^/]+)(?P<path>/.*?)?$')
            match = pattern.match(path)
            if match:
                return {
                    'protocol': 'smb',
                    'host': match.group('host'),
                    'share': match.group('share'),
                    'path': match.group('path') or '/'
                }
        
        elif protocol == RemoteProtocol.NFS:
            # nfs://host/export/path
            pattern = re.compile(r'^nfs://(?P<host>[^/]+)/(?P<export>[^/]+)(?P<path>/.*?)?$')
            match = pattern.match(path)
            if match:
                return {
                    'protocol': 'nfs',
                    'host': match.group('host'),
                    'export': match.group('export'),
                    'path': match.group('path') or '/'
                }
        
        elif protocol == RemoteProtocol.MOUNTED:
            # mounted://mount_point/path
            pattern = re.compile(r'^mounted://(?P<mount_point>[^/]+)(?P<path>/.*?)?$')
            match = pattern.match(path)
            if match:
                return {
                    'protocol': 'mounted',
                    'mount_point': match.group('mount_point'),
                    'path': match.group('path') or '/'
                }
        
        elif protocol == RemoteProtocol.UNC:
            # \\host\share\path
            pattern = re.compile(r'^\\\\(?P<host>[^\\]+)\\(?P<share>[^\\]+)(?P<path>\\.*)?$')
            match = pattern.match(path)
            if match:
                return {
                    'protocol': 'unc',
                    'host': match.group('host'),
                    'share': match.group('share'),
                    'path': match.group('path').replace('\\', '/') if match.group('path') else '/'
                }
        
        return {'error': 'Não foi possível analisar o caminho'}
    
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
    def get_safe_filename(filename: str, max_length: int = 180) -> str:
        """Gera nome de arquivo seguro com limite reduzido para evitar paths muito longos."""
        unsafe_chars = r'<>:"/\|?*'
        safe_name = filename
        
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')
        
        # Remove caracteres de controle ASCII, mas preserva caracteres UTF-8 válidos
        # Ajuste: remover apenas caracteres de controle realmente problemáticos
        safe_name = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', safe_name)
        # Remove múltiplos underscores consecutivos
        safe_name = re.sub(r'_{2,}', '_', safe_name)
        safe_name = safe_name.strip('. _')
        
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
        extension: Optional[str] = None,
        codec: Optional[str] = None,
        cq: Optional[str] = None,
        handle_conflict: bool = True
    ) -> str:
        """Gera caminho de output baseado no input.
        Se codec e cq forem fornecidos, gera sufixo automático _{codec}_cq{cq}.
        
        Args:
            input_path: Caminho do arquivo de entrada
            output_dir: Diretório de saída
            suffix: Sufixo personalizado (opcional)
            extension: Extensão personalizada (opcional)
            codec: Codec para gerar sufixo automático
            cq: Valor CQ para gerar sufixo automático
            handle_conflict: Se True, gera nome único se arquivo existir (default: True)
        
        Returns:
            Caminho completo do arquivo de saída
        """
        input_path = PathUtils.normalize_path(input_path)
        input_file = Path(input_path)

        stem = input_file.stem
        ext = extension or input_file.suffix

        # Simplificar nome se codec for fornecido (para evitar paths muito longos)
        if codec:
            # Truncar nome base se for muito longo
            max_stem_length = 80
            if len(stem) > max_stem_length:
                stem = stem[:max_stem_length]
            
            suffix = f"_{codec}"
            if cq:
                suffix += f"_cq{cq}"

        if suffix:
            output_filename = f"{stem}{suffix}{ext}"
        else:
            output_filename = f"{stem}{ext}"

        output_filename = PathUtils.get_safe_filename(output_filename)

        output_path = Path(output_dir) / output_filename

        # Se handle_conflict estiver habilitado, usa FileUtils para gerar nome único
        if handle_conflict and output_path.exists():
            return _get_file_utils().generate_unique_filename(str(output_path))

        return str(output_path)

    @staticmethod
    def generate_output_dir_name(
        folder_name: str,
        codec: str,
        cq: Optional[str] = None
    ) -> str:
        """Gera nome de pasta de saída com codec e CQ."""
        if cq:
            return f"{folder_name}_{codec}_cq{cq}"
        return f"{folder_name}_{codec}"
    
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
