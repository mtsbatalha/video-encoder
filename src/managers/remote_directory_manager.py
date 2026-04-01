"""
Gerenciador de diretórios remotos.

Este módulo contém a classe RemoteDirectoryManager que é responsável por
gerenciar a cópia de arquivos de diretórios remotos para um diretório
temporário local antes da conversão.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from ..utils.path_utils import PathUtils, RemoteProtocol
from ..utils.temp_directory_manager import TempDirectoryManager
from ..utils.remote.remote_protocol import RemoteProtocol as RemoteProtocolClient
from ..utils.remote.sshfs_client import SSHFSClient
from ..utils.remote.smb_client import SMBClient
from ..utils.remote.nfs_client import NFSClient
from ..utils.remote.mounted_client import MountedClient
from ..utils.remote.unc_client import UNCClient
from .config_manager import ConfigManager


class CopyStatus(Enum):
    """Status de uma operação de cópia."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CopyProgress:
    """Informações de progresso de cópia."""
    status: CopyStatus = CopyStatus.PENDING
    current_file: str = ""
    current_file_index: int = 0
    total_files: int = 0
    bytes_copied: int = 0
    total_bytes: int = 0
    files_completed: List[str] = field(default_factory=list)
    files_failed: List[str] = field(default_factory=list)
    error_message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def percent_complete(self) -> float:
        """Retorna porcentagem completa baseada em arquivos."""
        if self.total_files == 0:
            return 0.0
        return (len(self.files_completed) / self.total_files) * 100
    
    @property
    def elapsed_seconds(self) -> float:
        """Retorna tempo decorrido em segundos."""
        if not self.started_at:
            return 0.0
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    @property
    def estimated_remaining_seconds(self) -> float:
        """Estima tempo restante em segundos."""
        if self.elapsed_seconds == 0 or len(self.files_completed) == 0:
            return 0.0
        
        avg_seconds_per_file = self.elapsed_seconds / len(self.files_completed)
        remaining_files = self.total_files - len(self.files_completed)
        return avg_seconds_per_file * remaining_files
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'status': self.status.value,
            'current_file': self.current_file,
            'current_file_index': self.current_file_index,
            'total_files': self.total_files,
            'bytes_copied': self.bytes_copied,
            'total_bytes': self.total_bytes,
            'files_completed': self.files_completed,
            'files_failed': self.files_failed,
            'error_message': self.error_message,
            'percent_complete': self.percent_complete,
            'elapsed_seconds': self.elapsed_seconds,
            'estimated_remaining_seconds': self.estimated_remaining_seconds,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class RemoteDirectoryManager:
    """
    Gerenciador central para operações com diretórios remotos.
    
    Esta classe é responsável por:
    - Detectar se um caminho é remoto
    - Identificar o protocolo
    - Criar o cliente apropriado
    - Copiar arquivos para diretório temporário
    """
    
    # Extensões de vídeo suportadas
    VIDEO_EXTENSIONS = [
        '.mp4', '.mkv', '.avi', '.mov', '.wmv',
        '.flv', '.webm', '.m4v', '.mpeg', '.mpg',
        '.ts', '.mts', '.m2ts'
    ]
    
    def __init__(self, config_manager: ConfigManager):
        """
        Inicializa o gerenciador de diretórios remotos.
        
        Args:
            config_manager: Instância do ConfigManager.
        """
        self.config_manager = config_manager
        self.temp_manager = TempDirectoryManager(
            config_manager.get_temp_base()
        )
        self._current_client: Optional[RemoteProtocolClient] = None
        self._copy_progress: Optional[CopyProgress] = None
        self._cancel_requested = False
    
    def is_remote_path(self, path: str) -> bool:
        """
        Verifica se o caminho é um caminho remoto.
        
        Args:
            path: Caminho a ser verificado.
            
        Returns:
            True se o caminho é remoto, False caso contrário.
        """
        return PathUtils.is_remote_path(path)
    
    def get_protocol(self, path: str) -> Optional[RemoteProtocol]:
        """
        Identifica o protocolo do caminho remoto.
        
        Args:
            path: Caminho a ser verificado.
            
        Returns:
            RemoteProtocol ou None se for caminho local.
        """
        return PathUtils.get_protocol(path)
    
    def _create_client(self, protocol: RemoteProtocol) -> Optional[RemoteProtocolClient]:
        """
        Cria o cliente apropriado para o protocolo.
        
        Args:
            protocol: Protocolo remoto.
            
        Returns:
            Instância do cliente ou None se protocolo não suportado.
        """
        if protocol == RemoteProtocol.SSHFS:
            return SSHFSClient()
        elif protocol == RemoteProtocol.SMB:
            return SMBClient()
        elif protocol == RemoteProtocol.NFS:
            return NFSClient()
        elif protocol == RemoteProtocol.MOUNTED:
            return MountedClient()
        elif protocol == RemoteProtocol.UNC:
            return UNCClient()
        
        return None
    
    def _parse_connection_config(self, path: str, connection: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analisa o caminho e cria configuração para o cliente.
        
        Args:
            path: Caminho remoto.
            connection: Configuração de conexão salva (opcional).
            
        Returns:
            Configuração para o cliente.
        """
        parsed = PathUtils.parse_remote_path(path)
        
        if 'error' in parsed:
            return {}
        
        config = {
            'protocol': parsed.get('protocol'),
        }
        
        if parsed['protocol'] == 'sshfs':
            config.update({
                'host': parsed.get('host'),
                'port': parsed.get('port', 22),
                'username': parsed.get('user'),
                'password': connection.get('password') if connection else None,
                'private_key_path': connection.get('private_key_path') if connection else None,
                'path': parsed.get('path', '/')
            })
        
        elif parsed['protocol'] == 'smb':
            config.update({
                'host': parsed.get('host'),
                'share': parsed.get('share'),
                'port': 445,
                'username': connection.get('username') if connection else None,
                'password': connection.get('password') if connection else None,
                'path': parsed.get('path', '/')
            })
        
        elif parsed['protocol'] == 'nfs':
            config.update({
                'host': parsed.get('host'),
                'export': parsed.get('export'),
                'port': 2049,
                'path': parsed.get('path', '/')
            })
        
        elif parsed['protocol'] == 'mounted':
            config.update({
                'mount_point': connection.get('mount_point') if connection else parsed.get('mount_point'),
                'path': parsed.get('path', '/'),
                'mount_type': connection.get('mount_type', 'rclone') if connection else 'rclone'
            })
        
        elif parsed['protocol'] == 'unc':
            config.update({
                'host': parsed.get('host'),
                'share': parsed.get('share'),
                'path': parsed.get('path', '/'),
                'username': connection.get('username') if connection else None,
                'password': connection.get('password') if connection else None
            })
        
        return config
    
    def connect(self, path: str, connection_config: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Conecta ao diretório remoto.
        
        Args:
            path: Caminho remoto.
            connection_config: Configuração de conexão (opcional).
            
        Returns:
            Tuple com (sucesso, mensagem).
        """
        if not self.is_remote_path(path):
            return (False, "Caminho não é remoto")
        
        protocol = self.get_protocol(path)
        if not protocol:
            return (False, "Protocolo não reconhecido")
        
        client = self._create_client(protocol)
        if not client:
            return (False, f"Protocolo não suportado: {protocol}")
        
        config = self._parse_connection_config(path, connection_config)
        if not config:
            return (False, "Não foi possível analisar o caminho")
        
        if client.connect(config):
            self._current_client = client
            return (True, "Conectado com sucesso")
        else:
            return (False, "Falha ao conectar")
    
    def disconnect(self) -> None:
        """Desconecta do diretório remoto."""
        if self._current_client:
            self._current_client.disconnect()
            self._current_client = None
    
    def list_files(self, path: Optional[str] = None) -> List[str]:
        """
        Lista arquivos de vídeo no diretório remoto.
        
        Args:
            path: Caminho específico (opcional, usa path da configuração se não fornecido).
            
        Returns:
            Lista de caminhos dos arquivos de vídeo.
        """
        if not self._current_client:
            return []
        
        parsed = PathUtils.parse_remote_path(path) if path else self._current_client.config
        
        remote_path = parsed.get('path', '/') if isinstance(parsed, dict) else self._current_client.config.get('path', '/')
        
        return self._current_client.list_files(remote_path, self.VIDEO_EXTENSIONS)
    
    def copy_to_temp(
        self, 
        files: List[str], 
        temp_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Tuple[bool, List[str], str]:
        """
        Copia arquivos do diretório remoto para diretório temporário local.
        
        Args:
            files: Lista de caminhos dos arquivos remotos.
            temp_dir: Diretório temporário (cria um novo se None).
            progress_callback: Callback para progresso (arquivo_atual, bytes_copiados, total_bytes).
            
        Returns:
            Tuple com (sucesso, lista_de_arquivos_copiados, mensagem_erro).
        """
        if not self._current_client:
            return (False, [], "Não está conectado")
        
        if not files:
            return (False, [], "Nenhum arquivo para copiar")
        
        # Criar diretório temporário se não fornecido
        if temp_dir is None:
            temp_dir = self.temp_manager.create_temp_directory()
        
        # Verificar espaço em disco
        total_size_estimate = 0  # Não temos como saber o tamanho total antes
        min_disk_space = self.config_manager.get_min_disk_space_gb()
        has_space, available_space = self.temp_manager.check_disk_space(min_disk_space)
        
        if not has_space:
            return (False, [], f"Espaço em disco insuficiente. Disponível: {available_space:.2f} GB, Requerido: {min_disk_space} GB")
        
        copied_files = []
        
        try:
            for i, remote_file in enumerate(files):
                # Gerar caminho local
                file_name = os.path.basename(remote_file)
                local_path = os.path.join(temp_dir, file_name)
                
                # Callback de progresso por arquivo
                def file_progress(copied: int, total: int, file=remote_file):
                    if progress_callback:
                        progress_callback(file, copied, total)
                
                # Copiar arquivo
                success = self._current_client.copy_file(remote_file, local_path, file_progress)
                
                if success:
                    copied_files.append(local_path)
                else:
                    # Falha na cópia - limpar e retornar erro
                    self.temp_manager.cleanup(temp_dir)
                    return (False, copied_files, f"Falha ao copiar arquivo: {remote_file}")
            
            return (True, copied_files, temp_dir)
            
        except Exception as e:
            self.temp_manager.cleanup(temp_dir)
            return (False, [], f"Erro durante cópia: {str(e)}")
    
    def copy_directory_to_temp(
        self,
        remote_path: str,
        connection_config: Optional[Dict] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Tuple[bool, str, List[str]]:
        """
        Copia todo o diretório remoto para temporário local.
        
        Args:
            remote_path: Caminho do diretório remoto.
            connection_config: Configuração de conexão.
            progress_callback: Callback para progresso.
            
        Returns:
            Tuple com (sucesso, caminho_temp, lista_de_arquivos).
        """
        # Conectar
        success, msg = self.connect(remote_path, connection_config)
        if not success:
            return (False, "", msg)
        
        try:
            # Listar arquivos
            files = self.list_files(remote_path)
            
            if not files:
                self.disconnect()
                return (False, "", "Nenhum arquivo de vídeo encontrado")
            
            # Copiar para temp
            success, copied_files, temp_dir = self.copy_to_temp(files, progress_callback=progress_callback)
            
            self.disconnect()
            
            if success:
                return (True, temp_dir, copied_files)
            else:
                return (False, "", copied_files[0] if copied_files else "Erro na cópia")
                
        except Exception as e:
            self.disconnect()
            return (False, "", f"Erro: {str(e)}")
    
    def test_connection(self, path: str, connection_config: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Testa conexão com o diretório remoto.
        
        Args:
            path: Caminho remoto.
            connection_config: Configuração de conexão.
            
        Returns:
            Tuple com (sucesso, mensagem).
        """
        if not self.is_remote_path(path):
            return (False, "Caminho não é remoto")
        
        protocol = self.get_protocol(path)
        if not protocol:
            return (False, "Protocolo não reconhecido")
        
        client = self._create_client(protocol)
        if not client:
            return (False, f"Protocolo não suportado: {protocol}")
        
        config = self._parse_connection_config(path, connection_config)
        if not config:
            return (False, "Não foi possível analisar o caminho")
        
        if client.connect(config):
            success, msg = client.test_connection()
            client.disconnect()
            return (success, msg)
        else:
            return (False, "Falha ao conectar")
    
    def cleanup_temp(self, temp_dir: str) -> bool:
        """
        Limpa diretório temporário.
        
        Args:
            temp_dir: Caminho do diretório temporário.
            
        Returns:
            True se limpo com sucesso, False caso contrário.
        """
        return self.temp_manager.cleanup(temp_dir)
    
    def should_auto_cleanup(self) -> bool:
        """
        Verifica se cleanup automático está habilitado.
        
        Returns:
            True se cleanup automático está habilitado.
        """
        return self.config_manager.get_auto_cleanup()
    
    # Métodos Adicionais para Funcionalidades Avançadas
    
    def get_copy_progress(self) -> Optional[CopyProgress]:
        """
        Retorna progresso atual da cópia.
        
        Returns:
            CopyProgress ou None se não houver cópia em andamento.
        """
        return self._copy_progress
    
    def request_cancel(self) -> None:
        """Solicita cancelamento da operação atual."""
        self._cancel_requested = True
    
    def reset_cancel(self) -> None:
        """Reseta solicitação de cancelamento."""
        self._cancel_requested = False
    
    def get_directory_info(self, remote_path: str, connection_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Obtém informações sobre um diretório remoto.
        
        Args:
            remote_path: Caminho do diretório remoto.
            connection_config: Configuração de conexão.
            
        Returns:
            Dicionário com informações do diretório.
        """
        info = {
            'path': remote_path,
            'is_remote': self.is_remote_path(remote_path),
            'protocol': self.get_protocol(remote_path).value if self.get_protocol(remote_path) else None,
            'accessible': False,
            'file_count': 0,
            'total_size_bytes': 0,
            'video_files': [],
            'error': None
        }
        
        # Testar conexão
        success, msg = self.test_connection(remote_path, connection_config)
        info['accessible'] = success
        
        if not success:
            info['error'] = msg
            return info
        
        # Conectar e listar arquivos
        success, msg = self.connect(remote_path, connection_config)
        if not success:
            info['error'] = msg
            return info
        
        try:
            files = self.list_files(remote_path)
            info['file_count'] = len(files)
            info['video_files'] = files
            
        except Exception as e:
            info['error'] = str(e)
        finally:
            self.disconnect()
        
        return info
    
    def download_single_file(
        self,
        remote_path: str,
        local_path: str,
        connection_config: Optional[Dict] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[bool, str]:
        """
        Baixa um único arquivo remoto.
        
        Args:
            remote_path: Caminho do arquivo remoto.
            local_path: Caminho do arquivo local.
            connection_config: Configuração de conexão.
            progress_callback: Callback de progresso.
            
        Returns:
            Tuple com (sucesso, mensagem).
        """
        # Detectar protocolo do caminho
        protocol = self.get_protocol(remote_path)
        if not protocol:
            return (False, "Protocolo não reconhecido")
        
        client = self._create_client(protocol)
        if not client:
            return (False, f"Protocolo não suportado: {protocol}")
        
        config = self._parse_connection_config(remote_path, connection_config)
        if not config:
            return (False, "Não foi possível analisar o caminho")
        
        if client.connect(config):
            success = client.copy_file(remote_path, local_path, progress_callback)
            client.disconnect()
            
            if success:
                return (True, "Arquivo baixado com sucesso")
            else:
                return (False, "Falha ao baixar arquivo")
        else:
            return (False, "Falha ao conectar")
    
    def get_saved_connection_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Obtém conexão salva por nome.
        
        Args:
            name: Nome da conexão.
            
        Returns:
            Configuração da conexão ou None.
        """
        connections = self.config_manager.get_saved_connections()
        for conn in connections:
            if conn.get('name') == name:
                return conn
        return None
    
    def list_saved_connections(self) -> List[Dict[str, Any]]:
        """
        Lista todas as conexões salvas.
        
        Returns:
            Lista de configurações de conexões.
        """
        return self.config_manager.get_saved_connections()
    
    def add_saved_connection(self, connection: Dict[str, Any]) -> bool:
        """
        Adiciona conexão salva.
        
        Args:
            connection: Configuração da conexão.
            
        Returns:
            True se adicionado com sucesso.
        """
        return self.config_manager.add_saved_connection(connection)
    
    def remove_saved_connection(self, connection_id: str) -> bool:
        """
        Remove conexão salva.
        
        Args:
            connection_id: ID da conexão.
            
        Returns:
            True se removido com sucesso.
        """
        return self.config_manager.remove_saved_connection(connection_id)
