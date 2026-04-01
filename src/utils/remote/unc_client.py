"""
Cliente para caminhos UNC Windows.

Este módulo implementa o cliente para acessar caminhos UNC (Universal Naming Convention)
no Windows, como \\\\servidor\\share\\caminho.
"""

import os
import shutil
from pathlib import Path, PureWindowsPath
from typing import List, Tuple, Callable, Optional, Dict, Any

from .remote_protocol import RemoteProtocol


class UNCClient(RemoteProtocol):
    """
    Cliente para caminhos UNC Windows.
    
    Usado para acessar shares de rede Windows via caminho UNC:
    \\\\servidor\\share\\caminho\\arquivo
    """
    
    def __init__(self):
        """Inicializa o cliente UNC."""
        super().__init__()
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Conecta/verifica acesso ao caminho UNC.
        
        Args:
            config: Configuração contendo:
                - host: Nome do servidor (ex: servidor)
                - share: Nome do share (ex: videos)
                - path: Caminho dentro do share
                - username: Nome de usuário (opcional)
                - password: Senha (opcional)
                
        Returns:
            True se o caminho UNC está acessível, False caso contrário.
        """
        try:
            host = config.get('host')
            share = config.get('share')
            
            if not host or not share:
                return False
            
            # Construir caminho UNC
            unc_path = f"\\\\{host}\\{share}"
            
            # Verificar se o caminho existe
            if not os.path.exists(unc_path):
                return False
            
            # Verificar se é um diretório
            if not os.path.isdir(unc_path):
                return False
            
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
        Obtém o caminho UNC base.
        
        Returns:
            Caminho UNC base.
        """
        host = self._config.get('host', '')
        share = self._config.get('share', '')
        path = self._config.get('path', '/')
        
        base = f"\\\\{host}\\{share}"
        
        # Adicionar path se fornecido
        if path and path != '/':
            # Converter path Unix-style para Windows-style
            path = path.lstrip('/').replace('/', '\\')
            return f"{base}\\{path}"
        
        return base
    
    def list_files(self, path: str, extensions: Optional[List[str]] = None) -> List[str]:
        """
        Lista arquivos de vídeo em um diretório UNC.
        
        Args:
            path: Caminho dentro do share.
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
            path = path.lstrip('/').replace('/', '\\')
            full_path = f"{base_path}\\{path}" if path else base_path
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
        Caminha recursivamente por um diretório UNC.
        
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
        Copia um arquivo do caminho UNC para o local.
        
        Args:
            remote_path: Caminho do arquivo UNC.
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
        Testa o acesso ao caminho UNC.
        
        Returns:
            Tuple com (sucesso, mensagem).
        """
        if not self._config:
            return (False, "Nenhuma configuração fornecida")
        
        try:
            unc_path = self._get_base_path()
            
            if not os.path.exists(unc_path):
                return (False, f"Caminho UNC não existe: {unc_path}")
            
            if not os.path.isdir(unc_path):
                return (False, f"Caminho UNC não é um diretório: {unc_path}")
            
            # Testar leitura do diretório
            os.listdir(unc_path)
            
            return (True, "Caminho UNC acessível")
            
        except PermissionError:
            return (False, "Permissão negada")
        except OSError as e:
            if e.winerror == 5:
                return (False, "Acesso negado")
            elif e.winerror == 53:
                return (False, "Caminho de rede não encontrado")
            elif e.winerror == 1231:
                return (False, "Localização de rede não acessível")
            return (False, f"Erro Windows: {e}")
        except Exception as e:
            return (False, f"Erro: {str(e)}")
