"""
Cliente para diretórios montados (rclone, etc.).

Este módulo implementa o cliente para diretórios que já estão montados
no sistema de arquivos local, como mounts do rclone, Google Drive, etc.
"""

import os
import shutil
from pathlib import Path
from typing import List, Tuple, Callable, Optional, Dict, Any

from .remote_protocol import RemoteProtocol


class MountedClient(RemoteProtocol):
    """
    Cliente para diretórios montados.
    
    Usado para acessar diretórios que já estão montados no sistema
    de arquivos local, como:
    - rclone mounts (Google Drive, OneDrive, etc.)
    - Network mounts (NFS, CIFS montados via sistema)
    - FUSE mounts
    """
    
    def __init__(self):
        """Inicializa o cliente para diretórios montados."""
        super().__init__()
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Verifica se o ponto de mount existe e está acessível.
        
        Args:
            config: Configuração contendo:
                - mount_point: Ponto de mount (ex: X:, /mnt/gdrive)
                - path: Caminho dentro do mount
                - mount_type: Tipo de mount (ex: 'rclone', 'nfs', 'cifs')
                
        Returns:
            True se o mount point está acessível, False caso contrário.
        """
        try:
            mount_point = config.get('mount_point')
            
            if not mount_point:
                return False
            
            # Verificar se o mount point existe
            if not os.path.exists(mount_point):
                return False
            
            # Verificar se é um diretório
            if not os.path.isdir(mount_point):
                return False
            
            # Verificar se está acessível (pode ler o diretório)
            os.listdir(mount_point)
            
            self._config = config
            self._connected = True
            
            return True
            
        except Exception as e:
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Desconecta (apenas marca como desconectado)."""
        self._connected = False
    
    def _get_base_path(self) -> str:
        """
        Obtém o caminho base do mount.
        
        Returns:
            Caminho base combinando mount_point e path.
        """
        mount_point = self._config.get('mount_point', '')
        path = self._config.get('path', '/')
        
        # Combinar mount_point com path
        if path and path != '/':
            path = path.lstrip('/')
            return os.path.join(mount_point, path)
        
        return mount_point
    
    def list_files(self, path: str, extensions: Optional[List[str]] = None) -> List[str]:
        """
        Lista arquivos de vídeo em um diretório montado.
        
        Args:
            path: Caminho dentro do mount.
            extensions: Lista de extensões para filtrar.
            
        Returns:
            Lista de caminhos completos dos arquivos encontrados.
        """
        if not self._ensure_connected():
            return []
        
        video_extensions = extensions or [
            '.mp4', '.mkv', '.avi', '.mov', '.wmv', 
            '.flv', '.webm', '.m4v', '.mpeg', '.mpg'
        ]
        
        files = []
        base_path = self._get_base_path()
        
        # Combinar base_path com o path fornecido
        if path and path != '/':
            path = path.lstrip('/')
            full_path = os.path.join(base_path, path) if path else base_path
        else:
            full_path = base_path
        
        try:
            # Listar diretório recursivamente
            self._walk_directory(full_path, video_extensions, files)
        except Exception:
            pass
        
        return sorted(files)
    
    def _walk_directory(self, dir_path: str, extensions: List[str], files: List[str]) -> None:
        """
        Caminha recursivamente por um diretório montado.
        
        Args:
            dir_path: Caminho do diretório.
            extensions: Extensões para filtrar.
            files: Lista para adicionar arquivos encontrados.
        """
        try:
            for entry in os.scandir(dir_path):
                try:
                    if entry.is_dir(follow_symlinks=False):
                        # Diretório: recursão
                        self._walk_directory(entry.path, extensions, files)
                    elif entry.is_file(follow_symlinks=False):
                        # Arquivo: verificar extensão
                        if self._matches_extension(entry.name, extensions):
                            files.append(entry.path)
                except Exception:
                    # Ignora entradas com erro de acesso
                    pass
                        
        except Exception:
            pass
    
    def copy_file(
        self, 
        remote_path: str, 
        local_path: str, 
        callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Copia um arquivo do diretório montado para o local.
        
        Args:
            remote_path: Caminho do arquivo no mount.
            local_path: Caminho do arquivo local de destino.
            callback: Callback para progresso (bytes_copiados, total_bytes).
            
        Returns:
            True se copiado com sucesso, False caso contrário.
        """
        if not self._ensure_connected():
            return False
        
        try:
            # Garantir diretório local existe
            self._ensure_local_directory(local_path)
            
            # Obter tamanho do arquivo remoto
            total_size = os.path.getsize(remote_path)
            
            # Copiar arquivo com callback de progresso
            with open(remote_path, 'rb') as src:
                with open(local_path, 'wb') as dst:
                    copied = 0
                    chunk_size = 1024 * 1024  # 1MB chunks
                    
                    while True:
                        chunk = src.read(chunk_size)
                        if not chunk:
                            break
                        
                        dst.write(chunk)
                        copied += len(chunk)
                        
                        if callback:
                            callback(copied, total_size)
            
            return True
            
        except Exception as e:
            return False
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Testa o acesso ao diretório montado.
        
        Returns:
            Tuple com (sucesso, mensagem).
        """
        if not self._config:
            return (False, "Nenhuma configuração fornecida")
        
        try:
            mount_point = self._config.get('mount_point')
            
            if not mount_point:
                return (False, "Mount point não especificado")
            
            if not os.path.exists(mount_point):
                return (False, f"Mount point não existe: {mount_point}")
            
            if not os.path.isdir(mount_point):
                return (False, f"Mount point não é um diretório: {mount_point}")
            
            # Testar leitura do diretório
            os.listdir(mount_point)
            
            return (True, "Mount point acessível")
            
        except PermissionError:
            return (False, "Permissão negada")
        except Exception as e:
            return (False, f"Erro: {str(e)}")
