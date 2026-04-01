import threading
import time
import re
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .ffmpeg_wrapper import FFmpegWrapper
from .hw_monitor import HardwareMonitor
from ..ui.realtime_monitor import RealTimeEncodingMonitor, FFmpegProgressParser


class EncodingStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class EncodingJob:
    id: str
    input_path: str
    output_path: str
    profile: Dict[str, Any]
    status: EncodingStatus = EncodingStatus.PENDING
    progress: float = 0.0
    error_message: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    input_size: int = 0
    output_size: int = 0


class EncoderEngine:
    """Motor de encoding que gerencia jobs e execução FFmpeg."""
    
    def __init__(
        self,
        ffmpeg_wrapper: Optional[FFmpegWrapper] = None,
        hw_monitor: Optional[HardwareMonitor] = None,
        realtime_monitor: Optional[RealTimeEncodingMonitor] = None,
        max_concurrent: int = 2,
        queue_manager: Optional[Any] = None
    ):
        self.ffmpeg = ffmpeg_wrapper or FFmpegWrapper()
        self.hw_monitor = hw_monitor or HardwareMonitor()
        self.realtime_monitor = realtime_monitor or RealTimeEncodingMonitor()
        self.max_concurrent = max_concurrent
        self._queue_manager = queue_manager  # Armazena referência ao queue manager
        
        self._jobs: Dict[str, EncodingJob] = {}
        self._active_jobs: Dict[str, EncodingJob] = {}
        self._completed_jobs: Dict[str, EncodingJob] = {}
        self._lock = threading.Lock()
        self._executor_thread: Optional[threading.Thread] = None
        self._running = False
        self._pause_event = threading.Event()
        self._pause_event.set()
        
        self._progress_callbacks: list[Callable[[str, float], None]] = []
        self._status_callbacks: list[Callable[[str, EncodingStatus], None]] = []
        self._encoding_stats_callbacks: list[Callable[[str, Dict[str, Any]], None]] = []
    
    def add_job(self, job: EncodingJob) -> str:
        """Adiciona job à fila."""
        with self._lock:
            self._jobs[job.id] = job
        return job.id
    
    def remove_job(self, job_id: str) -> bool:
        """Remove job da fila."""
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            if job_id in self._active_jobs:
                del self._active_jobs[job_id]
                return True
        return False
    
    def pause_job(self, job_id: str) -> bool:
        """Pausa job específico."""
        with self._lock:
            if job_id in self._active_jobs:
                job = self._active_jobs[job_id]
                job.status = EncodingStatus.PAUSED
                self.ffmpeg.terminate()
                for callback in self._status_callbacks:
                    callback(job_id, EncodingStatus.PAUSED)
                return True
        return False
    
    def resume_job(self, job_id: str) -> bool:
        """Retoma job pausado."""
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                job.status = EncodingStatus.PENDING
                self._pause_event.set()
                for callback in self._status_callbacks:
                    callback(job_id, EncodingStatus.PENDING)
                return True
        return False
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancela job."""
        with self._lock:
            if job_id in self._active_jobs:
                job = self._active_jobs[job_id]
                self.ffmpeg.terminate()
                job.status = EncodingStatus.CANCELLED
                job.completed_at = time.time()
                self._completed_jobs[job_id] = job
                del self._active_jobs[job_id]
                for callback in self._status_callbacks:
                    callback(job_id, EncodingStatus.CANCELLED)
                return True
            if job_id in self._jobs:
                job = self._jobs[job_id]
                job.status = EncodingStatus.CANCELLED
                job.completed_at = time.time()
                self._completed_jobs[job_id] = job
                del self._jobs[job_id]
                for callback in self._status_callbacks:
                    callback(job_id, EncodingStatus.CANCELLED)
                return True
        return False
    
    def get_job(self, job_id: str) -> Optional[EncodingJob]:
        """Retorna job por ID."""
        with self._lock:
            return self._jobs.get(job_id) or self._active_jobs.get(job_id) or self._completed_jobs.get(job_id)
    
    def get_all_jobs(self) -> Dict[str, EncodingJob]:
        """Retorna todos os jobs (pendentes, ativos e completos)."""
        with self._lock:
            return {**self._jobs, **self._active_jobs, **self._completed_jobs}

    def get_active_jobs(self) -> Dict[str, EncodingJob]:
        """Retorna jobs atualmente em execução."""
        with self._lock:
            return dict(self._active_jobs)

    def get_pending_jobs(self) -> Dict[str, EncodingJob]:
        """Retorna jobs pendentes."""
        with self._lock:
            return {jid: j for jid, j in self._jobs.items() if j.status == EncodingStatus.PENDING}
    
    def add_progress_callback(self, callback: Callable[[str, float], None]):
        """Adiciona callback para atualizações de progresso."""
        self._progress_callbacks.append(callback)
    
    def add_status_callback(self, callback: Callable[[str, EncodingStatus], None]):
        """Adiciona callback para mudanças de status."""
        self._status_callbacks.append(callback)
    
    def add_encoding_stats_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Adiciona callback para estatísticas de encoding."""
        self._encoding_stats_callbacks.append(callback)
    
    def start(self):
        """Inicia executor de jobs."""
        if self._running:
            return
        
        self._running = True
        self._pause_event.set()
        self.hw_monitor.start()
        self._executor_thread = threading.Thread(target=self._executor_loop, daemon=True)
        self._executor_thread.start()
    
    def stop(self):
        """Para executor e cancela jobs ativos."""
        self._running = False
        self._pause_event.set()
        
        for job_id in list(self._active_jobs.keys()):
            self.cancel_job(job_id)
        
        self.hw_monitor.stop()
        self.realtime_monitor.stop()
        
        if self._executor_thread:
            self._executor_thread.join(timeout=5)
            self._executor_thread = None
    
    def toggle_debug(self) -> bool:
        """Alterna estado do debug e retorna novo estado."""
        return self.realtime_monitor.toggle_debug()
    
    def is_debug_enabled(self) -> bool:
        """Retorna estado atual do debug."""
        return self.realtime_monitor.is_debug_enabled()
    
    def _executor_loop(self):
        """Loop principal do executor."""
        while self._running:
            self._pause_event.wait()
            
            with self._lock:
                if len(self._active_jobs) >= self.max_concurrent:
                    time.sleep(1)
                    continue
                
                pending_jobs = [
                    (jid, job) for jid, job in self._jobs.items()
                    if job.status == EncodingStatus.PENDING
                ]
                
                if not pending_jobs:
                    time.sleep(1)
                    continue
                
                job_id, job = pending_jobs[0]
                del self._jobs[job_id]
                job.status = EncodingStatus.RUNNING
                job.started_at = time.time()
                self._active_jobs[job_id] = job
            
            for callback in self._status_callbacks:
                callback(job_id, EncodingStatus.RUNNING)
            
            success, error = self._execute_job(job)
            
            with self._lock:
                if job_id in self._active_jobs:
                    job = self._active_jobs[job_id]
                    job.completed_at = time.time()

                    if success:
                        job.status = EncodingStatus.COMPLETED
                        job.progress = 100.0
                    else:
                        job.status = EncodingStatus.FAILED
                        job.error_message = error

                    del self._active_jobs[job_id]
                    self._completed_jobs[job_id] = job
            
            for callback in self._status_callbacks:
                callback(job_id, job.status)
            
            # Atualizar o progresso do job para 100% nos callbacks se for sucesso
            if success:
                for callback in self._progress_callbacks:
                    callback(job_id, 100.0)
    
    def _execute_job(self, job: EncodingJob) -> tuple[bool, str]:
        """Executa job de encoding."""
        from pathlib import Path
        
        input_file = Path(job.input_path)
        output_file = Path(job.output_path)
        
        if not input_file.exists():
            error_msg = f"Arquivo de entrada não existe: {job.input_path}"
            return (False, error_msg)
        
        if not input_file.is_file():
            error_msg = f"Caminho de entrada não é um arquivo: {job.input_path}"
            return (False, error_msg)
        
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            error_msg = f"Erro ao criar diretório de saída: {e}"
            return (False, error_msg)
        
        profile = job.profile
        media_info = self.ffmpeg.get_media_info(job.input_path)
        duration = self.ffmpeg.get_duration(media_info)
        video_streams = self.ffmpeg.get_video_streams(media_info)
        
        self.realtime_monitor.start(
            description=f"Encoding: {job.input_path}",
            total_duration=duration,
            input_file=job.input_path,
            output_file=job.output_path,
            input_media_info=media_info,
            profile=profile
        )
        
        parser = FFmpegProgressParser(monitor=self.realtime_monitor)
        parser.set_duration(duration)
        
        # Agora que o monitor está iniciado, adicionamos logs de debug
        self.realtime_monitor.add_debug_log(f"Job iniciado: {job.id[:8]}")
        self.realtime_monitor.add_debug_log(f"Input: {job.input_path}")
        self.realtime_monitor.add_debug_log(f"Output: {job.output_path}")
        self.realtime_monitor.add_debug_log(f"Profile: {profile.get('name', 'Unknown')}, Codec: {profile.get('codec', 'Unknown')}")
        self.realtime_monitor.add_debug_log(f"Duration: {duration}s, Video streams: {len(video_streams)}")
        command = self.ffmpeg.build_encoding_command(
            input_path=job.input_path,
            output_path=job.output_path,
            codec=profile.get('codec', 'hevc_nvenc'),
            cq=profile.get('cq'),
            bitrate=profile.get('bitrate'),
            resolution=profile.get('resolution'),
            preset=profile.get('preset', 'p5'),
            two_pass=profile.get('two_pass', False),
            hdr_to_sdr=profile.get('hdr_to_sdr', False),
            deinterlace=profile.get('deinterlace', False),
            audio_tracks=profile.get('audio_tracks'),
            subtitle_burn=profile.get('subtitle_burn', False),
            plex_compatible=profile.get('plex_compatible', True)
        )
        self.realtime_monitor.add_debug_log(f"Comando FFmpeg iniciado")
        
        def progress_callback(output: str):
            # [DEBUG PATCH] Log callback sendo chamado
            if not hasattr(progress_callback, '_call_count'):
                progress_callback._call_count = 0
            progress_callback._call_count += 1
            if progress_callback._call_count <= 3 or progress_callback._call_count % 10 == 0:
                print(f"\n[CALLBACK #{progress_callback._call_count}] {output[:100]}")
            
            stats = parser.parse_line(output)
            
            # [DEBUG PATCH] Log stats extraídos
            if stats and (progress_callback._call_count <= 3 or progress_callback._call_count % 10 == 0):
                print(f"[STATS] {stats}")
            
            if 'fps' in stats:
                self.realtime_monitor.update_encoding_stats(fps=stats['fps'])
            if 'speed' in stats:
                self.realtime_monitor.update_encoding_stats(speed=stats['speed'])
            if 'bitrate' in stats:
                self.realtime_monitor.update_encoding_stats(bitrate=stats['bitrate'])
            if 'current_time' in stats:
                self.realtime_monitor.update_progress(
                    progress=stats.get('progress', 0),
                    current_time=stats['current_time']
                )
            
            hw_stats = self.hw_monitor.get_stats()
            self.realtime_monitor.update_hw_stats({
                'gpu_util': hw_stats.gpu_util,
                'gpu_temperature': hw_stats.gpu_temperature,
                'gpu_memory_used': hw_stats.gpu_memory_used,
                'gpu_memory_total': hw_stats.gpu_memory_total,
                'cpu_util': hw_stats.cpu_util
            })
            
            if 'progress' in stats:
                job.progress = stats['progress']
                for callback in self._progress_callbacks:
                    callback(job.id, stats['progress'])
            
            if stats:
                for callback in self._encoding_stats_callbacks:
                    callback(job.id, stats)
        
            # Atualizar o PID do FFMPEG no job correspondente no UnifiedQueueManager
            if hasattr(self.ffmpeg, '_process') and self.ffmpeg._process:
                ffmpeg_pid = self.ffmpeg._process.pid
                # Procurar o job correspondente no UnifiedQueueManager e atualizar o PID
                try:
                    # Tenta obter o UnifiedQueueManager se estiver disponível
                    if hasattr(self, '_queue_manager'):
                        queue_job = self._queue_manager.get_job(job.id)
                        if queue_job and hasattr(queue_job, 'ffmpeg_pid'):
                            queue_job.ffmpeg_pid = ffmpeg_pid
                            # Salvar as alterações
                            self._queue_manager.save()
                except:
                    # Se não for possível atualizar o PID no queue manager, registrar aviso
                    print(f"Aviso: Não foi possível atualizar o PID do FFMPEG no job {job.id}")
            
            self.realtime_monitor.add_debug_log("Executando encoding...")
            success, error = self.ffmpeg.run_encoding(command, callback=progress_callback)
        
        if success:
            self.realtime_monitor.add_debug_log("Encoding completado com sucesso")
        else:
            self.realtime_monitor.add_debug_log(f"Erro no encoding: {error}")
        
        # Antes de parar o monitor, garantir que o progresso está completo
        if success:
            self.realtime_monitor.update_progress(100.0)
        
        self.realtime_monitor.stop()
        
        return (success, error)
    
    def set_pause(self, paused: bool):
        """Pausa ou retoma todos os jobs."""
        if paused:
            self._pause_event.clear()
        else:
            self._pause_event.set()
    
    def is_paused(self) -> bool:
        """Verifica se executor está pausado."""
        return not self._pause_event.is_set()
