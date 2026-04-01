"""
Cliente SSHFS para acesso a filesystems remotos via SSH.

Este módulo implementa o cliente SSHFS que usa a biblioteca paramiko
para conectar e copiar arquivos de servidores remotos via SFTP.
"""

import os
import stat
from pathlib import Path
from typing import List, Tuple, Callable, Optional, Dict, Any

from .remote_protocol import RemoteProtocol


class SSHFSClient(RemoteProtocol):
    """
    Cliente SSHFS para filesystem sobre SSH.
    
    Usa paramiko para estabelecer conexão SFTP e transferir arquivos.
    """
    
    DEFAULT_PORT = 22
    DEFAULT_TIMEOUT = 30
    
    def __init__(self):
        """Inicializa o cliente SSHFS."""
        super().__init__()
        self._sftp = None
        self._ssh_client = None
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Conecta ao servidor SSH via SFTP.
        
        Args:
            config: Configuração contendo:
                - host: Endereço do servidor SSH
                - port: Porta SSH (padrão: 22)
                - username: Nome de usuário
                - password: Senha (opcional)
                - private_key_path: Caminho da chave privada (opcional)
                - path: Caminho remoto base
                
        Returns:
            True se conectado com sucesso, False caso contrário.
        """
        try:
            import paramiko
            
            host = config.get('host')
            port = config.get('port', self.DEFAULT_PORT)
            username = config.get('username')
            password = config.get('password')
            private_key_path = config.get('private_key_path')
            
            if not host or not username:
                return False
            
            # Criar cliente SSH
            self._ssh_client = paramiko.SSHClient()
            self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Conectar via SSH
            if private_key_path and os.path.exists(private_key_path):
                # Usar chave privada
                pkey = paramiko.RSAKey.from_private_key_file(private_key_path)
                self._ssh_client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    pkey=pkey,
                    timeout=self.DEFAULT_TIMEOUT
                )
            else:
                # Usar senha
                self._ssh_client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=password,
                    timeout=self.DEFAULT_TIMEOUT
                )
            
            # Abrir sessão SFTP
            self._sftp = self._ssh_client.open_sftp()
            
            self._config = config
            self._connected = True
            
            return True
            
        except Exception as e:
            self._connected = False
            self._sftp = None
            self._ssh_client = None
            return False
    
    def disconnect(self) -> None:
        """Desconecta do servidor SSH."""
        try:
            if self._sftp:
                self._sftp.close()
                self._sftp = None
            
            if self._ssh_client:
                self._ssh_client.close()
                self._ssh_client = None
        except Exception:
            pass
        finally:
            self._connected = False
    
    def list_files(self, path: str, extensions: Optional[List[str]] = None) -> List[str]:
        """
        Lista arquivos de vídeo em um diretório remoto.
        
        Args:
            path: Caminho do diretório remoto.
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
        
        try:
            # Listar diretório recursivamente
            self._walk_directory(path, video_extensions, files)
        except Exception:
            pass
        
        return sorted(files)
    
    def _walk_directory(self, remote_path: str, extensions: List[str], files: List[str]) -> None:
        """
        Caminha recursivamente por um diretório remoto.
        
        Args:
            remote_path: Caminho do diretório remoto.
            extensions: Extensões para filtrar.
            files: Lista para adicionar arquivos encontrados.
        """
        try:
            entries = self._sftp.listdir_attr(remote_path)
            
            for entry in entries:
                full_path = f"{remote_path}/{entry.filename}"
                
                # Ignorar . e ..
                if entry.filename in ('.', '..'):
                    continue
                
                if stat.S_ISDIR(entry.st_mode):
                    # Diretório: recursão
                    self._walk_directory(full_path, extensions, files)
                elif stat.S_ISREG(entry.st_mode):
                    # Arquivo: verificar extensão
                    if self._matches_extension(entry.filename, extensions):
                        files.append(full_path)
                        
        except Exception:
            pass
    
    def copy_file(
        self, 
        remote_path: str, 
        local_path: str, 
        callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Copia um arquivo do servidor remoto para o local.
        
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
            remote_stat = self._sftp.stat(remote_path)
            total_size = remote_stat.st_size
            
            # Copiar arquivo com callback de progresso
            self._sftp.get(
                remote_path, 
                local_path, 
                callback=lambda transferred, total: callback(transferred, total_size) if callback else None
            )
            
            return True
            
        except Exception as e:
            return False
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Testa a conexão com o servidor SSH.
        
        Returns:
            Tuple com (sucesso, mensagem).
        """
        if not self._config:
            return (False, "Nenhuma configuração fornecida")
        
        try:
            # Tentar listar o diretório base
            path = self._config.get('path', '/')
            self._sftp.listdir(path)
            return (True, "Conexão bem-sucedida")
        except FileNotFoundError:
            return (True, "Conectado, mas diretório não existe")
        except PermissionError:
            return (False, "Permissão negada")
        except Exception as e:
            return (False, f"Erro: {str(e)}")
