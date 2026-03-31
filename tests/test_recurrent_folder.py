"""
Testes unitários para o RecurrentFolderManager.

Estes testes cobrem:
- Adição de pasta recorrente com configurações válidas
- Edição de pasta recorrente existente
- Remoção de pasta recorrente com confirmação
- Ativar/desativar pasta
- Validação de configurações
- Tratamento de erros (caminhos inválidos, perfil deletado)
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.managers.recurrent_folder_manager import RecurrentFolderManager
from src.managers.config_manager import ConfigManager
from src.managers.profile_manager import ProfileManager


class TestRecurrentFolderManager(unittest.TestCase):
    """Testes unitários para a classe RecurrentFolderManager."""
    
    def setUp(self):
        """Configura o ambiente de teste."""
        # Cria diretório temporário para os testes
        self.test_dir = tempfile.mkdtemp()
        self.config_path = Path(self.test_dir) / "config.json"
        self.profiles_path = Path(self.test_dir) / "profiles"
        self.profiles_path.mkdir()
        
        # Cria configuração de teste
        self.config_manager = ConfigManager(str(self.config_path))
        
        # Cria pastas de teste
        self.input_dir = Path(self.test_dir) / "input"
        self.output_dir = Path(self.test_dir) / "output"
        self.input_dir.mkdir()
        self.output_dir.mkdir()
        
        # Mock do ProfileManager
        self.profile_manager = MagicMock(spec=ProfileManager)
        self.profile_manager.get_profile.return_value = {
            'id': 'test-profile-1',
            'name': 'Test Profile',
            'codec': 'hevc_nvenc'
        }
        
        # Instancia o RecurrentFolderManager
        self.folder_manager = RecurrentFolderManager(
            self.config_manager,
            self.profile_manager
        )
    
    def tearDown(self):
        """Limpa o ambiente de teste."""
        shutil.rmtree(self.test_dir)
    
    def test_01_add_folder_with_valid_config(self):
        """Testa adição de pasta recorrente com configurações válidas."""
        folder_data = {
            'name': 'Test Folder',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
            'enabled': True,
            'options': {
                'supported_extensions': ['.mp4', '.mkv'],
                'skip_existing_output': True
            }
        }
        
        folder_id = self.folder_manager.add_folder(folder_data)
        
        # Verifica se o ID foi gerado
        self.assertIsNotNone(folder_id)
        self.assertIsInstance(folder_id, str)
        
        # Verifica se a pasta foi adicionada
        folders = self.folder_manager.list_folders()
        self.assertEqual(len(folders), 1)
        self.assertEqual(folders[0]['id'], folder_id)
        self.assertEqual(folders[0]['name'], 'Test Folder')
        self.assertEqual(folders[0]['input_directory'], str(self.input_dir))
        self.assertEqual(folders[0]['output_directory'], str(self.output_dir))
        self.assertEqual(folders[0]['profile_id'], 'test-profile-1')
        self.assertTrue(folders[0]['enabled'])
    
    def test_02_add_folder_missing_required_field(self):
        """Testa adição de pasta com campo obrigatório ausente."""
        folder_data = {
            'name': 'Test Folder',
            # input_directory ausente
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1'
        }
        
        with self.assertRaises(ValueError) as context:
            self.folder_manager.add_folder(folder_data)
        
        self.assertIn("Campo obrigatório ausente", str(context.exception))
    
    def test_03_add_folder_invalid_input_path(self):
        """Testa adição de pasta com caminho de entrada inválido."""
        folder_data = {
            'name': 'Test Folder',
            'input_directory': 'C:\\Caminho\\Inexistente\\Pasta',
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1'
        }
        
        with self.assertRaises(ValueError) as context:
            self.folder_manager.add_folder(folder_data)
        
        self.assertIn("Diretório de entrada não existe", str(context.exception))
    
    def test_04_add_folder_invalid_profile(self):
        """Testa adição de pasta com perfil inexistente."""
        self.profile_manager.get_profile.return_value = None
        
        folder_data = {
            'name': 'Test Folder',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'non-existent-profile',
        }
        
        with self.assertRaises(ValueError) as context:
            self.folder_manager.add_folder(folder_data)
        
        self.assertIn("Perfil não encontrado", str(context.exception))
    
    def test_05_add_folder_invalid_extension_format(self):
        """Testa adição de pasta com formato de extensão inválido."""
        folder_data = {
            'name': 'Test Folder',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
            'options': {
                'supported_extensions': ['mp4', '.mkv']  # 'mp4' não começa com '.'
            }
        }
        
        with self.assertRaises(ValueError) as context:
            self.folder_manager.add_folder(folder_data)
        
        self.assertIn("Extensão inválida", str(context.exception))
    
    def test_06_get_folder_by_id(self):
        """Testa obtenção de pasta por ID."""
        folder_data = {
            'name': 'Test Folder',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
        }
        
        folder_id = self.folder_manager.add_folder(folder_data)
        
        # Obtém a pasta por ID
        folder = self.folder_manager.get_folder(folder_id)
        
        self.assertIsNotNone(folder)
        self.assertEqual(folder['id'], folder_id)
        self.assertEqual(folder['name'], 'Test Folder')
    
    def test_07_get_folder_not_found(self):
        """Testa obtenção de pasta com ID inexistente."""
        folder = self.folder_manager.get_folder('non-existent-id')
        self.assertIsNone(folder)
    
    def test_08_update_folder(self):
        """Testa atualização de pasta existente."""
        folder_data = {
            'name': 'Test Folder',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
        }
        
        folder_id = self.folder_manager.add_folder(folder_data)
        
        # Atualiza o nome da pasta
        updates = {'name': 'Updated Folder Name'}
        result = self.folder_manager.update_folder(folder_id, updates)
        
        self.assertTrue(result)
        
        # Verifica se a atualização foi aplicada
        folder = self.folder_manager.get_folder(folder_id)
        self.assertEqual(folder['name'], 'Updated Folder Name')
    
    def test_09_update_folder_invalid_path(self):
        """Testa atualização com caminho inválido."""
        folder_data = {
            'name': 'Test Folder',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
        }
        
        folder_id = self.folder_manager.add_folder(folder_data)
        
        # Tenta atualizar com caminho inválido
        updates = {'input_directory': 'C:\\Caminho\\Inexistente'}
        
        with self.assertRaises(ValueError) as context:
            self.folder_manager.update_folder(folder_id, updates)
        
        self.assertIn("Diretório de entrada não existe", str(context.exception))
    
    def test_10_enable_disable_folder(self):
        """Testa ativar/desativar pasta."""
        folder_data = {
            'name': 'Test Folder',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
        }
        
        folder_id = self.folder_manager.add_folder(folder_data)
        
        # Desabilita a pasta
        result = self.folder_manager.disable_folder(folder_id)
        self.assertTrue(result)
        
        folder = self.folder_manager.get_folder(folder_id)
        self.assertFalse(folder['enabled'])
        
        # Habilita a pasta novamente
        result = self.folder_manager.enable_folder(folder_id)
        self.assertTrue(result)
        
        folder = self.folder_manager.get_folder(folder_id)
        self.assertTrue(folder['enabled'])
    
    def test_11_get_enabled_folders(self):
        """Testa obtenção apenas de pastas habilitadas."""
        # Adiciona duas pastas
        folder_data_1 = {
            'name': 'Enabled Folder',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
            'enabled': True
        }
        
        folder_data_2 = {
            'name': 'Disabled Folder',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
            'enabled': False
        }
        
        self.folder_manager.add_folder(folder_data_1)
        self.folder_manager.add_folder(folder_data_2)
        
        # Obtém apenas pastas habilitadas
        enabled_folders = self.folder_manager.get_enabled_folders()
        
        self.assertEqual(len(enabled_folders), 1)
        self.assertEqual(enabled_folders[0]['name'], 'Enabled Folder')
    
    def test_12_remove_folder(self):
        """Testa remoção de pasta recorrente."""
        folder_data = {
            'name': 'Test Folder',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
        }
        
        folder_id = self.folder_manager.add_folder(folder_data)
        
        # Remove a pasta
        result = self.folder_manager.remove_folder(folder_id)
        self.assertTrue(result)
        
        # Verifica se a pasta foi removida
        folders = self.folder_manager.list_folders()
        self.assertEqual(len(folders), 0)
        
        # Tenta remover novamente (deve falhar)
        result = self.folder_manager.remove_folder(folder_id)
        self.assertFalse(result)
    
    def test_13_remove_nonexistent_folder(self):
        """Testa remoção de pasta inexistente."""
        result = self.folder_manager.remove_folder('non-existent-id')
        self.assertFalse(result)
    
    def test_14_get_folder_status(self):
        """Testa obtenção de status detalhado da pasta."""
        folder_data = {
            'name': 'Test Folder',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
            'options': {
                'skip_existing_output': True
            }
        }
        
        folder_id = self.folder_manager.add_folder(folder_data)
        
        # Obtém o status
        status = self.folder_manager.get_folder_status(folder_id)
        
        self.assertIsNotNone(status)
        self.assertEqual(status['id'], folder_id)
        self.assertEqual(status['name'], 'Test Folder')
        self.assertEqual(status['enabled'], True)
        self.assertIn('options', status)
    
    def test_15_persistence_after_restart(self):
        """Testa persistência de configurações após 'restart' (nova instância)."""
        folder_data = {
            'name': 'Persistent Folder',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
        }
        
        folder_id = self.folder_manager.add_folder(folder_data)
        
        # Cria nova instância do manager (simula restart)
        new_config_manager = ConfigManager(str(self.config_path))
        new_folder_manager = RecurrentFolderManager(new_config_manager, self.profile_manager)
        
        # Verifica se a pasta persistiu
        folders = new_folder_manager.list_folders()
        self.assertEqual(len(folders), 1)
        self.assertEqual(folders[0]['id'], folder_id)
        self.assertEqual(folders[0]['name'], 'Persistent Folder')
    
    def test_16_multiple_folders(self):
        """Testa adição de múltiplas pastas."""
        for i in range(5):
            folder_data = {
                'name': f'Test Folder {i}',
                'input_directory': str(self.input_dir),
                'output_directory': str(self.output_dir),
                'profile_id': 'test-profile-1',
            }
            self.folder_manager.add_folder(folder_data)
        
        folders = self.folder_manager.list_folders()
        self.assertEqual(len(folders), 5)
        
        # Verifica nomes únicos
        names = [f['name'] for f in folders]
        self.assertEqual(len(set(names)), 5)  # Todos únicos
    
    def test_17_folder_id_uniqueness(self):
        """Testa se IDs gerados são únicos."""
        folder_ids = []
        for i in range(10):
            folder_data = {
                'name': f'Folder {i}',
                'input_directory': str(self.input_dir),
                'output_directory': str(self.output_dir),
                'profile_id': 'test-profile-1',
            }
            folder_id = self.folder_manager.add_folder(folder_data)
            folder_ids.append(folder_id)
        
        # Verifica se todos os IDs são únicos
        self.assertEqual(len(set(folder_ids)), len(folder_ids))


class TestRecurrentFolderManagerEdgeCases(unittest.TestCase):
    """Testes de casos extremos e borda."""
    
    def setUp(self):
        """Configura o ambiente de teste."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = Path(self.test_dir) / "config.json"
        self.profiles_path = Path(self.test_dir) / "profiles"
        self.profiles_path.mkdir()
        
        self.config_manager = ConfigManager(str(self.config_path))
        
        self.input_dir = Path(self.test_dir) / "input"
        self.output_dir = Path(self.test_dir) / "output"
        self.input_dir.mkdir()
        self.output_dir.mkdir()
        
        self.profile_manager = MagicMock(spec=ProfileManager)
        self.profile_manager.get_profile.return_value = {
            'id': 'test-profile-1',
            'name': 'Test Profile',
            'codec': 'hevc_nvenc'
        }
        
        self.folder_manager = RecurrentFolderManager(
            self.config_manager,
            self.profile_manager
        )
    
    def tearDown(self):
        """Limpa o ambiente de teste."""
        shutil.rmtree(self.test_dir)
    
    def test_edge_case_empty_name(self):
        """Testa adição de pasta com nome vazio."""
        folder_data = {
            'name': '',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
        }
        
        # Nome vazio deve levantar erro (campo obrigatório)
        with self.assertRaises(ValueError) as context:
            self.folder_manager.add_folder(folder_data)
        
        self.assertIn("Campo obrigatório ausente: name", str(context.exception))
    
    def test_edge_case_special_characters_in_name(self):
        """Testa adição de pasta com caracteres especiais no nome."""
        folder_data = {
            'name': 'Pasta @#$%&* Teste',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
        }
        
        folder_id = self.folder_manager.add_folder(folder_data)
        self.assertIsNotNone(folder_id)
        
        folder = self.folder_manager.get_folder(folder_id)
        self.assertEqual(folder['name'], 'Pasta @#$%&* Teste')
    
    def test_edge_case_unicode_characters(self):
        """Testa adição de pasta com caracteres Unicode."""
        folder_data = {
            'name': 'Pasta 日本語 📁',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
        }
        
        folder_id = self.folder_manager.add_folder(folder_data)
        self.assertIsNotNone(folder_id)
        
        folder = self.folder_manager.get_folder(folder_id)
        self.assertEqual(folder['name'], 'Pasta 日本語 📁')
    
    def test_edge_case_very_long_path(self):
        """Testa adição de pasta com caminho muito longo."""
        # Cria caminho profundo
        deep_dir = self.input_dir
        for i in range(10):
            deep_dir = deep_dir / f"subdir_{i}"
        deep_dir.mkdir(parents=True)
        
        folder_data = {
            'name': 'Deep Folder',
            'input_directory': str(deep_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
        }
        
        folder_id = self.folder_manager.add_folder(folder_data)
        self.assertIsNotNone(folder_id)
    
    def test_edge_case_same_input_output(self):
        """Testa adição de pasta com input e output iguais."""
        folder_data = {
            'name': 'Same IO Folder',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.input_dir),  # Mesmo que input
            'profile_id': 'test-profile-1',
        }
        
        # Deve permitir (embora não seja recomendado)
        folder_id = self.folder_manager.add_folder(folder_data)
        self.assertIsNotNone(folder_id)
    
    def test_edge_case_options_null(self):
        """Testa adição de pasta com options null."""
        folder_data = {
            'name': 'Test Folder',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'profile_id': 'test-profile-1',
            'options': None
        }
        
        folder_id = self.folder_manager.add_folder(folder_data)
        self.assertIsNotNone(folder_id)
        
        folder = self.folder_manager.get_folder(folder_id)
        self.assertEqual(folder.get('options'), None)
    
    def test_edge_case_update_nonexistent_folder(self):
        """Testa atualização de pasta inexistente."""
        updates = {'name': 'New Name'}
        result = self.folder_manager.update_folder('non-existent-id', updates)
        self.assertFalse(result)
    
    def test_edge_case_enable_disable_nonexistent_folder(self):
        """Testa ativar/desativar pasta inexistente."""
        result = self.folder_manager.enable_folder('non-existent-id')
        self.assertFalse(result)
        
        result = self.folder_manager.disable_folder('non-existent-id')
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
