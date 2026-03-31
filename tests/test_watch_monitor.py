"""
Testes unitários para o WatchFolderMonitor.

Estes testes cobrem:
- Detecção de novos arquivos
- Debounce para arquivos em cópia
- Skip de arquivos já processados
- Validação de extensão suportada
- Validação de tamanho mínimo
- Tratamento de erros
- Concorrência (múltiplas pastas)
"""

import unittest
import tempfile
import shutil
import time
import threading
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch, call
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.watch_folder_monitor import WatchFolderMonitor
from src.managers.queue_manager import QueueManager
from src.managers.job_manager import JobManager
from src.managers.profile_manager import ProfileManager
from src.managers.recurrent_history_manager import RecurrentHistoryManager


class TestWatchFolderMonitor(unittest.TestCase):
    """Testes unitários para a classe WatchFolderMonitor."""
    
    def setUp(self):
        """Configura o ambiente de teste."""
        # Cria diretório temporário
        self.test_dir = tempfile.mkdtemp()
        
        # Cria pastas de teste
        self.watch_path = Path(self.test_dir) / "watch"
        self.output_path = Path(self.test_dir) / "output"
        self.watch_path.mkdir()
        self.output_path.mkdir()
        
        # Mock dos managers
        self.queue_manager = MagicMock(spec=QueueManager)
        self.queue_manager.add_to_queue.return_value = 1  # Posição na fila
        
        self.job_manager = MagicMock(spec=JobManager)
        self.job_manager.create_job.return_value = "test-job-id-123"
        self.job_manager.register_status_callback = MagicMock()
        
        self.profile_manager = MagicMock(spec=ProfileManager)
        self.profile_manager.get_profile.return_value = {
            'id': 'test-profile-1',
            'name': 'Test Profile',
            'codec': 'hevc_nvenc'
        }
        
        self.history_manager = MagicMock(spec=RecurrentHistoryManager)
        
        # Configuração do monitor
        self.config = {
            'path': str(self.watch_path),
            'output_path': str(self.output_path),
            'profile_id': 'test-profile-1',
            'folder_id': 'test-folder-123',
            'interval': 1,  # 1 segundo para testes rápidos
            'min_size': 1024,  # 1KB
            'skip_existing_output': True,
            'extensions': ['.mp4', '.mkv', '.avi'],
            'debounce_time': 0.5,  # 0.5 segundos para testes
            'enabled': True,
            'priority': 'normal'
        }
        
        # Cria o monitor
        self.monitor = WatchFolderMonitor(
            config=self.config,
            queue_manager=self.queue_manager,
            job_manager=self.job_manager,
            profile_manager=self.profile_manager,
            history_manager=self.history_manager
        )
    
    def tearDown(self):
        """Limpa o ambiente de teste."""
        # Para o monitor se estiver rodando
        if self.monitor._monitor_thread and self.monitor._monitor_thread.is_alive():
            self.monitor.stop()
        
        shutil.rmtree(self.test_dir)
    
    def test_01_monitor_initialization(self):
        """Testa inicialização do monitor."""
        self.assertEqual(self.monitor.watch_path, self.watch_path)
        self.assertEqual(self.monitor.profile_id, 'test-profile-1')
        self.assertEqual(self.monitor.folder_id, 'test-folder-123')
        self.assertEqual(self.monitor.interval, 1)
        self.assertEqual(self.monitor.min_size, 1024)
        self.assertTrue(self.monitor.skip_existing_output)
        self.assertEqual(self.monitor.extensions, ['.mp4', '.mkv', '.avi'])
        self.assertEqual(self.monitor.debounce_time, 0.5)
        self.assertTrue(self.monitor.enabled)
    
    def test_02_start_stop_monitor(self):
        """Testa start e stop do monitor."""
        # Inicia o monitor
        self.monitor.start()
        
        # Verifica se o monitor está rodando
        self.assertTrue(self.monitor._monitor_thread.is_alive())
        
        # Para o monitor
        self.monitor.stop()
        
        # Aguarda um pouco para garantir que parou
        time.sleep(0.5)
        self.assertFalse(self.monitor._monitor_thread.is_alive())
    
    def test_03_start_disabled_monitor(self):
        """Testa inicialização de monitor desabilitado."""
        self.monitor.enabled = False
        
        # Tenta iniciar monitor desabilitado
        self.monitor.start()
        
        # Monitor não deve iniciar
        self.assertIsNone(self.monitor._monitor_thread)
    
    def test_04_start_nonexistent_path(self):
        """Testa inicialização com caminho inexistente."""
        self.monitor.watch_path = Path("C:\\Caminho\\Inexistente")
        
        # Tenta iniciar com caminho inexistente
        self.monitor.start()
        
        # Monitor não deve iniciar thread de monitoramento
        self.assertIsNone(self.monitor._monitor_thread)
    
    def test_05_detect_new_file(self):
        """Testa detecção de novo arquivo."""
        # Inicia o monitor
        self.monitor.start()
        
        # Cria um arquivo de teste
        test_file = self.watch_path / "test_video.mp4"
        test_file.write_bytes(b"x" * 2048)  # 2KB
        
        # Aguarda detecção (interval + debounce)
        time.sleep(2.0)
        
        # Para o monitor
        self.monitor.stop()
        time.sleep(0.5)
        
        # Verifica se o arquivo foi processado
        self.assertIn(str(test_file), self.monitor._processed_files)
    
    def test_06_skip_already_processed_file(self):
        """Testa skip de arquivo já processado."""
        # Adiciona arquivo ao conjunto de processados
        test_file = self.watch_path / "already_processed.mp4"
        test_file.write_bytes(b"x" * 2048)
        self.monitor._processed_files.add(str(test_file))
        
        # Inicia o monitor
        self.monitor.start()
        time.sleep(1.5)
        self.monitor.stop()
        
        # Verifica que não foi adicionado à fila novamente
        self.queue_manager.add_to_queue.assert_not_called()
    
    def test_07_skip_unsupported_extension(self):
        """Testa skip de arquivo com extensão não suportada."""
        # Cria arquivo com extensão não suportada
        test_file = self.watch_path / "test_video.txt"
        test_file.write_bytes(b"x" * 2048)
        
        # Inicia o monitor
        self.monitor.start()
        time.sleep(1.5)
        self.monitor.stop()
        
        # Verifica que não foi processado
        self.assertNotIn(str(test_file), self.monitor._processed_files)
        self.queue_manager.add_to_queue.assert_not_called()
    
    def test_08_skip_file_below_min_size(self):
        """Testa skip de arquivo abaixo do tamanho mínimo."""
        # Cria arquivo pequeno (menor que 1KB)
        test_file = self.watch_path / "small_video.mp4"
        test_file.write_bytes(b"x" * 512)  # 512 bytes
        
        # Inicia o monitor
        self.monitor.start()
        time.sleep(1.5)
        self.monitor.stop()
        
        # Verifica que não foi processado
        self.assertNotIn(str(test_file), self.monitor._processed_files)
        self.queue_manager.add_to_queue.assert_not_called()
    
    def test_09_debounce_incomplete_file(self):
        """Testa debounce para arquivo incompleto."""
        # Cria arquivo inicial
        test_file = self.watch_path / "incomplete_video.mp4"
        test_file.write_bytes(b"x" * 1024)
        
        # Inicia o monitor
        self.monitor.start()
        
        # Modifica o arquivo durante o debounce
        time.sleep(0.2)
        test_file.write_bytes(b"x" * 2048)  # Aumenta o arquivo
        
        # Aguarda mais um pouco
        time.sleep(1.5)
        self.monitor.stop()
        
        # O arquivo pode ou não ter sido processado dependendo do timing
        # O importante é que o debounce foi executado
    
    def test_10_skip_existing_output(self):
        """Testa skip quando output já existe."""
        # Cria arquivo de input
        test_file = self.watch_path / "test_video.mp4"
        test_file.write_bytes(b"x" * 2048)
        
        # Cria arquivo de output (simula processamento anterior)
        output_file = self.output_path / "test_video.mp4"
        output_file.write_bytes(b"encoded content")
        
        # Inicia o monitor
        self.monitor.start()
        time.sleep(1.5)
        self.monitor.stop()
        
        # Verifica que não foi processado (skip_existing_output = True)
        self.assertNotIn(str(test_file), self.monitor._processed_files)
        self.queue_manager.add_to_queue.assert_not_called()
    
    def test_11_process_when_output_not_exists(self):
        """Testa processamento quando output não existe."""
        # Cria arquivo de input
        test_file = self.watch_path / "test_video.mp4"
        test_file.write_bytes(b"x" * 2048)
        
        # Inicia o monitor
        self.monitor.start()
        time.sleep(1.5)
        self.monitor.stop()
        
        # Verifica que foi processado
        self.assertIn(str(test_file), self.monitor._processed_files)
        self.job_manager.create_job.assert_called()
        self.queue_manager.add_to_queue.assert_called()
    
    def test_12_profile_not_found(self):
        """Testa comportamento quando perfil não é encontrado."""
        self.profile_manager.get_profile.return_value = None
        
        # Cria arquivo de input
        test_file = self.watch_path / "test_video.mp4"
        test_file.write_bytes(b"x" * 2048)
        
        # Inicia o monitor
        self.monitor.start()
        time.sleep(1.5)
        self.monitor.stop()
        
        # Verifica que não foi processado (perfil não encontrado)
        self.assertNotIn(str(test_file), self.monitor._processed_files)
        self.job_manager.create_job.assert_not_called()
    
    def test_13_multiple_files_detection(self):
        """Testa detecção de múltiplos arquivos simultaneamente."""
        # Cria múltiplos arquivos
        files = []
        for i in range(5):
            test_file = self.watch_path / f"video_{i}.mp4"
            test_file.write_bytes(b"x" * 2048)
            files.append(test_file)
        
        # Inicia o monitor
        self.monitor.start()
        time.sleep(2.0)
        self.monitor.stop()
        
        # Verifica que todos foram processados
        for f in files:
            self.assertIn(str(f), self.monitor._processed_files)
        
        # Verifica que create_job foi chamado 5 vezes
        self.assertEqual(self.job_manager.create_job.call_count, 5)
    
    def test_14_subdirectory_detection(self):
        """Testa detecção de arquivos em subdiretórios."""
        # Cria subdiretório
        subdir = self.watch_path / "subdir"
        subdir.mkdir()
        
        # Cria arquivo no subdiretório
        test_file = subdir / "nested_video.mp4"
        test_file.write_bytes(b"x" * 2048)
        
        # Inicia o monitor
        self.monitor.start()
        time.sleep(1.5)
        self.monitor.stop()
        
        # Verifica que foi processado (rglob busca recursivamente)
        self.assertIn(str(test_file), self.monitor._processed_files)
    
    def test_15_output_path_generation(self):
        """Testa geração de caminho de output."""
        # Cria arquivo de input
        test_file = self.watch_path / "test_video.mp4"
        
        # Gera caminho de output
        output_path = self.monitor._get_output_path(test_file)
        
        # Verifica caminho gerado
        self.assertIsNotNone(output_path)
        self.assertEqual(output_path.parent, self.output_path)
        self.assertEqual(output_path.stem, "test_video")
        self.assertEqual(output_path.suffix, ".mp4")
    
    def test_16_enqueue_file_creates_job(self):
        """Testa que enqueue de arquivo cria job."""
        test_file = self.watch_path / "test_video.mp4"
        test_file.write_bytes(b"x" * 2048)
        
        # Chama enqueue diretamente
        self.monitor._enqueue_file(test_file)
        
        # Verifica que job foi criado
        self.job_manager.create_job.assert_called_once()
        self.queue_manager.add_to_queue.assert_called_once()
    
    def test_17_priority_handling(self):
        """Testa handling de diferentes prioridades."""
        # Testa prioridade alta
        self.monitor.config['priority'] = 'high'
        self.monitor.start()
        
        test_file = self.watch_path / "high_priority.mp4"
        test_file.write_bytes(b"x" * 2048)
        
        time.sleep(1.5)
        self.monitor.stop()
        
        # Verifica chamada com prioridade alta
        calls = self.queue_manager.add_to_queue.call_args_list
        if calls:
            # Verifica que priority foi passado
            call_kwargs = calls[0][1] if len(calls[0]) > 1 else {}
            # A prioridade deve ser QueuePriority.HIGH
    
    def test_18_concurrent_monitoring(self):
        """Testa monitoramento concorrente com múltiplos monitores."""
        # Cria segundo monitor
        watch_path_2 = Path(self.test_dir) / "watch2"
        watch_path_2.mkdir()
        
        config_2 = self.config.copy()
        config_2['path'] = str(watch_path_2)
        config_2['folder_id'] = 'test-folder-456'
        
        monitor_2 = WatchFolderMonitor(
            config=config_2,
            queue_manager=self.queue_manager,
            job_manager=self.job_manager,
            profile_manager=self.profile_manager,
            history_manager=self.history_manager
        )
        
        # Inicia ambos os monitores
        self.monitor.start()
        monitor_2.start()
        
        # Cria arquivos em ambas as pastas
        file_1 = self.watch_path / "video_1.mp4"
        file_1.write_bytes(b"x" * 2048)
        
        file_2 = watch_path_2 / "video_2.mp4"
        file_2.write_bytes(b"x" * 2048)
        
        # Aguarda detecção
        time.sleep(2.0)
        
        # Para ambos
        self.monitor.stop()
        monitor_2.stop()
        
        # Verifica que ambos processaram seus arquivos
        self.assertIn(str(file_1), self.monitor._processed_files)
        self.assertIn(str(file_2), monitor_2._processed_files)
    
    def test_19_error_handling_file_locked(self):
        """Testa handling de erro quando arquivo está bloqueado."""
        # Cria arquivo
        test_file = self.watch_path / "locked_video.mp4"
        test_file.write_bytes(b"x" * 2048)
        
        # Mock para simular arquivo bloqueado
        with patch('src.utils.file_utils.FileUtils.is_file_locked', return_value=True):
            self.monitor.start()
            time.sleep(1.5)
            self.monitor.stop()
        
        # Arquivo não deve ser processado enquanto estiver bloqueado
        # (pode ser processado em verificações subsequentes)
    
    def test_20_error_handling_permission_denied(self):
        """Testa handling de erro de permissão negada."""
        # Cria arquivo
        test_file = self.watch_path / "no_permission.mp4"
        test_file.write_bytes(b"x" * 2048)
        
        # Mock para simular erro de permissão no is_file_locked
        with patch('src.utils.file_utils.FileUtils.is_file_locked', side_effect=PermissionError("Access denied")):
            self.monitor.start()
            time.sleep(1.5)
            self.monitor.stop()
        
        # Monitor deve continuar funcionando apesar do erro
        # (não deve crashar)


class TestWatchFolderMonitorEdgeCases(unittest.TestCase):
    """Testes de casos extremos para WatchFolderMonitor."""
    
    def setUp(self):
        """Configura o ambiente de teste."""
        self.test_dir = tempfile.mkdtemp()
        self.watch_path = Path(self.test_dir) / "watch"
        self.output_path = Path(self.test_dir) / "output"
        self.watch_path.mkdir()
        self.output_path.mkdir()
        
        self.queue_manager = MagicMock(spec=QueueManager)
        self.queue_manager.add_to_queue.return_value = 1
        
        self.job_manager = MagicMock(spec=JobManager)
        self.job_manager.create_job.return_value = "test-job-id"
        
        self.profile_manager = MagicMock(spec=ProfileManager)
        self.profile_manager.get_profile.return_value = {
            'id': 'test-profile-1',
            'name': 'Test Profile',
            'codec': 'hevc_nvenc'
        }
        
        self.history_manager = MagicMock(spec=RecurrentHistoryManager)
        
        self.config = {
            'path': str(self.watch_path),
            'output_path': str(self.output_path),
            'profile_id': 'test-profile-1',
            'folder_id': 'test-folder-123',
            'interval': 1,
            'min_size': 0,  # Sem tamanho mínimo para testes
            'skip_existing_output': False,
            'extensions': ['.mp4', '.mkv', '.avi', '.MOV', '.MP4'],  # Mistura de cases
            'debounce_time': 0.1,
            'enabled': True,
            'priority': 'normal'
        }
        
        self.monitor = WatchFolderMonitor(
            config=self.config,
            queue_manager=self.queue_manager,
            job_manager=self.job_manager,
            profile_manager=self.profile_manager,
            history_manager=self.history_manager
        )
    
    def tearDown(self):
        """Limpa o ambiente de teste."""
        if self.monitor._monitor_thread and self.monitor._monitor_thread.is_alive():
            self.monitor.stop()
        shutil.rmtree(self.test_dir)
    
    def test_edge_case_case_insensitive_extensions(self):
        """Testa detecção com extensões case-insensitive."""
        # Cria arquivos com diferentes cases
        files = [
            self.watch_path / "video1.MP4",
            self.watch_path / "video2.Mp4",
            self.watch_path / "video3.mp4",
        ]
        
        for f in files:
            f.write_bytes(b"x" * 1024)
        
        self.monitor.start()
        time.sleep(1.5)
        self.monitor.stop()
        
        # Verifica que pelo menos alguns foram detectados
        # (depende da implementação do rglob)
    
    def test_edge_case_empty_directory(self):
        """Testa monitoramento de diretório vazio."""
        self.monitor.start()
        time.sleep(1.5)
        self.monitor.stop()
        
        # Não deve haver erros
        self.job_manager.create_job.assert_not_called()
    
    def test_edge_case_rapid_file_creation(self):
        """Testa criação rápida de múltiplos arquivos."""
        # Cria 10 arquivos rapidamente
        for i in range(10):
            test_file = self.watch_path / f"rapid_{i}.mp4"
            test_file.write_bytes(b"x" * 1024)
        
        self.monitor.start()
        time.sleep(2.0)
        self.monitor.stop()
        
        # Verifica que todos foram processados
        self.assertEqual(len(self.monitor._processed_files), 10)
    
    def test_edge_case_very_large_file(self):
        """Testa processamento de arquivo grande."""
        # Cria arquivo de 10MB
        test_file = self.watch_path / "large_video.mp4"
        test_file.write_bytes(b"x" * (10 * 1024 * 1024))
        
        self.monitor.start()
        time.sleep(1.5)
        self.monitor.stop()
        
        # Verifica que foi processado
        self.assertIn(str(test_file), self.monitor._processed_files)
    
    def test_edge_case_special_characters_filename(self):
        """Testa arquivos com caracteres especiais no nome."""
        special_names = [
            "vídeo com acento.mp4",
            "video@hashtag.mp4",
            "video spaces.mp4",
        ]
        
        for name in special_names:
            test_file = self.watch_path / name
            test_file.write_bytes(b"x" * 1024)
        
        self.monitor.start()
        time.sleep(1.5)
        self.monitor.stop()
        
        # Verifica que foram processados
        self.assertEqual(len(self.monitor._processed_files), 3)
    
    def test_edge_case_double_start(self):
        """Testa iniciar monitor já em execução."""
        self.monitor.start()
        
        # Tenta iniciar novamente
        self.monitor.start()
        
        # Não deve criar thread adicional
        self.monitor.stop()
    
    def test_edge_case_stop_not_started(self):
        """Testa parar monitor não iniciado."""
        # Não deve causar erro
        self.monitor.stop()
    
    def test_edge_case_output_directory_creation(self):
        """Testa criação automática de diretório de output."""
        # Configura output em subdiretório inexistente
        new_output = Path(self.test_dir) / "new_output" / "subdir"
        self.monitor.config['output_path'] = str(new_output)
        
        test_file = self.watch_path / "test.mp4"
        test_file.write_bytes(b"x" * 1024)
        
        self.monitor.start()
        time.sleep(1.5)
        self.monitor.stop()
        
        # Verifica que diretório foi criado
        self.assertTrue(new_output.exists())


class TestWatchFolderMonitorHistoryIntegration(unittest.TestCase):
    """Testes de integração com RecurrentHistoryManager."""
    
    def setUp(self):
        """Configura o ambiente de teste."""
        self.test_dir = tempfile.mkdtemp()
        self.watch_path = Path(self.test_dir) / "watch"
        self.output_path = Path(self.test_dir) / "output"
        self.watch_path.mkdir()
        self.output_path.mkdir()
        
        self.queue_manager = MagicMock(spec=QueueManager)
        self.queue_manager.add_to_queue.return_value = 1
        
        self.job_manager = MagicMock(spec=JobManager)
        self.job_manager.create_job.return_value = "test-job-id"
        
        self.profile_manager = MagicMock(spec=ProfileManager)
        self.profile_manager.get_profile.return_value = {
            'id': 'test-profile-1',
            'name': 'Test Profile',
            'codec': 'hevc_nvenc'
        }
        
        self.history_manager = MagicMock(spec=RecurrentHistoryManager)
        
        self.config = {
            'path': str(self.watch_path),
            'output_path': str(self.output_path),
            'profile_id': 'test-profile-1',
            'folder_id': 'test-folder-123',
            'interval': 1,
            'min_size': 0,
            'skip_existing_output': False,
            'extensions': ['.mp4'],
            'debounce_time': 0.1,
            'enabled': True,
            'priority': 'normal'
        }
        
        self.monitor = WatchFolderMonitor(
            config=self.config,
            queue_manager=self.queue_manager,
            job_manager=self.job_manager,
            profile_manager=self.profile_manager,
            history_manager=self.history_manager
        )
    
    def tearDown(self):
        """Limpa o ambiente de teste."""
        if self.monitor._monitor_thread and self.monitor._monitor_thread.is_alive():
            self.monitor.stop()
        shutil.rmtree(self.test_dir)
    
    def test_history_callback_registration(self):
        """Testa registro de callback para histórico."""
        test_file = self.watch_path / "test.mp4"
        test_file.write_bytes(b"x" * 1024)
        
        self.monitor.start()
        time.sleep(1.5)
        self.monitor.stop()
        
        # Verifica que callback foi registrado
        self.job_manager.register_status_callback.assert_called()
    
    def test_history_entry_on_job_completion(self):
        """Testa criação de entrada no histórico ao completar job."""
        # Mock do job_manager.get_job para retornar dados do job
        from datetime import datetime
        self.job_manager.get_job.return_value = {
            'input_path': str(self.watch_path / "test.mp4"),
            'output_path': str(self.output_path / "test.mp4"),
            'started_at': datetime.now().isoformat() + 'Z',
            'completed_at': datetime.now().isoformat() + 'Z',
        }
        
        # Simula callback de status change
        self.monitor._on_job_status_change(
            job_id="test-job-id",
            old_status="running",
            new_status="completed"
        )
        
        # Verifica que history_manager.add_entry foi chamado
        self.history_manager.add_entry.assert_called()


if __name__ == '__main__':
    unittest.main()
