"""
Cliente SMB/CIFS para acesso a shares Windows/Samba.

Este módulo implementa o cliente SMB que usa a biblioteca smbprotocol
para conectar e copiar arquivos de shares Windows ou Samba.
"""

import os
from pathlib import Path
from typing import List, Tuple, Callable, Optional, Dict, Any
from datetime import datetime

from .remote_protocol import RemoteProtocol


class SMBClient(RemoteProtocol):
    """
    Cliente SMB para shares Windows/Samba.
    
    Usa smbprotocol para acessar shares SMB/CIFS.
    """
    
    DEFAULT_PORT = 445
    
    def __init__(self):
        """Inicializa o cliente SMB."""
        super().__init__()
        self._connection = None
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Conecta ao servidor SMB.
        
        Args:
            config: Configuração contendo:
                - host: Endereço do servidor SMB
                - port: Porta SMB (padrão: 445)
                - share: Nome do share
                - username: Nome de usuário
                - password: Senha
                - path: Caminho dentro do share
                
        Returns:
            True se conectado com sucesso, False caso contrário.
        """
        try:
            from smbclient import register_session
            
            host = config.get('host')
            port = config.get('port', self.DEFAULT_PORT)
            share = config.get('share')
            username = config.get('username')
            password = config.get('password')
            
            if not host or not share:
                return False
            
            # Registrar sessão SMB
            register_session(
                server=host,
                username=username,
                password=password,
                port=port
            )
            
            self._config = config
            self._connected = True
            
            return True
            
        except Exception as e:
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Desconecta do servidor SMB."""
        try:
            from smbclient import delete_session
            
            if self._config and self._config.get('host'):
                delete_session(self._config.get('host'))
        except Exception:
            pass
        finally:
            self._connected = False
            self._connection = None
    
    def _get_base_path(self) -> str:
        """
        Obtém o caminho base UNC.
        
        Returns:
            Caminho UNC base.
        """
        host = self._config.get('host', '')
        share = self._config.get('share', '')
        path = self._config.get('path', '/')
        
        # Remover barras iniciais do path
        path = path.lstrip('/')
        
        return f"\\\\{host}\\{share}\\{path}" if path else f"\\\\{host}\\{share}"
    
    def list_files(self, path: str, extensions: Optional[List[str]] = None) -> List[str]:
        """
        Lista arquivos de vídeo em um diretório SMB.
        
        Args:
            path: Caminho dentro do share.
            extensions: Lista de extensões para filtrar.
            
        Returns:
            Lista de caminhos completos dos arquivos encontrados.
        """
        if not self._ensure_connected():
            return []
        
        import smbclient
        
        video_extensions = extensions or [
            '.mp4', '.mkv', '.avi', '.mov', '.wmv', 
            '.flv', '.webm', '.m4v', '.mpeg', '.mpg'
        ]
        
        files = []
        base_path = self._get_base_path()
        
        # Combinar base_path com o path fornecido
        if path and path != '/':
            path = path.lstrip('/')
            full_path = f"{base_path}\\{path}" if path else base_path
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
        Caminha recursivamente por um diretório SMB.
        
        Args:
            remote_path: Caminho do diretório remoto.
            extensions: Extensões para filtrar.
            files: Lista para adicionar arquivos encontrados.
        """
        import smbclient
        
        try:
            entries = smbclient.listdir(remote_path)
            
            for entry in entries:
                full_path = f"{remote_path}\\{entry}"
                
                try:
                    stat_info = smbclient.stat(full_path)
                    
                    if stat_info.st_file_attributes & 0x10:  # FILE_ATTRIBUTE_DIRECTORY
                        # Diretório: recursão
                        self._walk_directory(full_path, extensions, files)
                    else:
                        # Arquivo: verificar extensão
                        if self._matches_extension(entry, extensions):
                            files.append(full_path)
                            
                except Exception:
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
        Copia um arquivo do share SMB para o local.
        
        Args:
            remote_path: Caminho do arquivo remoto.
            local_path: Caminho do arquivo local de destino.
            callback: Callback para progresso (bytes_copiados, total_bytes).
            
        Returns:
            True se copiado com sucesso, False caso contrário.
        """
        if not self._ensure_connected():
            return False
        
        import smbclient
        
        try:
            # Garantir diretório local existe
            self._ensure_local_directory(local_path)
            
            # Obter tamanho do arquivo remoto
            remote_stat = smbclient.stat(remote_path)
            total_size = remote_stat.st_size
            
            # Copiar arquivo
            with smbclient.open_file(remote_path, mode='rb') as src:
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
        Testa a conexão com o servidor SMB.
        
        Returns:
            Tuple com (sucesso, mensagem).
        """
        if not self._config:
            return (False, "Nenhuma configuração fornecida")
        
        import smbclient
        
        try:
            base_path = self._get_base_path()
            smbclient.listdir(base_path)
            return (True, "Conexão bem-sucedida")
        except smbclient.exceptions.SMBOSError as e:
            if e.errno == 2:  # File not found
                return (True, "Conectado, mas diretório não existe")
            return (False, f"Erro SMB: {str(e)}")
        except Exception as e:
            return (False, f"Erro: {str(e)}")
