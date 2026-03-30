import threading
import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .ffmpeg_wrapper import FFmpegWrapper
from .hw_monitor import HardwareMonitor


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
        max_concurrent: int = 2
    ):
        self.ffmpeg = ffmpeg_wrapper or FFmpegWrapper()
        self.hw_monitor = hw_monitor or HardwareMonitor()
        self.max_concurrent = max_concurrent
        
        self._jobs: Dict[str, EncodingJob] = {}
        self._active_jobs: Dict[str, EncodingJob] = {}
        self._lock = threading.Lock()
        self._executor_thread: Optional[threading.Thread] = None
        self._running = False
        self._pause_event = threading.Event()
        self._pause_event.set()
        
        self._progress_callbacks: list[Callable[[str, float], None]] = []
        self._status_callbacks: list[Callable[[str, EncodingStatus], None]] = []
    
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
                del self._active_jobs[job_id]
                for callback in self._status_callbacks:
                    callback(job_id, EncodingStatus.CANCELLED)
                return True
            if job_id in self._jobs:
                job = self._jobs[job_id]
                job.status = EncodingStatus.CANCELLED
                job.completed_at = time.time()
                del self._jobs[job_id]
                for callback in self._status_callbacks:
                    callback(job_id, EncodingStatus.CANCELLED)
                return True
        return False
    
    def get_job(self, job_id: str) -> Optional[EncodingJob]:
        """Retorna job por ID."""
        with self._lock:
            return self._jobs.get(job_id) or self._active_jobs.get(job_id)
    
    def get_all_jobs(self) -> Dict[str, EncodingJob]:
        """Retorna todos os jobs."""
        with self._lock:
            return {**self._jobs, **self._active_jobs}
    
    def add_progress_callback(self, callback: Callable[[str, float], None]):
        """Adiciona callback para atualizações de progresso."""
        self._progress_callbacks.append(callback)
    
    def add_status_callback(self, callback: Callable[[str, EncodingStatus], None]):
        """Adiciona callback para mudanças de status."""
        self._status_callbacks.append(callback)
    
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
        
        if self._executor_thread:
            self._executor_thread.join(timeout=5)
            self._executor_thread = None
    
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
                    
                    if success:
                        self._jobs[job_id] = job
            
            for callback in self._status_callbacks:
                callback(job_id, job.status)
    
    def _execute_job(self, job: EncodingJob) -> tuple[bool, str]:
        """Executa job de encoding."""
        profile = job.profile
        
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
        
        def progress_callback(output: str):
            progress = self._parse_ffmpeg_progress(output)
            if progress is not None:
                job.progress = progress
                for callback in self._progress_callbacks:
                    callback(job.id, progress)
        
        return self.ffmpeg.run_encoding(command, callback=progress_callback)
    
    def _parse_ffmpeg_progress(self, output: str) -> Optional[float]:
        """Extrai progresso do output do FFmpeg."""
        import re
        
        time_match = re.search(r'time=(\d+):(\d+):(\d+)', output)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = int(time_match.group(3))
            current_seconds = hours * 3600 + minutes * 60 + seconds
            
            duration_match = re.search(r'Duration: (\d+):(\d+):(\d+)', output)
            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = int(duration_match.group(3))
                total_seconds = hours * 3600 + minutes * 60 + seconds
                
                if total_seconds > 0:
                    return (current_seconds / total_seconds) * 100
        
        return None
    
    def set_pause(self, paused: bool):
        """Pausa ou retoma todos os jobs."""
        if paused:
            self._pause_event.clear()
        else:
            self._pause_event.set()
    
    def is_paused(self) -> bool:
        """Verifica se executor está pausado."""
        return not self._pause_event.is_set()
