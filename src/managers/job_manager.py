import json
import uuid
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class Job:
    id: str
    input_path: str
    output_path: str
    profile_id: str
    profile_name: str
    status: str
    progress: float
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    input_size: int
    output_size: int
    retry_count: int


class JobManager:
    """Gerenciador de jobs de encoding."""
    
    def __init__(self, jobs_dir: Optional[str] = None):
        self.jobs_dir = Path(jobs_dir) if jobs_dir else Path(__file__).parent.parent.parent / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self._jobs_file = self.jobs_dir / "jobs.json"
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = __import__('threading').Lock()
        self._status_callbacks: Dict[str, List[callable]] = {}  # Callbacks por job_id
        self.load()
    
    def load(self) -> Dict[str, Dict[str, Any]]:
        """Carrega jobs do arquivo."""
        if self._jobs_file.exists():
            try:
                with open(self._jobs_file, 'r', encoding='utf-8') as f:
                    self._jobs = json.load(f)
            except Exception:
                self._jobs = {}
        return self._jobs.copy()
    
    def save(self) -> bool:
        """Salva jobs no arquivo."""
        try:
            with open(self._jobs_file, 'w', encoding='utf-8') as f:
                json.dump(self._jobs, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def create_job(
        self,
        input_path: str,
        output_path: str,
        profile_id: str,
        profile_name: str
    ) -> str:
        """Cria novo job."""
        job_id = str(uuid.uuid4())
        
        job = {
            "id": job_id,
            "input_path": str(input_path),
            "output_path": str(output_path),
            "profile_id": profile_id,
            "profile_name": profile_name,
            "status": JobStatus.PENDING.value,
            "progress": 0.0,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "input_size": 0,
            "output_size": 0,
            "retry_count": 0
        }
        
        with self._lock:
            self._jobs[job_id] = job
            self.save()
        
        return job_id
    
    def register_status_callback(self, job_id: str, callback: callable) -> None:
        """Registra um callback para quando o status do job mudar."""
        if job_id not in self._status_callbacks:
            self._status_callbacks[job_id] = []
        self._status_callbacks[job_id].append(callback)
    
    def _trigger_callbacks(self, job_id: str, old_status: str, new_status: str) -> None:
        """Aciona callbacks registrados para mudança de status."""
        if job_id in self._status_callbacks:
            for callback in self._status_callbacks[job_id]:
                try:
                    callback(job_id, old_status, new_status)
                except Exception as e:
                    print(f"Erro ao executar callback para job {job_id}: {e}")
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Obtém job por ID."""
        return self._jobs.get(job_id)
    
    def update_job_status(self, job_id: str, status: JobStatus, **kwargs) -> bool:
        """Atualiza status do job."""
        with self._lock:
            if job_id not in self._jobs:
                return False
            
            old_status = self._jobs[job_id]["status"]
            
            self._jobs[job_id]["status"] = status.value
            
            if status == JobStatus.RUNNING:
                self._jobs[job_id]["started_at"] = datetime.now().isoformat()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                self._jobs[job_id]["completed_at"] = datetime.now().isoformat()
            
            for key, value in kwargs.items():
                self._jobs[job_id][key] = value
            
            self.save()
            
            # Aciona callbacks após atualização
            self._trigger_callbacks(job_id, old_status, status.value)
            
            return True
    
    def update_progress(self, job_id: str, progress: float) -> bool:
        """Atualiza progresso do job."""
        with self._lock:
            if job_id not in self._jobs:
                return False
            self._jobs[job_id]["progress"] = progress
            self.save()
            return True
    
    def increment_retry(self, job_id: str) -> int:
        """Incrementa contador de retry e retorna novo valor."""
        with self._lock:
            if job_id not in self._jobs:
                return 0
            self._jobs[job_id]["retry_count"] = self._jobs[job_id].get("retry_count", 0) + 1
            self.save()
            return self._jobs[job_id]["retry_count"]
    
    def delete_job(self, job_id: str) -> bool:
        """Exclui job."""
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                self.save()
                return True
        return False
    
    def list_jobs(self, status: Optional[JobStatus] = None) -> List[Dict[str, Any]]:
        """Retorna lista de jobs, opcionalmente filtrada por status."""
        with self._lock:
            if status:
                return [
                    job.copy() for job in self._jobs.values()
                    if job["status"] == status.value
                ]
            return [job.copy() for job in self._jobs.values()]
    
    def get_pending_jobs(self) -> List[Dict[str, Any]]:
        """Retorna jobs pendentes."""
        return self.list_jobs(JobStatus.PENDING)
    
    def get_running_jobs(self) -> List[Dict[str, Any]]:
        """Retorna jobs em execução."""
        return self.list_jobs(JobStatus.RUNNING)
    
    def get_completed_jobs(self) -> List[Dict[str, Any]]:
        """Retorna jobs completados."""
        return self.list_jobs(JobStatus.COMPLETED)
    
    def get_failed_jobs(self) -> List[Dict[str, Any]]:
        """Retorna jobs falhados."""
        return self.list_jobs(JobStatus.FAILED)
    
    def clear_completed(self, older_than_days: int = 7) -> int:
        """Limpa jobs completados mais antigos que X dias."""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=older_than_days)
        to_delete = []
        
        for job_id, job in self._jobs.items():
            if job["status"] == JobStatus.COMPLETED.value:
                completed_at = job.get("completed_at")
                if completed_at:
                    try:
                        completed_date = datetime.fromisoformat(completed_at)
                        if completed_date < cutoff:
                            to_delete.append(job_id)
                    except Exception:
                        pass
        
        with self._lock:
            for job_id in to_delete:
                del self._jobs[job_id]
            self.save()
        
        return len(to_delete)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de jobs."""
        total = len(self._jobs)
        completed = len(self.get_completed_jobs())
        failed = len(self.get_failed_jobs())
        pending = len(self.get_pending_jobs())
        running = len(self.get_running_jobs())
        
        total_input_size = sum(job.get("input_size", 0) for job in self._jobs.values())
        total_output_size = sum(job.get("output_size", 0) for job in self._jobs.values())
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "running": running,
            "success_rate": (completed / total * 100) if total > 0 else 0,
            "total_input_size_gb": total_input_size / (1024 ** 3),
            "total_output_size_gb": total_output_size / (1024 ** 3)
        }
