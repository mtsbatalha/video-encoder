import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, List
from .config_manager import ConfigManager
from .profile_manager import ProfileManager
from ..utils.path_utils import PathUtils


class RecurrentFolderManager:
    """Gerenciador central para operações de pastas recorrentes."""
    
    def __init__(self, config_manager: ConfigManager, profile_manager: Optional[ProfileManager] = None):
        """
        Inicializa o gerenciador de pastas recorrentes.
        
        Args:
            config_manager: Instância do ConfigManager para persistência
            profile_manager: Instância opcional do ProfileManager para validação de perfis
        """
        self.config_manager = config_manager
        self.profile_manager = profile_manager or ProfileManager()
        self._validate_config_structure()
    
    def _validate_config_structure(self) -> None:
        """Valida e corrige estrutura de configuração se necessário."""
        # Garante que a chave 'recurrent_folders' exista
        if not self.config_manager.get('recurrent_folders'):
            self.config_manager.set('recurrent_folders', [])
            self.config_manager.save()
    
    def _generate_folder_id(self) -> str:
        """Gera um ID único para pasta recorrente."""
        return str(uuid.uuid4())
    
    def _validate_folder_data(self, folder_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Valida os dados da pasta recorrente.
        
        Args:
            folder_data: Dados da pasta a serem validados
            
        Returns:
            Tuple com (valid, error_message)
        """
        # Valida campos obrigatórios
        required_fields = ['name', 'input_directory', 'output_directory', 'profile_id']
        for field in required_fields:
            if field not in folder_data or not folder_data[field]:
                return False, f"Campo obrigatório ausente: {field}"
        
        # Valida caminhos
        input_dir = folder_data['input_directory']
        output_dir = folder_data['output_directory']
        
        # Verifica se caminhos não estão vazios
        if not input_dir or not input_dir.strip():
            return False, "Caminho de entrada vazio"
        
        if not output_dir or not output_dir.strip():
            return False, "Caminho de saída vazio"
        
        # Verifica se diretórios existem
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        if not input_path.exists():
            return False, f"Diretório de entrada não existe: {input_dir}"
        
        if not output_path.exists():
            return False, f"Diretório de saída não existe: {output_dir}"
        
        # Valida se o perfil existe
        profile_id = folder_data['profile_id']
        if self.profile_manager and not self.profile_manager.get_profile(profile_id):
            return False, f"Perfil não encontrado: {profile_id}"
        
        # Valida opções adicionais se presentes
        if 'options' in folder_data and folder_data['options']:
            options = folder_data['options']
            if 'supported_extensions' in options:
                if not isinstance(options['supported_extensions'], list):
                    return False, "supported_extensions deve ser uma lista"
                
                for ext in options['supported_extensions']:
                    if not ext.startswith('.'):
                        return False, f"Extensão inválida: {ext}. Deve começar com '.'"
        
        return True, ""
    
    def add_folder(self, folder_data: Dict[str, Any]) -> str:
        """
        Adiciona uma nova pasta recorrente.
        
        Args:
            folder_data: Dados da pasta a ser adicionada
            
        Returns:
            ID da pasta adicionada ou None se falhar
        """
        # Valida os dados da pasta
        is_valid, error_msg = self._validate_folder_data(folder_data)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Gera ID único se não fornecido
        folder_id = self._generate_folder_id()
        
        # Prepara os dados completos da pasta
        complete_folder_data = {
            'id': folder_id,
            'name': folder_data['name'],
            'input_directory': folder_data['input_directory'],
            'output_directory': folder_data['output_directory'],
            'profile_id': folder_data['profile_id'],
            'enabled': folder_data.get('enabled', True),
            'created_at': datetime.now().isoformat() + 'Z',
            'last_run': folder_data.get('last_run'),
            'total_processed': folder_data.get('total_processed', 0),
            'options': folder_data.get('options', {})
        }
        
        # Adiciona à configuração
        success = self.config_manager.add_recurrent_folder(complete_folder_data)
        if not success:
            raise RuntimeError("Falha ao adicionar pasta recorrente à configuração")
        
        return folder_id
    
    def remove_folder(self, folder_id: str) -> bool:
        """
        Remove uma pasta recorrente.
        
        Args:
            folder_id: ID da pasta a ser removida
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        folders = self.config_manager.get_recurrent_folders()
        
        # Encontra o índice da pasta com o ID especificado
        folder_index = None
        for i, folder in enumerate(folders):
            if folder.get('id') == folder_id:
                folder_index = i
                break
        
        if folder_index is None:
            return False
        
        # Remove a pasta da lista
        folders.pop(folder_index)
        self.config_manager.set('recurrent_folders', folders)
        return self.config_manager.save()
    
    def update_folder(self, folder_id: str, updates: Dict[str, Any]) -> bool:
        """
        Atualiza uma pasta recorrente existente.
        
        Args:
            folder_id: ID da pasta a ser atualizada
            updates: Dados para atualizar
            
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        # Se houver atualizações de caminho ou perfil, valida-os
        folder = self.get_folder(folder_id)
        if not folder:
            return False
        
        # Combina as atualizações com os dados existentes
        updated_folder = {**folder, **updates}
        
        # Valida os dados atualizados
        is_valid, error_msg = self._validate_folder_data(updated_folder)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Atualiza a pasta
        return self.config_manager.update_recurrent_folder(folder_id, updates)
    
    def list_folders(self) -> List[Dict[str, Any]]:
        """
        Lista todas as pastas recorrentes.
        
        Returns:
            Lista de dicionários com dados das pastas
        """
        return self.config_manager.get_recurrent_folders()
    
    def get_folder(self, folder_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém uma pasta específica por ID.
        
        Args:
            folder_id: ID da pasta a ser obtida
            
        Returns:
            Dicionário com dados da pasta ou None se não encontrada
        """
        folders = self.config_manager.get_recurrent_folders()
        for folder in folders:
            if folder.get('id') == folder_id:
                return folder
        return None
    
    def enable_folder(self, folder_id: str) -> bool:
        """
        Habilita uma pasta recorrente.
        
        Args:
            folder_id: ID da pasta a ser habilitada
            
        Returns:
            True se habilitado com sucesso, False caso contrário
        """
        return self.update_folder(folder_id, {'enabled': True})
    
    def disable_folder(self, folder_id: str) -> bool:
        """
        Desabilita uma pasta recorrente.
        
        Args:
            folder_id: ID da pasta a ser desabilitada
            
        Returns:
            True se desabilitado com sucesso, False caso contrário
        """
        return self.update_folder(folder_id, {'enabled': False})
    
    def get_enabled_folders(self) -> List[Dict[str, Any]]:
        """
        Retorna apenas as pastas recorrentes habilitadas.
        
        Returns:
            Lista de pastas habilitadas
        """
        all_folders = self.list_folders()
        return [folder for folder in all_folders if folder.get('enabled', False)]
    
    def get_folder_status(self, folder_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações detalhadas sobre o status de uma pasta.
        
        Args:
            folder_id: ID da pasta
            
        Returns:
            Dicionário com informações de status ou None se não encontrada
        """
        folder = self.get_folder(folder_id)
        if not folder:
            return None
        
        # Aqui poderíamos adicionar informações mais detalhadas sobre o status
        # como número de arquivos processados recentemente, último tempo de execução, etc.
        status_info = {
            'id': folder['id'],
            'name': folder['name'],
            'enabled': folder['enabled'],
            'input_directory': folder['input_directory'],
            'output_directory': folder['output_directory'],
            'profile_id': folder['profile_id'],
            'created_at': folder['created_at'],
            'last_run': folder['last_run'],
            'total_processed': folder['total_processed'],
            'options': folder.get('options', {})
        }
        
        return status_info