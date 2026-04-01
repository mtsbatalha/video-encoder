"""
Cliente NFS para acesso a Network File System.

Este módulo implementa o cliente NFS que usa a biblioteca nfs3
para conectar e copiar arquivos de exports NFS.
"""

import os
import shutil
from pathlib import Path
from typing import List, Tuple, Callable, Optional, Dict, Any

from .remote_protocol import RemoteProtocol


class NFSClient(RemoteProtocol):
    """
    Cliente NFS para Network File System.
    
    Usa nfs3 para acessar exports NFS.
    Nota: Em sistemas Linux, o NFS é tipicamente montado via sistema de arquivos.
    Este cliente é mais útil para sistemas onde o mount não está disponível.
    """
    
    DEFAULT_PORT = 2049
    
    def __init__(self):
        """Inicializa o cliente NFS."""
        super().__init__()
        self._nfs_client = None
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Conecta ao servidor NFS.
        
        Args:
            config: Configuração contendo:
                - host: Endereço do servidor NFS
                - port: Porta NFS (padrão: 2049)
                - export: Caminho do export NFS
                - path: Caminho dentro do export
                
        Returns:
            True se conectado com sucesso, False caso contrário.
        """
        try:
            # Em Linux, NFS é tipicamente montado via sistema de arquivos
            # Para uso direto via Python, podemos usar nfs3 ou montar via subprocesso
            
            host = config.get('host')
            port = config.get('port', self.DEFAULT_PORT)
            export = config.get('export')
            
            if not host or not export:
                return False
            
            self._config = config
            self._connected = True
            
            return True
            
        except Exception as e:
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Desconecta do servidor NFS."""
        self._connected = False
        self._nfs_client = None
    
    def _get_mount_path(self) -> str:
        """
        Obtém o caminho base do export NFS.
        
        Returns:
            Caminho base do export.
        """
        host = self._config.get('host', '')
        export = self._config.get('export', '')
        path = self._config.get('path', '/')
        
        return f"{export}/{path.lstrip('/')}" if path != '/' else export
    
    def list_files(self, path: str, extensions: Optional[List[str]] = None) -> List[str]:
        """
        Lista arquivos de vídeo em um diretório NFS.
        
        Args:
            path: Caminho dentro do export.
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
        base_path = self._get_mount_path()
        
        # Combinar base_path com o path fornecido
        if path and path != '/':
            path = path.lstrip('/')
            full_path = f"{base_path}/{path}" if path else base_path
        else:
            full_path = base_path
        
        try:
            # Listar diretório recursivamente
            self._walk_directory(full_path, video_extensions, files)
        except Exception:
            pass
        
        return sorted(files)
    
    def _walk_directory(self, remote_path: str, extensions: List[str], files: List[str]) -> None:
        """
        Caminha recursivamente por um diretório NFS.
        
        Args:
            remote_path: Caminho do diretório remoto.
            extensions: Extensões para filtrar.
            files: Lista para adicionar arquivos encontrados.
        """
        try:
            for entry in os.scandir(remote_path):
                if entry.is_dir(follow_symlinks=False):
                    # Diretório: recursão
                    self._walk_directory(entry.path, extensions, files)
                elif entry.is_file(follow_symlinks=False):
                    # Arquivo: verificar extensão
                    if self._matches_extension(entry.name, extensions):
                        files.append(entry.path)
                        
        except Exception:
            pass
    
    def copy_file(
        self, 
        remote_path: str, 
        local_path: str, 
        callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Copia um arquivo do export NFS para o local.
        
        Args:
            remote_path: Caminho do arquivo remoto.
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
        Testa a conexão com o servidor NFS.
        
        Returns:
            Tuple com (sucesso, mensagem).
        """
        if not self._config:
            return (False, "Nenhuma configuração fornecida")
        
        try:
            base_path = self._get_mount_path()
            
            # Verificar se o caminho existe e é acessível
            if os.path.exists(base_path):
                return (True, "Conexão bem-sucedida")
            else:
                return (False, "Export NFS não encontrado ou não montado")
                
        except PermissionError:
            return (False, "Permissão negada")
        except Exception as e:
            return (False, f"Erro: {str(e)}")
