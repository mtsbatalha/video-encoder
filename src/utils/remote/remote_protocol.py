"""
Interface base para protocolos remotos.

Este módulo define a interface abstrata que todos os clientes de protocolo
remoto devem implementar.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Callable, Optional, Dict, Any
from pathlib import Path


class RemoteProtocol(ABC):
    """
    Interface base para protocolos remotos.
    
    Todos os clientes de protocolo remoto (SSHFS, SMB, NFS, etc.)
    devem implementar esta interface.
    """
    
    def __init__(self):
        """Inicializa o cliente de protocolo."""
        self._connected = False
        self._config: Optional[Dict[str, Any]] = None
    
    @property
    def is_connected(self) -> bool:
        """Verifica se está conectado."""
        return self._connected
    
    @property
    def config(self) -> Optional[Dict[str, Any]]:
        """Retorna a configuração atual."""
        return self._config
    
    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Conecta ao servidor remoto.
        
        Args:
            config: Configuração da conexão contendo:
                - host: Endereço do servidor
                - port: Porta (opcional, usa padrão se não fornecido)
                - username: Nome de usuário
                - password: Senha (ou None para chave SSH)
                - private_key_path: Caminho da chave privada (opcional)
                - path: Caminho remoto base
                
        Returns:
            True se conectado com sucesso, False caso contrário.
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Desconecta do servidor remoto.
        """
        pass
    
    @abstractmethod
    def list_files(self, path: str, extensions: Optional[List[str]] = None) -> List[str]:
        """
        Lista arquivos em um diretório remoto.
        
        Args:
            path: Caminho do diretório remoto.
            extensions: Lista de extensões para filtrar (opcional).
                       Ex: ['.mp4', '.mkv', '.avi']
                       
        Returns:
            Lista de caminhos completos dos arquivos encontrados.
        """
        pass
    
    @abstractmethod
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
            callback: Função de callback para progresso (bytes_copiados, total_bytes).
                     
        Returns:
            True se copiado com sucesso, False caso contrário.
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """
        Testa a conexão com o servidor remoto.
        
        Returns:
            Tuple com (sucesso, mensagem).
        """
        pass
    
    def _ensure_connected(self) -> bool:
        """
        Verifica se está conectado e lança erro se não estiver.
        
        Returns:
            True se conectado.
            
        Raises:
            ConnectionError: Se não estiver conectado.
        """
        if not self._connected:
            raise ConnectionError("Não está conectado ao servidor remoto")
        return True
    
    def _matches_extension(self, filename: str, extensions: Optional[List[str]]) -> bool:
        """
        Verifica se o arquivo tem uma das extensões especificadas.
        
        Args:
            filename: Nome do arquivo.
            extensions: Lista de extensões para verificar.
            
        Returns:
            True se o arquivo tem uma extensão válida.
        """
        if not extensions:
            return True
        
        filename_lower = filename.lower()
        return any(filename_lower.endswith(ext.lower()) for ext in extensions)
    
    def _ensure_local_directory(self, local_path: str) -> None:
        """
        Garante que o diretório local existe.
        
        Args:
            local_path: Caminho local do arquivo.
        """
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
