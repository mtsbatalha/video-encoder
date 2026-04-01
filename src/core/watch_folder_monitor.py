import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import os

from ..utils.file_utils import FileUtils, FileConflictStrategy
from ..managers.queue_manager import QueueManager, QueuePriority
from ..managers.job_manager import JobManager
from ..managers.profile_manager import ProfileManager
from ..managers.recurrent_history_manager import RecurrentHistoryManager


class WatchFolderMonitor:
    """Monitor de pastas para detecção e processamento automático de arquivos de vídeo."""

    def __init__(
        self,
        config: Dict[str, Any],
        queue_manager: QueueManager,
        job_manager: JobManager,
        profile_manager: ProfileManager,
        history_manager: Optional[RecurrentHistoryManager] = None,
    ):
        self.config = config
        self.queue_manager = queue_manager
        self.job_manager = job_manager
        self.profile_manager = profile_manager
        self.history_manager = history_manager  # Gerenciador de histórico opcional

        # Configurações do monitor
        self.watch_path = Path(config.get("path", ""))
        self.profile_id = config.get("profile_id", "")
        self.folder_id = config.get(
            "folder_id", ""
        )  # ID da pasta recorrente (opcional)
        self.interval = config.get("interval", 10)  # segundos entre verificações
        self.min_size = config.get("min_size", 10 * 1024 * 1024)  # 10MB em bytes
        self.skip_existing_output = config.get("skip_existing_output", True)
        self.rename_existing_output = config.get(
            "rename_existing_output", False
        )  # Renomeia automaticamente
        self.extensions = config.get(
            "extensions", [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"]
        )
        self.debounce_time = config.get("debounce_time", 5)  # segundos para debounce
        self.enabled = config.get("enabled", True)

        # Estados internos
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._processed_files = set()  # Arquivos já processados

        # Configurar logging
        self.logger = logging.getLogger(f"{__name__}.{self.watch_path.name}")
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def start(self) -> None:
        """Inicia o monitoramento da pasta."""
        if not self.enabled:
            self.logger.info(f"Monitoramento desabilitado para {self.watch_path}")
            return

        if not self.watch_path.exists():
            self.logger.error(f"Caminho de monitoramento não existe: {self.watch_path}")
            return

        if self._monitor_thread and self._monitor_thread.is_alive():
            self.logger.warning(
                f"Monitoramento já está em execução para {self.watch_path}"
            )
            return

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self.logger.info(f"Iniciando monitoramento da pasta: {self.watch_path}")

    def stop(self) -> None:
        """Para o monitoramento da pasta."""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)  # Espera até 2 segundos pelo término
        self.logger.info(f"Monitoramento parado para: {self.watch_path}")

    def is_running(self) -> bool:
        """Returns True if the monitor thread is running."""
        return self._monitor_thread is not None and self._monitor_thread.is_alive()

    def _monitor_loop(self) -> None:
        """Loop principal de monitoramento."""
        self.logger.info(f">>> MONITOR LOOP INICIADO para {self.watch_path}")
        while not self._stop_event.wait(self.interval):  # Aguarda intervalo ou stop
            try:
                self.logger.info(
                    f"Verificando arquivos em {self.watch_path} (intervalo: {self.interval}s)"
                )
                self._check_for_new_files()
            except Exception as e:
                self.logger.error(f"Erro no monitoramento de {self.watch_path}: {e}")

    def _check_for_new_files(self) -> None:
        """Verifica por novos arquivos na pasta."""
        if not self.watch_path.exists():
            self.logger.warning(f"Caminho não existe: {self.watch_path}")
            return

        try:
            # Busca arquivos com extensões suportadas
            found_files = []
            for ext in self.extensions:
                files = list(self.watch_path.rglob(f"*{ext}"))
                found_files.extend(files)
                if files:
                    self.logger.info(
                        f"Encontrados {len(files)} arquivos com extensão {ext}"
                    )

            self.logger.info(f"Total de arquivos encontrados: {len(found_files)}")

            # Processa cada arquivo encontrado
            for file_path in found_files:
                try:
                    should_process = self._should_process_file(file_path)
                    self.logger.info(
                        f"Arquivo {file_path.name}: should_process={should_process}"
                    )
                    if should_process:
                        if self._is_file_complete(file_path):
                            self.logger.info(f">>> ENFILEIRANDO: {file_path}")
                            self._enqueue_file(file_path)
                            self._processed_files.add(str(file_path))
                        else:
                            self.logger.debug(
                                f"Arquivo ainda sendo copiado, aguardando: {file_path}"
                            )
                except Exception as e:
                    self.logger.error(f"Erro ao processar arquivo {file_path}: {e}")

        except Exception as e:
            self.logger.error(f"Erro ao buscar arquivos em {self.watch_path}: {e}")

    def _is_file_complete(self, path: Path) -> bool:
        """Verifica se arquivo está completo (implementa debounce)."""
        try:
            initial_size = path.stat().st_size
            time.sleep(self.debounce_time)  # Aguarda para ver se o tamanho muda

            # Verifica novamente o tamanho
            current_size = path.stat().st_size

            # Se o tamanho mudou, o arquivo ainda está sendo escrito
            if initial_size != current_size:
                self.logger.debug(
                    f"Tamanho do arquivo mudou ({initial_size} -> {current_size}), ainda sendo copiado: {path}"
                )
                return False

            # Verifica se o arquivo está bloqueado (em uso por outro processo)
            if FileUtils.is_file_locked(str(path)):
                self.logger.debug(f"Arquivo bloqueado, ainda sendo copiado: {path}")
                return False

            return True
        except Exception as e:
            self.logger.error(f"Erro ao verificar se arquivo está completo {path}: {e}")
            return False

    def _should_process_file(self, path: Path) -> bool:
        """Verifica se arquivo deve ser processado."""
        try:
            # Verifica se já foi processado recentemente
            if str(path) in self._processed_files:
                return False

            # Verifica extensão
            if path.suffix.lower() not in self.extensions:
                return False

            # Verifica tamanho mínimo
            try:
                file_size = path.stat().st_size
                if file_size < self.min_size:
                    self.logger.debug(
                        f"Arquivo abaixo do tamanho mínimo ({self.min_size} bytes): {path} ({file_size} bytes)"
                    )
                    return False
            except OSError:
                # Arquivo pode estar bloqueado ou indisponível
                return False

            # Verifica se output já existe (se configurado para pular)
            if self.skip_existing_output:
                output_path = self._get_output_path(path)
                if output_path and output_path.exists():
                    self.logger.info(f"Output já existe, pulando: {output_path}")
                    return False

            # Verifica se profile existe
            if not self.profile_manager.get_profile(self.profile_id):
                self.logger.error(f"Profile não encontrado: {self.profile_id}")
                return False

            return True
        except Exception as e:
            self.logger.error(
                f"Erro ao verificar se deve processar arquivo {path}: {e}"
            )
            return False

    def _get_output_path(self, input_path: Path) -> Optional[Path]:
        """Gera caminho de saída baseado no caminho de entrada."""
        try:
            # Obtém o profile para determinar extensão de saída
            profile = self.profile_manager.get_profile(self.profile_id)
            if not profile:
                return None

            # Determina extensão de saída baseado no codec
            codec = profile.get("codec", "hevc_nvenc")
            if "h264" in codec:
                output_ext = ".mp4"
            elif "hevc" in codec or "265" in codec:
                output_ext = ".mp4"  # HEVC geralmente usa .mp4
            elif "av1" in codec:
                output_ext = ".mkv"
            else:
                output_ext = ".mp4"  # padrão

            # Define pasta de saída (pode vir do profile ou usar padrão)
            output_dir_str = self.config.get(
                "output_path", str(input_path.parent / "encoded")
            )
            output_dir = Path(output_dir_str)

            # Cria nome de arquivo de saída
            output_filename = input_path.stem + output_ext
            output_path = output_dir / output_filename

            return output_path
        except Exception as e:
            self.logger.error(f"Erro ao gerar caminho de saída para {input_path}: {e}")
            return None

    def _enqueue_file(self, path: Path) -> None:
        """Adiciona arquivo à fila de encoding."""
        self.logger.info(f">>> _enqueue_file() CHAMADO para {path}")
        try:
            # Gera caminho de saída
            output_path = self._get_output_path(path)
            if not output_path:
                self.logger.error(f"Falha ao gerar caminho de saída para: {path}")
                return

            # Verifica se output já existe e aplica ação configurada
            if output_path.exists():
                if self.skip_existing_output:
                    # Se configurado para pular, ignora este arquivo
                    self.logger.info(f"Output já existe, pulando: {output_path}")
                    return
                elif self.rename_existing_output:
                    # Se configurado para renomear, gera nome único com numeração
                    output_path = Path(
                        FileUtils.generate_unique_filename(str(output_path))
                    )
                    self.logger.info(
                        f"Output já existe, usando nome alternativo: {output_path}"
                    )
                # else: vai substituir o arquivo existente (não faz nada aqui)

            # Garante que diretório de saída existe
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Obtém o profile
            profile = self.profile_manager.get_profile(self.profile_id)
            if not profile:
                self.logger.error(f"Profile não encontrado: {self.profile_id}")
                return

            # Cria job
            job_id = self.job_manager.create_job(
                input_path=str(path),
                output_path=str(output_path),
                profile_id=self.profile_id,
                profile_name=profile.get("name", self.profile_id),
            )

            # Registra callback para rastrear o status do job se tivermos um history_manager
            if self.history_manager and self.folder_id:
                self.job_manager.register_status_callback(
                    job_id, self._on_job_status_change
                )

            # Adiciona à fila
            priority_value = self.config.get("priority", "normal")
            priority_map = {
                "low": QueuePriority.LOW,
                "normal": QueuePriority.NORMAL,
                "high": QueuePriority.HIGH,
                "critical": QueuePriority.CRITICAL,
            }
            priority = priority_map.get(priority_value, QueuePriority.NORMAL)

            queue_pos = self.queue_manager.add_to_queue(
                job_id=job_id,
                input_path=str(path),
                output_path=str(output_path),
                profile=profile,
                priority=priority,
            )

            self.logger.info(
                f"Arquivo adicionado à fila: {path} -> {output_path} (posição: {queue_pos})"
            )

        except Exception as e:
            self.logger.error(f"Erro ao enfileirar arquivo {path}: {e}")

    def _on_job_status_change(
        self, job_id: str, old_status: str, new_status: str
    ) -> None:
        """Callback chamado quando o status do job muda."""
        try:
            job = self.job_manager.get_job(job_id)
            if not job or not self.history_manager or not self.folder_id:
                return

            # Registra no histórico quando o job é completado ou falha
            if new_status in ["completed", "failed"]:
                input_path = job.get("input_path", "")
                output_path = job.get("output_path", "")

                # Converte timestamps do job
                started_at_str = job.get("started_at")
                completed_at_str = job.get("completed_at")

                if started_at_str and completed_at_str:
                    try:
                        started_at = datetime.fromisoformat(
                            started_at_str.replace("Z", "+00:00")
                        )
                        completed_at = datetime.fromisoformat(
                            completed_at_str.replace("Z", "+00:00")
                        )

                        error_message = (
                            job.get("error_message") if new_status == "failed" else None
                        )

                        # Adiciona entrada no histórico
                        self.history_manager.add_entry(
                            folder_id=self.folder_id,
                            input_path=input_path,
                            output_path=output_path,
                            status=new_status,
                            started_at=started_at,
                            completed_at=completed_at,
                            error_message=error_message,
                        )

                        self.logger.info(
                            f"Registro de histórico adicionado para job {job_id} (status: {new_status})"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Erro ao converter timestamps para job {job_id}: {e}"
                        )
        except Exception as e:
            self.logger.error(f"Erro no callback de status do job {job_id}: {e}")
