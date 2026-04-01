"""
Serviço de monitoramento recorrente para gerenciar todos os monitores ativos.

Este módulo contém a classe RecurrentMonitorService que é responsável por
gerenciar todos os monitores de pastas ativos conforme especificado no plano de implementação.
"""

import asyncio
import logging
import threading
import time
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from src.core.watch_folder_monitor import WatchFolderMonitor
from src.managers.config_manager import ConfigManager
from src.managers.queue_manager import QueueManager
from src.managers.job_manager import JobManager
from src.managers.profile_manager import ProfileManager
from src.managers.recurrent_history_manager import RecurrentHistoryManager


class RecurrentMonitorService:
    """
    Serviço que gerencia todos os monitores de pasta ativos.

    Esta classe é responsável por iniciar, parar e monitorar todos os monitores
    de pasta configurados no sistema.
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        queue_manager: QueueManager,
        job_manager: JobManager,
        profile_manager: ProfileManager,
        history_manager: Optional[RecurrentHistoryManager] = None,
        encoder: Optional[Any] = None,
    ):
        """
        Inicializa o serviço de monitoramento recorrente.

        Args:
            config_manager: Gerenciador de configurações
            queue_manager: Gerenciador de filas
            job_manager: Gerenciador de jobs
            profile_manager: Gerenciador de perfis
            history_manager: Gerenciador de histórico (opcional)
            encoder: Encoder engine to process jobs from queue
        """
        self.config_manager = config_manager
        self.queue_manager = queue_manager
        self.job_manager = job_manager
        self.profile_manager = profile_manager
        self.history_manager = history_manager or RecurrentHistoryManager()
        self.encoder = encoder
        self.monitors: Dict[str, WatchFolderMonitor] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.logger = logging.getLogger(__name__)
        self._queue_processor_thread: Optional[threading.Thread] = None
        self._queue_processor_running = False

    def start_all_monitors(self) -> Dict[str, WatchFolderMonitor]:
        """
        Lê as configurações e inicia todos os monitores de pasta configurados.

        Returns:
            Dicionário com os monitores iniciados, onde as chaves são os IDs das pastas
        """
        self.logger.info("Iniciando todos os monitores configurados...")

        # Obter configurações de pastas recorrentes
        recurrent_folders = self.config_manager.get_recurrent_folders()

        self.logger.info(
            f"Total de pastas recorrentes configuradas: {len(recurrent_folders)}"
        )

        started_monitors = {}

        for folder_id, folder_config in recurrent_folders.items():
            if folder_config.get("enabled", True):
                self.logger.info(
                    f"Processando pasta {folder_id}: enabled={folder_config.get('enabled', True)}"
                )
                try:
                    monitor = self._create_monitor(folder_id, folder_config)
                    if monitor:
                        self.monitors[folder_id] = monitor
                        started_monitors[folder_id] = monitor
                        self.logger.info(f"Monitor iniciado para a pasta: {folder_id}")
                    else:
                        self.logger.error(
                            f"Falha ao criar monitor para a pasta: {folder_id}"
                        )
                except Exception as e:
                    self.logger.error(
                        f"Erro ao iniciar monitor para a pasta {folder_id}: {str(e)}"
                    )

        self.logger.info(f"{len(started_monitors)} monitores iniciados com sucesso.")
        return started_monitors

    def _create_monitor(
        self, folder_id: str, folder_config: Dict[str, Any]
    ) -> Optional[WatchFolderMonitor]:
        """
        Cria um monitor para uma pasta específica.

        Args:
            folder_id: ID da pasta
            folder_config: Configuração da pasta

        Returns:
            Instância de WatchFolderMonitor ou None em caso de erro
        """
        try:
            self.logger.info(f"Criando monitor para folder_id={folder_id}")
            self.logger.info(
                f"Configuração da pasta: path={folder_config.get('input_directory')}, output={folder_config.get('output_directory')}, profile={folder_config.get('profile_id')}"
            )
            # Converter a configuração da pasta recorrente para o formato esperado pelo WatchFolderMonitor
            watch_config = {
                "path": folder_config.get("input_directory"),  # Caminho de entrada
                "output_path": folder_config.get(
                    "output_directory"
                ),  # Caminho de saída
                "profile_id": folder_config.get("profile_id"),  # ID do perfil
                "folder_id": folder_id,  # ID da pasta recorrente
                "interval": folder_config.get(
                    "interval", 10
                ),  # Intervalo de verificação
                "min_size": folder_config.get(
                    "min_size", 10 * 1024 * 1024
                ),  # Tamanho mínimo
                "skip_existing_output": folder_config.get("skip_existing_output", True),
                "extensions": folder_config.get(
                    "supported_extensions",
                    [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"],
                ),
                "debounce_time": folder_config.get("debounce_time", 5),
                "enabled": folder_config.get("enabled", True),
                "priority": folder_config.get("priority", "normal"),
            }

            # Criar monitor com a configuração convertida
            monitor = WatchFolderMonitor(
                config=watch_config,
                queue_manager=self.queue_manager,
                job_manager=self.job_manager,
                profile_manager=self.profile_manager,
                history_manager=self.history_manager,
            )

            # Iniciar o monitor
            monitor.start()

            return monitor
        except Exception as e:
            self.logger.error(
                f"Erro ao criar monitor para a pasta {folder_id}: {str(e)}"
            )
            return None

    def stop_all_monitors(self) -> None:
        """Para todos os monitores ativos."""
        self.logger.info("Parando todos os monitores...")

        for folder_id, monitor in self.monitors.items():
            try:
                monitor.stop()
                self.logger.info(f"Monitor parado para a pasta: {folder_id}")
            except Exception as e:
                self.logger.error(
                    f"Erro ao parar monitor para a pasta {folder_id}: {str(e)}"
                )

        self.monitors.clear()
        self.logger.info("Todos os monitores foram parados.")

    def start_monitor(self, folder_id: str) -> bool:
        """
        Inicia um monitor específico pelo ID da pasta.

        Args:
            folder_id: ID da pasta a ser monitorada

        Returns:
            True se o monitor foi iniciado com sucesso, False caso contrário
        """
        self.logger.info(f"Tentando iniciar monitor para a pasta: {folder_id}")

        # Verificar se o monitor já está ativo
        if folder_id in self.monitors:
            self.logger.warning(f"Monitor já está ativo para a pasta: {folder_id}")
            return True

        # Obter configuração da pasta
        folder_config = self.config_manager.get_recurrent_folder(folder_id)
        if not folder_config:
            self.logger.error(f"Configuração não encontrada para a pasta: {folder_id}")
            return False

        # Verificar se o monitor está habilitado
        if not folder_config.get("enabled", True):
            self.logger.warning(f"Monitor está desabilitado para a pasta: {folder_id}")
            return False

        # Criar e iniciar o monitor
        monitor = self._create_monitor(folder_id, folder_config)
        if monitor:
            self.monitors[folder_id] = monitor
            self.logger.info(f"Monitor iniciado com sucesso para a pasta: {folder_id}")
            return True
        else:
            self.logger.error(f"Falha ao iniciar monitor para a pasta: {folder_id}")
            return False

    def stop_monitor(self, folder_id: str) -> bool:
        """
        Para um monitor específico pelo ID da pasta.

        Args:
            folder_id: ID da pasta cujo monitor deve ser parado

        Returns:
            True se o monitor foi parado com sucesso, False caso contrário
        """
        self.logger.info(f"Tentando parar monitor para a pasta: {folder_id}")

        if folder_id not in self.monitors:
            self.logger.warning(
                f"Nenhum monitor ativo encontrado para a pasta: {folder_id}"
            )
            return False

        try:
            monitor = self.monitors[folder_id]
            monitor.stop()
            del self.monitors[folder_id]
            self.logger.info(f"Monitor parado com sucesso para a pasta: {folder_id}")
            return True
        except Exception as e:
            self.logger.error(
                f"Erro ao parar monitor para a pasta {folder_id}: {str(e)}"
            )
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Retorna o status de todos os monitores ativos.

        Returns:
            Dicionário com o status de todos os monitores
        """
        status = {
            "total_monitors": len(self.monitors),
            "active_monitors": {},
            "monitor_count": len(self.monitors),
        }

        for folder_id, monitor in self.monitors.items():
            monitor_status = {
                "folder_id": folder_id,
                "is_running": monitor.is_running(),
                "source_path": getattr(monitor, "source_path", "N/A"),
                "destination_path": getattr(monitor, "destination_path", "N/A"),
                "last_event_time": getattr(monitor, "last_event_time", None),
                "processed_files": getattr(monitor, "processed_files", 0),
                "errors_count": getattr(monitor, "errors_count", 0),
            }
            status["active_monitors"][folder_id] = monitor_status

        return status

    def graceful_shutdown(self) -> None:
        """
        Realiza o desligamento gracioso de todos os monitores.
        """
        self.logger.info("Iniciando desligamento gracioso dos monitores...")

        # Parar todos os monitores
        self.stop_all_monitors()

        # Aguardar um pouco para garantir que os monitores foram encerrados
        try:
            self.executor.shutdown(wait=True, timeout=5)
        except Exception as e:
            self.logger.error(f"Erro ao encerrar executor: {str(e)}")

        self.logger.info("Desligamento gracioso dos monitores concluído.")

    def _queue_processor_loop(self):
        """Loop that pulls jobs from queue_manager and adds them to encoder."""
        from src.core.encoder_engine import EncodingJob

        self.logger.info("=== QUEUE PROCESSOR LOOP INICIADO ===")
        iteration = 0
        while self._queue_processor_running:
            try:
                iteration += 1
                if iteration % 10 == 0:  # Log every 10 iterations to reduce noise
                    self.logger.info(
                        f"Queue processor: iteration {iteration}, active={len(self.encoder.get_active_jobs()) if self.encoder else 0}, pending={len(self.encoder.get_pending_jobs()) if self.encoder else 0}"
                    )

                if self.encoder is not None and self.queue_manager is not None:
                    active_jobs = len(self.encoder.get_active_jobs())
                    pending_jobs = len(self.encoder.get_pending_jobs())

                    if active_jobs + pending_jobs < self.encoder.max_concurrent:
                        next_job = self.queue_manager.pop_next_job()
                        if next_job:
                            self.logger.info(
                                f">>> JOB ENCONTRADO NA QUEUE: {next_job['job_id'][:8] if next_job.get('job_id') else 'NO_ID'} - {next_job.get('input_path', 'NO_PATH')}"
                            )
                            encoding_job = EncodingJob(
                                id=next_job["job_id"],
                                input_path=next_job["input_path"],
                                output_path=next_job["output_path"],
                                profile=next_job["profile"],
                            )
                            self.encoder.add_job(encoding_job)
                            self.logger.info(
                                f"Job {next_job['job_id'][:8]} adicionado ao encoder"
                            )
                        else:
                            if iteration % 10 == 0:
                                self.logger.debug("Queue vazia, aguardando...")
            except Exception as e:
                self.logger.error(f"Erro no queue processor: {e}")

            time.sleep(1)

    def start(self) -> Dict[str, WatchFolderMonitor]:
        """Starts all monitors and the queue processor thread."""
        self.logger.info("=== START() CHAMADO ===")
        self.logger.info(f"Encoder configurado: {self.encoder is not None}")
        result = self.start_all_monitors()
        self.logger.info(f"Monitores criados: {len(result)}")

        if self.encoder is not None:
            self.logger.info("Iniciando encoder...")
            self.encoder.start()
            self._queue_processor_running = True
            self._queue_processor_thread = threading.Thread(
                target=self._queue_processor_loop, daemon=True
            )
            self._queue_processor_thread.start()
            self.logger.info("Queue processor thread started")
        else:
            self.logger.warning(
                "Encoder NÃO configurado - queue processor não será iniciado!"
            )

        return result

    def stop(self) -> None:
        """Stops all monitors and the queue processor thread."""
        self._queue_processor_running = False

        if self._queue_processor_thread:
            self._queue_processor_thread.join(timeout=5)
            self._queue_processor_thread = None

        if self.encoder is not None:
            self.encoder.stop()

        self.stop_all_monitors()

    def is_running(self) -> bool:
        """Retorna True se algum monitor está rodando."""
        return any(monitor.is_running() for monitor in self.monitors.values())
