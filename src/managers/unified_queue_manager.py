"""
Unified Queue Manager - Gerenciador unificado de fila de encoding.

Este módulo implementa um sistema unificado para gerenciamento de fila de jobs
de encoding, substituindo os antigos QueueManager e JobManager.

Author: Video Encoder Team
Version: 2.0.0
"""

import json
import threading
import uuid
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
import time


class JobStatus(Enum):
    """Status possíveis de um job na fila."""
    PENDING = "pending"       # Job criado, aguardando na fila
    QUEUED = "queued"         # Job na fila, aguardando execução
    RUNNING = "running"       # Job em execução
    PAUSED = "paused"         # Job pausado pelo usuário
    COMPLETED = "completed"   # Job completado com sucesso
    FAILED = "failed"         # Job falhou com erro
    CANCELLED = "cancelled"   # Job cancelado pelo usuário


class QueuePriority(Enum):
    """Níveis de prioridade para jobs na fila."""
    LOW = 1       # Baixa prioridade
    NORMAL = 2    # Prioridade normal (padrão)
    HIGH = 3      # Alta prioridade
    CRITICAL = 4  # Prioridade crítica (executa primeiro)


@dataclass
class ResourceUsage:
    """Representação do uso de recursos por um job."""
    gpu_usage: float = 0.0        # Uso da GPU (%)
    vram_usage: float = 0.0       # Uso de VRAM (GB)
    cpu_usage: float = 0.0        # Uso da CPU (%)
    memory_usage: float = 0.0     # Uso de memória RAM (GB)
    encoder_utilization: float = 0.0  # Utilização do encoder (%)
    
    def to_dict(self) -> Dict[str, float]:
        """Converte para dicionário."""
        return {
            "gpu_usage": self.gpu_usage,
            "vram_usage": self.vram_usage,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "encoder_utilization": self.encoder_utilization
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "ResourceUsage":
        """Cria instância a partir de dicionário."""
        return cls(
            gpu_usage=data.get("gpu_usage", 0.0),
            vram_usage=data.get("vram_usage", 0.0),
            cpu_usage=data.get("cpu_usage", 0.0),
            memory_usage=data.get("memory_usage", 0.0),
            encoder_utilization=data.get("encoder_utilization", 0.0)
        )


@dataclass
class QueueJob:
    """
    Representação completa de um job na fila de encoding.
    
    Atributos:
        id: UUID único do job
        input_path: Caminho do arquivo de entrada
        output_path: Caminho do arquivo de saída
        profile: Configurações do perfil de encoding
        profile_name: Nome legível do perfil
        status: Status atual do job
        progress: Progresso em porcentagem (0-100)
        priority: Nível de prioridade (1-4)
        created_at: Timestamp de criação (ISO format)
        started_at: Timestamp de início (ISO format)
        paused_at: Timestamp de pausa (ISO format)
        resumed_at: Timestamp de retomada (ISO format)
        completed_at: Timestamp de conclusão (ISO format)
        elapsed_time: Tempo decorrido formatado (HH:MM:SS)
        eta: Tempo estimado para conclusão (HH:MM:SS)
        speed: Velocidade de encoding (%/min)
        input_size: Tamanho do arquivo de entrada (bytes)
        output_size: Tamanho do arquivo de saída (bytes)
        compression_ratio: Razão de compressão (output/input)
        error_message: Mensagem de erro (se falhou)
        retry_count: Contador de tentativas de retry
        resource_usage: Uso de recursos (GPU, CPU, VRAM, RAM)
        ffmpeg_pid: PID do processo FFmpeg
        log_file: Caminho para arquivo de log
    """
    id: str
    input_path: str
    output_path: str
    profile: Dict[str, Any]
    profile_name: str
    status: str = JobStatus.PENDING.value
    progress: float = 0.0
    priority: int = QueuePriority.NORMAL.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    paused_at: Optional[str] = None
    resumed_at: Optional[str] = None
    completed_at: Optional[str] = None
    elapsed_time: str = "00:00:00"
    eta: str = "--:--:--"
    speed: float = 0.0
    input_size: int = 0
    output_size: int = 0
    compression_ratio: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0
    resource_usage: ResourceUsage = field(default_factory=ResourceUsage)
    ffmpeg_pid: Optional[int] = None
    log_file: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte job para dicionário serializável."""
        data = asdict(self)
        data["resource_usage"] = self.resource_usage.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueueJob":
        """Cria job a partir de dicionário."""
        if "resource_usage" in data:
            data["resource_usage"] = ResourceUsage.from_dict(data["resource_usage"])
        else:
            data["resource_usage"] = ResourceUsage()
        return cls(**data)
    
    def get_details_dict(self) -> Dict[str, Any]:
        """Retorna dicionário completo com todos os detalhes do job."""
        details = self.to_dict()
        details["status_display"] = self._get_status_display()
        details["input_size_formatted"] = self._format_file_size(self.input_size)
        details["output_size_formatted"] = self._format_file_size(self.output_size)
        return details
    
    def _get_status_display(self) -> str:
        """Retorna representação formatada do status."""
        displays = {
            JobStatus.PENDING.value: "[PENDENTE]",
            JobStatus.QUEUED.value: "[NA FILA]",
            JobStatus.RUNNING.value: "[EXECUTANDO]",
            JobStatus.PAUSED.value: "[PAUSADO]",
            JobStatus.COMPLETED.value: "[COMPLETO]",
            JobStatus.FAILED.value: "[FALHOU]",
            JobStatus.CANCELLED.value: "[CANCELADO]"
        }
        return displays.get(self.status, self.status)
    
    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """Formata tamanho de arquivo em unidades legíveis."""
        if size_bytes <= 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


class UnifiedQueueManager:
    """
    Gerenciador unificado de fila de encoding.
    
    Este classe fornece uma interface completa para gerenciamento de jobs
    de encoding, incluindo:
    - Adição, remoção e modificação de jobs
    - Controle de execução (pausar, retomar, cancelar)
    - Gerenciamento de prioridade e ordenação
    - Persistência em arquivo JSON
    - Callbacks para atualizações em tempo real
    - Detecção automática de limites de hardware
    
    Exemplo de uso:
        >>> mgr = UnifiedQueueManager()
        >>> job = mgr.add_job("/input/video.mp4", "/output/video.mp4", profile)
        >>> mgr.pause_job(job.id)
        >>> mgr.resume_job(job.id)
        >>> stats = mgr.get_statistics()
    """
    
    VERSION = "2.0"
    SCHEMA_VERSION = 1
    
    def __init__(
        self,
        jobs_dir: Optional[str] = None,
        max_concurrent_jobs: Optional[int] = None
    ):
        """
        Inicializa o gerenciador de fila.
        
        Args:
            jobs_dir: Diretório para armazenar dados dos jobs (padrão: ./jobs)
            max_concurrent_jobs: Máximo de jobs simultâneos (padrão: auto-detect)
        """
        self.jobs_dir = Path(jobs_dir) if jobs_dir else Path(__file__).parent.parent.parent / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar subdiretórios
        (self.jobs_dir / "logs").mkdir(exist_ok=True)
        (self.jobs_dir / "temp").mkdir(exist_ok=True)
        (self.jobs_dir / "history").mkdir(exist_ok=True)
        
        self.data_file = self.jobs_dir / "queue.json"
        
        # Estado interno
        self._jobs: Dict[str, QueueJob] = {}
        self._queue_order: List[str] = []  # Lista ordenada de job IDs
        self._active_jobs: set[str] = set()  # Jobs em execução
        self._max_concurrent_jobs = max_concurrent_jobs or self._calculate_max_concurrent_jobs()
        self._paused = False
        
        # Callbacks
        self._status_callbacks: Dict[str, List[Callable]] = {}
        self._progress_callbacks: Dict[str, List[Callable]] = {}
        self._global_status_callbacks: List[Callable] = []
        self._global_progress_callbacks: List[Callable] = []
        
        # Thread safety
        self._lock = threading.RLock()
        self._save_lock = threading.Lock()
        
        # Auto-save
        self._auto_save_interval = 5  # segundos
        self._last_save_time = 0
        self._pending_save = False
        
        # Carregar dados existentes
        self.load()
    
    def _calculate_max_concurrent_jobs(self) -> int:
        """
        Calcula o número máximo de jobs simultâneos baseado no hardware.
        
        Returns:
            Número máximo de jobs que podem ser executados simultaneamente
        """
        try:
            # Tentar importação relativa primeiro
            try:
                from ..core.hw_detector import HardwareDetector
            except (ImportError, ValueError):
                # Fallback para importação absoluta se estiver fora do pacote
                from core.hw_detector import HardwareDetector
            
            detector = HardwareDetector()
            caps = detector.detect()
            
            # Calcular limites
            max_by_gpu = 0
            max_by_cpu = max(1, caps.cpu_cores // 2)  # 1-2 cores por job
            
            # GPUs NVIDIA
            for gpu in caps.gpus_nvidia:
                if gpu.get('nvenc_supported', False):
                    vram_per_job_gb = 6.0
                    gpu_max_jobs = int(gpu.get('memory_gb', 0) / vram_per_job_gb)
                    max_by_gpu = max(max_by_gpu, gpu_max_jobs)
            
            # GPUs AMD
            for gpu in caps.gpus_amd:
                if gpu.get('amf_supported', False):
                    vram_per_job_gb = 4.0
                    gpu_max_jobs = int(gpu.get('vram_gb', 0) / vram_per_job_gb)
                    max_by_gpu = max(max_by_gpu, gpu_max_jobs)
            
            # iGPUs
            if caps.igpu_intel and caps.igpu_intel.get('qsv_supported', False):
                max_by_gpu = max(max_by_gpu, 2)
            
            if caps.igpu_amd and caps.igpu_amd.get('amf_supported', False):
                max_by_gpu = max(max_by_gpu, 2)
            
            # Retornar limite mais restritivo
            if max_by_gpu > 0:
                return min(max_by_gpu, max_by_cpu)
            else:
                return max_by_cpu
                
        except Exception as e:
            print(f"Erro ao calcular limite de jobs: {e}")
            return 2  # Valor padrão seguro
    
    # =========================================================================
    # MÉTODOS DE GERENCIAMENTO DE JOBS
    # =========================================================================
    
    def add_job(
        self,
        input_path: str,
        output_path: str,
        profile: Dict[str, Any],
        priority: QueuePriority = QueuePriority.NORMAL
    ) -> QueueJob:
        """
        Adiciona um novo job à fila.
        
        Args:
            input_path: Caminho do arquivo de entrada
            output_path: Caminho do arquivo de saída
            profile: Configurações do perfil de encoding
            priority: Prioridade do job (padrão: NORMAL)
        
        Returns:
            QueueJob: O job criado
        """
        with self._lock:
            job_id = str(uuid.uuid4())
            
            # Extrair nome do perfil
            profile_name = profile.get('name', profile.get('id', 'Unknown'))
            
            # Criar job
            job = QueueJob(
                id=job_id,
                input_path=str(input_path),
                output_path=str(output_path),
                profile=profile,
                profile_name=profile_name,
                status=JobStatus.QUEUED.value,
                priority=priority.value
            )
            
            # Adicionar à fila
            self._jobs[job_id] = job
            self._queue_order.append(job_id)
            
            # Ordenar por prioridade
            self._sort_queue_by_priority()
            
            # Salvar
            self.save()
            
            # Trigger callbacks
            self._trigger_status_callbacks(job_id, JobStatus.PENDING.value, JobStatus.QUEUED.value)
            
            return job
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove um job da fila.
        
        Args:
            job_id: ID do job para remover
        
        Returns:
            bool: True se removido com sucesso
        """
        with self._lock:
            if job_id not in self._jobs:
                return False
            
            # Remover da lista de ativos se estiver lá
            self._active_jobs.discard(job_id)
            
            # Remover da fila
            if job_id in self._queue_order:
                self._queue_order.remove(job_id)
            
            # Remover do dicionário
            del self._jobs[job_id]
            
            # Remover callbacks
            self._status_callbacks.pop(job_id, None)
            self._progress_callbacks.pop(job_id, None)
            
            # Salvar
            self.save()
            
            return True
    
    def get_job(self, job_id: str) -> Optional[QueueJob]:
        """
        Obtém um job por ID.
        
        Args:
            job_id: ID do job
        
        Returns:
            QueueJob ou None se não encontrado
        """
        with self._lock:
            return self._jobs.get(job_id)
    
    def get_job_details(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes completos de um job como dicionário.
        
        Args:
            job_id: ID do job
        
        Returns:
            Dict com todos os detalhes do job ou None
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                return job.get_details_dict()
            return None
    
    # =========================================================================
    # MÉTODOS DE CONTROLE DE EXECUÇÃO
    # =========================================================================
    
    def pause_job(self, job_id: str) -> bool:
        """
        Pausa um job em execução.
        
        Args:
            job_id: ID do job para pausar
        
        Returns:
            bool: True se pausado com sucesso
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            if job.status != JobStatus.RUNNING.value:
                return False
            
            old_status = job.status
            job.status = JobStatus.PAUSED.value
            job.paused_at = datetime.now().isoformat()
            
            # Remover de ativos
            self._active_jobs.discard(job_id)
            
            # Salvar
            self.save()
            
            # Trigger callbacks
            self._trigger_status_callbacks(job_id, old_status, JobStatus.PAUSED.value)
            
            return True
    
    def resume_job(self, job_id: str) -> bool:
        """
        Retoma um job pausado.
        
        Args:
            job_id: ID do job para retomar
        
        Returns:
            bool: True se retomado com sucesso
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            if job.status != JobStatus.PAUSED.value:
                return False
            
            # Verificar se pode iniciar novo job
            if not self.can_start_new_job():
                return False
            
            old_status = job.status
            job.status = JobStatus.RUNNING.value
            job.resumed_at = datetime.now().isoformat()
            
            # Adicionar a ativos
            self._active_jobs.add(job_id)
            
            # Salvar
            self.save()
            
            # Trigger callbacks
            self._trigger_status_callbacks(job_id, old_status, JobStatus.RUNNING.value)
            
            return True
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancela um job.
        
        Args:
            job_id: ID do job para cancelar
        
        Returns:
            bool: True se cancelado com sucesso
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            old_status = job.status
            job.status = JobStatus.CANCELLED.value
            job.completed_at = datetime.now().isoformat()
            
            # Remover de ativos
            self._active_jobs.discard(job_id)
            
            # Remover da fila
            if job_id in self._queue_order:
                self._queue_order.remove(job_id)
            
            # Salvar
            self.save()
            
            # Trigger callbacks
            self._trigger_status_callbacks(job_id, old_status, JobStatus.CANCELLED.value)
            
            return True
    
    def retry_job(self, job_id: str) -> Optional[str]:
        """
        Retenta um job falhado ou cancelado.
        
        Args:
            job_id: ID do job para retentar
        
        Returns:
            str: ID do novo job ou None se não pode retentar
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            
            # Só pode retentar jobs falhados ou cancelados
            if job.status not in [JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
                return None
            
            # Criar novo job baseado no antigo
            new_job = self.add_job(
                input_path=job.input_path,
                output_path=job.output_path,
                profile=job.profile,
                priority=QueuePriority(job.priority)
            )
            
            # Incrementar retry count
            new_job.retry_count = job.retry_count + 1
            
            # Salvar
            self.save()
            
            return new_job.id
    
    # =========================================================================
    # MÉTODOS DE GERENCIAMENTO DE FILA
    # =========================================================================
    
    def list_queue(
        self,
        status_filter: Optional[JobStatus] = None,
        sort_by: str = "priority",
        ascending: bool = False
    ) -> List[QueueJob]:
        """
        Lista jobs na fila com filtros e ordenação.
        
        Args:
            status_filter: Filtrar por status (opcional)
            sort_by: Campo para ordenar (priority, created_at, status)
            ascending: Ordenação ascendente (padrão: descendente)
        
        Returns:
            Lista de jobs filtrados e ordenados
        """
        with self._lock:
            jobs = list(self._jobs.values())
            
            # Aplicar filtro de status
            if status_filter:
                jobs = [j for j in jobs if j.status == status_filter.value]
            
            # Ordenar
            reverse = not ascending
            if sort_by == "priority":
                jobs.sort(key=lambda x: (-x.priority, x.created_at), reverse=reverse)
            elif sort_by == "created_at":
                jobs.sort(key=lambda x: x.created_at, reverse=reverse)
            elif sort_by == "status":
                jobs.sort(key=lambda x: x.status, reverse=reverse)
            
            return jobs
    
    def reorder_job(self, job_id: str, new_position: int) -> bool:
        """
        Reordena um job para uma nova posição na fila.
        
        Args:
            job_id: ID do job para reordenar
            new_position: Nova posição (0-based index)
        
        Returns:
            bool: True se reordenado com sucesso
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            # Jobs em execução não podem ser reordenados
            if job.status == JobStatus.RUNNING.value:
                return False
            
            if job_id not in self._queue_order:
                return False
            
            # Remover e inserir na nova posição
            self._queue_order.remove(job_id)
            new_position = max(0, min(new_position, len(self._queue_order)))
            self._queue_order.insert(new_position, job_id)
            
            # Salvar
            self.save()
            
            return True
    
    def set_job_priority(self, job_id: str, priority: QueuePriority) -> bool:
        """
        Define a prioridade de um job e reordena a fila.
        
        Args:
            job_id: ID do job
            priority: Nova prioridade
        
        Returns:
            bool: True se atualizado com sucesso
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            job.priority = priority.value
            
            # Reordenar fila por prioridade
            self._sort_queue_by_priority()
            
            # Salvar
            self.save()
            
            return True
    
    def clear_queue(self, status_filter: Optional[JobStatus] = None) -> int:
        """
        Limpa a fila de jobs.
        
        Args:
            status_filter: Filtrar por status para remoção (opcional)
        
        Returns:
            int: Número de jobs removidos
        """
        with self._lock:
            if status_filter:
                # Remover apenas jobs com status específico
                to_remove = [
                    j.id for j in self._jobs.values()
                    if j.status == status_filter.value
                ]
                for job_id in to_remove:
                    self.remove_job(job_id)
                return len(to_remove)
            else:
                # Limpar tudo
                count = len(self._jobs)
                self._jobs.clear()
                self._queue_order.clear()
                self._active_jobs.clear()
                self.save()
                return count
    
    # =========================================================================
    # CONTROLE DA FILA
    # =========================================================================
    
    def pause_queue(self) -> bool:
        """
        Pausa o processamento da fila.
        
        Returns:
            bool: True se pausado com sucesso
        """
        with self._lock:
            self._paused = True
            self.save()
            return True
    
    def resume_queue(self) -> bool:
        """
        Retoma o processamento da fila.
        
        Returns:
            bool: True se retomado com sucesso
        """
        with self._lock:
            self._paused = False
            self.save()
            return True
    
    def is_queue_paused(self) -> bool:
        """
        Verifica se a fila está pausada.
        
        Returns:
            bool: True se pausada
        """
        return self._paused
    
    # =========================================================================
    # MÉTODOS DE HARDWARE E CONCURRENÇA
    # =========================================================================
    
    def can_start_new_job(self) -> bool:
        """
        Verifica se pode iniciar um novo job.
        
        Returns:
            bool: True se pode iniciar novo job
        """
        return len(self._active_jobs) < self._max_concurrent_jobs and not self._paused
    
    def register_active_job(self, job_id: str) -> bool:
        """
        Registra um job como ativo (em execução).
        
        Args:
            job_id: ID do job
        
        Returns:
            bool: True se registrado com sucesso
        """
        with self._lock:
            if not self.can_start_new_job():
                return False
            
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            self._active_jobs.add(job_id)
            job.status = JobStatus.RUNNING.value
            job.started_at = datetime.now().isoformat()
            
            self.save()
            self._trigger_status_callbacks(job_id, JobStatus.QUEUED.value, JobStatus.RUNNING.value)
            
            return True
    
    def unregister_active_job(self, job_id: str) -> None:
        """
        Desregistra um job da lista de ativos.
        
        Args:
            job_id: ID do job
        """
        with self._lock:
            self._active_jobs.discard(job_id)
    
    def get_max_concurrent_jobs(self) -> int:
        """
        Obtém o número máximo de jobs simultâneos.
        
        Returns:
            int: Máximo de jobs simultâneos
        """
        return self._max_concurrent_jobs
    
    def get_active_jobs_count(self) -> int:
        """
        Obtém o número de jobs ativos.
        
        Returns:
            int: Número de jobs ativos
        """
        return len(self._active_jobs)
    
    # =========================================================================
    # ESTATÍSTICAS E INFORMAÇÕES
    # =========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtém estatísticas completas da fila.
        
        Returns:
            Dict com estatísticas da fila
        """
        with self._lock:
            total = len(self._jobs)
            
            # Contar por status
            by_status = {}
            for status in JobStatus:
                by_status[status.value] = sum(1 for j in self._jobs.values() if j.status == status.value)
            
            # Contar por prioridade
            by_priority = {}
            for priority in QueuePriority:
                by_priority[priority.name.lower()] = sum(1 for j in self._jobs.values() if j.priority == priority.value)
            
            # Calcular tamanhos totais
            total_input_size = sum(j.input_size for j in self._jobs.values())
            total_output_size = sum(j.output_size for j in self._jobs.values())
            
            # Calcular taxa de sucesso
            completed = by_status.get(JobStatus.COMPLETED.value, 0)
            failed = by_status.get(JobStatus.FAILED.value, 0)
            success_rate = (completed / (completed + failed) * 100) if (completed + failed) > 0 else 0
            
            return {
                "total": total,
                "active": len(self._active_jobs),
                "paused": self._paused,
                "max_concurrent": self._max_concurrent_jobs,
                "by_status": by_status,
                "by_priority": by_priority,
                "total_input_size_gb": total_input_size / (1024 ** 3),
                "total_output_size_gb": total_output_size / (1024 ** 3),
                "success_rate": success_rate
            }
    
    def get_queue_length(self) -> int:
        """
        Obtém o tamanho da fila (jobs pendentes/queued).
        
        Returns:
            int: Número de jobs na fila
        """
        with self._lock:
            return sum(1 for j in self._jobs.values() if j.status in [JobStatus.QUEUED.value, JobStatus.PENDING.value])
    
    # =========================================================================
    # CALLBACKS
    # =========================================================================
    
    def register_status_callback(
        self,
        callback: Callable[[str, str, str], None],
        job_id: Optional[str] = None
    ) -> None:
        """
        Registra um callback para mudanças de status.
        
        Args:
            callback: Função callback(job_id, old_status, new_status)
            job_id: ID do job específico (opcional, se None é global)
        """
        with self._lock:
            if job_id:
                if job_id not in self._status_callbacks:
                    self._status_callbacks[job_id] = []
                self._status_callbacks[job_id].append(callback)
            else:
                self._global_status_callbacks.append(callback)
    
    def register_progress_callback(
        self,
        callback: Callable[[str, float], None],
        job_id: Optional[str] = None
    ) -> None:
        """
        Registra um callback para atualizações de progresso.
        
        Args:
            callback: Função callback(job_id, progress)
            job_id: ID do job específico (opcional, se None é global)
        """
        with self._lock:
            if job_id:
                if job_id not in self._progress_callbacks:
                    self._progress_callbacks[job_id] = []
                self._progress_callbacks[job_id].append(callback)
            else:
                self._global_progress_callbacks.append(callback)
    
    def _trigger_status_callbacks(
        self,
        job_id: str,
        old_status: str,
        new_status: str
    ) -> None:
        """Aciona callbacks de status para um job."""
        callbacks = self._status_callbacks.get(job_id, []) + self._global_status_callbacks
        
        for callback in callbacks:
            try:
                callback(job_id, old_status, new_status)
            except Exception as e:
                print(f"Erro ao executar callback de status: {e}")
    
    def _trigger_progress_callbacks(self, job_id: str, progress: float) -> None:
        """Aciona callbacks de progresso para um job."""
        callbacks = self._progress_callbacks.get(job_id, []) + self._global_progress_callbacks
        
        for callback in callbacks:
            try:
                callback(job_id, progress)
            except Exception as e:
                print(f"Erro ao executar callback de progresso: {e}")
    
    def update_progress(self, job_id: str, progress: float) -> bool:
        """
        Atualiza o progresso de um job.
        
        Args:
            job_id: ID do job
            progress: Progresso (0-100)
        
        Returns:
            bool: True se atualizado com sucesso
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            job.progress = progress
            
            # Atualizar métricas de tempo
            self._update_job_metrics(job)
            
            # Trigger callbacks
            self._trigger_progress_callbacks(job_id, progress)
            
            # Marcar para salvar
            self._pending_save = True
            
            return True
    
    def update_job_status(self, job_id: str, status: JobStatus, **kwargs) -> bool:
        """
        Atualiza o status de um job.
        
        Args:
            job_id: ID do job
            status: Novo status
            **kwargs: Campos adicionais para atualizar
        
        Returns:
            bool: True se atualizado com sucesso
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            old_status = job.status
            
            # Atualizar status
            job.status = status.value
            
            # Atualizar timestamps conforme status
            if status == JobStatus.RUNNING:
                if old_status != JobStatus.RUNNING.value:
                    job.started_at = datetime.now().isoformat()
                    self._active_jobs.add(job_id)
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                job.completed_at = datetime.now().isoformat()
                self._active_jobs.discard(job_id)
                if job_id in self._queue_order:
                    self._queue_order.remove(job_id)
            
            # Atualizar campos adicionais
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            
            # Atualizar métricas
            self._update_job_metrics(job)
            
            # Salvar
            self.save()
            
            # Trigger callbacks
            self._trigger_status_callbacks(job_id, old_status, status.value)
            
            return True
    
    def _update_job_metrics(self, job: QueueJob) -> None:
        """
        Atualiza métricas de tempo e velocidade de um job.
        
        Args:
            job: Job para atualizar métricas
        """
        if not job.started_at:
            return
        
        try:
            started_at = datetime.fromisoformat(job.started_at)
            now = datetime.now()
            elapsed = now - started_at
            elapsed_seconds = elapsed.total_seconds()
            
            # Atualizar tempo decorrido
            job.elapsed_time = self._format_duration(elapsed_seconds)
            
            # Calcular velocidade e ETA
            if job.progress > 0 and elapsed_seconds > 0:
                # Velocidade em %/min
                job.speed = (job.progress / elapsed_seconds) * 60
                
                # ETA
                remaining_percent = 100 - job.progress
                eta_seconds = remaining_percent / (job.progress / elapsed_seconds)
                job.eta = self._format_duration(eta_seconds)
            
            # Calcular razão de compressão
            if job.input_size > 0 and job.output_size > 0:
                job.compression_ratio = job.output_size / job.input_size
                
        except Exception:
            pass
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """
        Formata duração em segundos para HH:MM:SS.
        
        Args:
            seconds: Duração em segundos
        
        Returns:
            str: Duração formatada
        """
        if seconds <= 0:
            return "00:00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _sort_queue_by_priority(self) -> None:
        """Ordena a fila por prioridade (maior prioridade primeiro)."""
        # Obter jobs na fila (apenas queued/pending)
        queue_jobs = [
            (job_id, self._jobs[job_id])
            for job_id in self._queue_order
            if job_id in self._jobs and self._jobs[job_id].status in [JobStatus.QUEUED.value, JobStatus.PENDING.value]
        ]
        
        # Ordenar por prioridade (descendente) e depois por created_at (ascendente)
        queue_jobs.sort(key=lambda x: (-x[1].priority, x[1].created_at))
        
        # Atualizar ordem
        self._queue_order = [job_id for job_id, _ in queue_jobs]
    
    # =========================================================================
    # PERSISTÊNCIA
    # =========================================================================
    
    def save(self) -> bool:
        """
        Salva o estado atual no arquivo JSON.
        
        Returns:
            bool: True se salvo com sucesso
        """
        with self._save_lock:
            try:
                data = {
                    "version": self.VERSION,
                    "schema_version": self.SCHEMA_VERSION,
                    "last_updated": datetime.now().isoformat(),
                    "queue_paused": self._paused,
                    "max_concurrent_jobs": self._max_concurrent_jobs,
                    "jobs": {job_id: job.to_dict() for job_id, job in self._jobs.items()},
                    "queue_order": self._queue_order,
                    "active_jobs": list(self._active_jobs),
                    "history": {
                        "completed": [j.id for j in self._jobs.values() if j.status == JobStatus.COMPLETED.value],
                        "failed": [j.id for j in self._jobs.values() if j.status == JobStatus.FAILED.value],
                        "cancelled": [j.id for j in self._jobs.values() if j.status == JobStatus.CANCELLED.value]
                    }
                }
                
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self._last_save_time = time.time()
                self._pending_save = False
                
                return True
                
            except Exception as e:
                print(f"Erro ao salvar fila: {e}")
                return False
    
    def load(self) -> Dict[str, Any]:
        """
        Carrega o estado do arquivo JSON.
        
        Returns:
            Dict com dados carregados
        """
        with self._lock:
            if not self.data_file.exists():
                return {}
            
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Verificar versão
                version = data.get("version", "1.0")
                if version != self.VERSION:
                    # Poderia fazer migração aqui
                    print(f"Aviso: Versão do arquivo {version}, versão atual {self.VERSION}")
                
                # Carregar dados
                self._paused = data.get("queue_paused", False)
                self._max_concurrent_jobs = data.get("max_concurrent_jobs", self._max_concurrent_jobs)
                self._queue_order = data.get("queue_order", [])
                self._active_jobs = set(data.get("active_jobs", []))
                
                # Carregar jobs
                jobs_data = data.get("jobs", {})
                self._jobs = {
                    job_id: QueueJob.from_dict(job_data)
                    for job_id, job_data in jobs_data.items()
                }
                
                return data
                
            except Exception as e:
                print(f"Erro ao carregar fila: {e}")
                return {}
    
    def export_to_json(self, filepath: str) -> bool:
        """
        Exporta a fila para um arquivo JSON.
        
        Args:
            filepath: Caminho do arquivo de exportação
        
        Returns:
            bool: True se exportado com sucesso
        """
        try:
            with self._lock:
                data = {
                    "version": self.VERSION,
                    "exported_at": datetime.now().isoformat(),
                    "jobs": [job.get_details_dict() for job in self._jobs.values()]
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                return True
        except Exception:
            return False
    
    def import_from_json(self, filepath: str) -> int:
        """
        Importa jobs de um arquivo JSON.
        
        Args:
            filepath: Caminho do arquivo de importação
        
        Returns:
            int: Número de jobs importados
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            jobs_data = data.get("jobs", [])
            count = 0
            
            with self._lock:
                for job_data in jobs_data:
                    # Criar novo job com novo ID
                    new_job = QueueJob.from_dict(job_data)
                    new_job.id = str(uuid.uuid4())
                    new_job.status = JobStatus.QUEUED.value
                    new_job.created_at = datetime.now().isoformat()
                    
                    self._jobs[new_job.id] = new_job
                    self._queue_order.append(new_job.id)
                    count += 1
                
                self._sort_queue_by_priority()
                self.save()
            
            return count
            
        except Exception:
            return 0
    
    # =========================================================================
    # MÉTODOS UTILITÁRIOS
    # =========================================================================
    
    def cleanup_history(self, older_than_days: int = 30) -> int:
        """
        Limpa jobs completados/falhados/cancelados mais antigos que X dias.
        
        Args:
            older_than_days: Dias para considerar (padrão: 30)
        
        Returns:
            int: Número de jobs removidos
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=older_than_days)
        to_remove = []
        
        with self._lock:
            for job_id, job in self._jobs.items():
                if job.status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
                    if job.completed_at:
                        try:
                            completed_date = datetime.fromisoformat(job.completed_at)
                            if completed_date < cutoff:
                                to_remove.append(job_id)
                        except Exception:
                            pass
            
            for job_id in to_remove:
                self.remove_job(job_id)
        
        return len(to_remove)
    
    def get_next_pending_job(self) -> Optional[QueueJob]:
        """
        Obtém o próximo job pendente (maior prioridade).
        
        Returns:
            QueueJob ou None se não houver jobs pendentes
        """
        with self._lock:
            for job_id in self._queue_order:
                job = self._jobs.get(job_id)
                if job and job.status in [JobStatus.QUEUED.value, JobStatus.PENDING.value]:
                    return job
            return None
    
    # === Métodos de Compatibilidade com JobManager ===
    
    def get_running_jobs(self) -> List[Dict[str, Any]]:
        """
        Obtém lista de jobs em execução (compatibilidade com JobManager).
        
        Returns:
            Lista de dicionários com informações dos jobs em execução
        """
        with self._lock:
            running = [
                job.to_dict()
                for job in self._jobs.values()
                if job.status == JobStatus.RUNNING.value
            ]
            return running
    
    def get_pending_jobs(self) -> List[Dict[str, Any]]:
        """
        Obtém lista de jobs pendentes (compatibilidade com JobManager).
        
        Returns:
            Lista de dicionários com informações dos jobs pendentes
        """
        with self._lock:
            pending = [
                job.to_dict()
                for job in self._jobs.values()
                if job.status in [JobStatus.PENDING.value, JobStatus.QUEUED.value]
            ]
            return pending
    
    def list_jobs(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista todos os jobs (compatibilidade com JobManager).
        
        Args:
            status_filter: Filtro opcional por status
        
        Returns:
            Lista de dicionários com informações dos jobs
        """
        with self._lock:
            if status_filter:
                jobs = [
                    job.to_dict()
                    for job in self._jobs.values()
                    if job.status == status_filter
                ]
            else:
                jobs = [job.to_dict() for job in self._jobs.values()]
            
            return jobs
    
    def create_job(
        self,
        input_path: str,
        output_path: str,
        profile_id: str,
        profile_name: str
    ) -> str:
        """
        Cria um novo job (compatibilidade com JobManager).
        
        Este método mantém compatibilidade com o antigo JobManager.create_job,
        que recebia profile_id e profile_name separadamente.
        
        Args:
            input_path: Caminho do arquivo de entrada
            output_path: Caminho do arquivo de saída
            profile_id: ID do perfil de encoding
            profile_name: Nome do perfil de encoding
        
        Returns:
            str: ID do job criado
        """
        # Construir objeto de perfil a partir dos parâmetros
        profile = {
            'id': profile_id,
            'name': profile_name
        }
        
        # Usar add_job para criar o job
        job = self.add_job(
            input_path=input_path,
            output_path=output_path,
            profile=profile,
            priority=QueuePriority.NORMAL
        )
        
        return job.id
    
    def add_to_queue(
        self,
        job_id: str,
        input_path: str,
        output_path: str,
        profile: Dict[str, Any],
        priority: QueuePriority = QueuePriority.NORMAL
    ) -> int:
        """
        Adiciona job à fila (compatibilidade com QueueManager).
        
        NOTA: No UnifiedQueueManager, este método é redundante quando usado
        após create_job(), pois add_job() já adiciona o job à fila.
        Este método existe apenas para compatibilidade com código antigo.
        
        Args:
            job_id: ID do job (ignorado, pois job já foi criado)
            input_path: Caminho do arquivo de entrada (ignorado)
            output_path: Caminho do arquivo de saída (ignorado)
            profile: Configurações do perfil (ignorado)
            priority: Prioridade do job (pode atualizar se diferente)
        
        Returns:
            int: Posição do job na fila (1-based)
        """
        with self._lock:
            # Verificar se job existe
            if job_id not in self._jobs:
                # Job não existe, não fazer nada
                return 0
            
            # Atualizar prioridade se fornecida
            job = self._jobs[job_id]
            if priority and job.priority != priority.value:
                job.priority = priority.value
                self._sort_queue_by_priority()
                self.save()
            
            # Retornar posição na fila (1-based)
            try:
                position = self._queue_order.index(job_id) + 1
                return position
            except ValueError:
                return 0
    
    def pop_next_job(self) -> Optional[Dict[str, Any]]:
        """
        Retorna e remove o próximo job da fila (compatibilidade com QueueManager).
        
        Returns:
            Dict com informações do próximo job ou None se fila vazia/pausada
        """
        with self._lock:
            if self._paused or not self._queue_order:
                return None
            
            # Encontrar próximo job que não está em execução
            for job_id in self._queue_order:
                job = self._jobs.get(job_id)
                if job and job.status in [JobStatus.QUEUED.value, JobStatus.PENDING.value]:
                    # Remover da fila
                    self._queue_order.remove(job_id)
                    self.save()
                    
                    # Retornar como dicionário para compatibilidade
                    return {
                        'job_id': job.id,
                        'input_path': job.input_path,
                        'output_path': job.output_path,
                        'profile': job.profile,
                        'priority': job.priority,
                        'added_at': job.created_at,
                        'started_at': job.started_at
                    }
            
            return None
    
    def get_next_job(self) -> Optional[Dict[str, Any]]:
        """
        Retorna o próximo job da fila sem remover (compatibilidade com QueueManager).
        
        Returns:
            Dict com informações do próximo job ou None se fila vazia/pausada
        """
        with self._lock:
            if self._paused or not self._queue_order:
                return None
            
            # Encontrar próximo job que não está em execução
            for job_id in self._queue_order:
                job = self._jobs.get(job_id)
                if job and job.status in [JobStatus.QUEUED.value, JobStatus.PENDING.value]:
                    # Retornar como dicionário para compatibilidade
                    return {
                        'job_id': job.id,
                        'input_path': job.input_path,
                        'output_path': job.output_path,
                        'profile': job.profile,
                        'priority': job.priority,
                        'added_at': job.created_at,
                        'started_at': job.started_at
                    }
            
            return None
    
    def mark_job_started(self, job_id: str) -> bool:
        """
        Marca job como iniciado (compatibilidade com QueueManager).
        
        Args:
            job_id: ID do job
        
        Returns:
            bool: True se marcado com sucesso
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            job.started_at = datetime.now().isoformat()
            self.save()
            return True
    
    def remove_from_queue(self, job_id: str) -> bool:
        """
        Remove job da fila (compatibilidade com QueueManager).
        
        Args:
            job_id: ID do job para remover
        
        Returns:
            bool: True se removido com sucesso
        """
        return self.remove_job(job_id)
    
    def pause(self) -> bool:
        """
        Pausa a fila (compatibilidade com QueueManager).
        
        Returns:
            bool: True se pausado com sucesso
        """
        return self.pause_queue()
    
    def resume(self) -> bool:
        """
        Retoma a fila (compatibilidade com QueueManager).
        
        Returns:
            bool: True se retomado com sucesso
        """
        return self.resume_queue()
    
    def is_paused(self) -> bool:
        """
        Verifica se a fila está pausada (compatibilidade com QueueManager).
        
        Returns:
            bool: True se pausada
        """
        return self.is_queue_paused()
