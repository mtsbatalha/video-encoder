import json
import threading
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class QueuePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class QueueManager:
    """Gerenciador de fila de encoding com persistência."""
    
    def __init__(self, jobs_dir: Optional[str] = None):
        self.jobs_dir = Path(jobs_dir) if jobs_dir else Path(__file__).parent.parent.parent / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self._queue_file = self.jobs_dir / "queue.json"
        self._queue: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._paused = False
        self.load()
    
    def load(self) -> List[Dict[str, Any]]:
        """Carrega fila do arquivo."""
        if self._queue_file.exists():
            try:
                with open(self._queue_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._queue = data.get('queue', [])
                    self._paused = data.get('paused', False)
            except Exception:
                self._queue = []
        return self._queue.copy()
    
    def save(self) -> bool:
        """Salva fila no arquivo."""
        try:
            with open(self._queue_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'queue': self._queue,
                    'paused': self._paused,
                    'updated_at': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def add_to_queue(
        self,
        job_id: str,
        input_path: str,
        output_path: str,
        profile: Dict[str, Any],
        priority: QueuePriority = QueuePriority.NORMAL
    ) -> int:
        """Adiciona job à fila."""
        with self._lock:
            queue_item = {
                "job_id": job_id,
                "input_path": str(input_path),
                "output_path": str(output_path),
                "profile": profile,
                "priority": priority.value,
                "added_at": datetime.now().isoformat(),
                "started_at": None
            }
            
            self._queue.append(queue_item)
            self._queue.sort(key=lambda x: (-x['priority'], x['added_at']))
            self.save()
            
            return len(self._queue)
    
    def get_next_job(self) -> Optional[Dict[str, Any]]:
        """Retorna próximo job da fila (sem remover)."""
        if self._paused or not self._queue:
            return None
        
        with self._lock:
            for item in self._queue:
                if not item.get('started_at'):
                    return item.copy()
            return None
    
    def pop_next_job(self) -> Optional[Dict[str, Any]]:
        """Retorna e remove próximo job da fila."""
        if self._paused or not self._queue:
            return None
        
        with self._lock:
            for i, item in enumerate(self._queue):
                if not item.get('started_at'):
                    removed = self._queue.pop(i)
                    self.save()
                    return removed
            return None
    
    def mark_job_started(self, job_id: str) -> bool:
        """Marca job como iniciado."""
        with self._lock:
            for item in self._queue:
                if item['job_id'] == job_id:
                    item['started_at'] = datetime.now().isoformat()
                    self.save()
                    return True
        return False
    
    def remove_from_queue(self, job_id: str) -> bool:
        """Remove job da fila."""
        with self._lock:
            for i, item in enumerate(self._queue):
                if item['job_id'] == job_id:
                    self._queue.pop(i)
                    self.save()
                    return True
        return False
    
    def reorder_job(self, job_id: str, new_position: int) -> bool:
        """Reordena job para nova posição (prioridade manual)."""
        with self._lock:
            for i, item in enumerate(self._queue):
                if item['job_id'] == job_id:
                    queue_item = self._queue.pop(i)
                    
                    new_position = max(0, min(new_position, len(self._queue)))
                    self._queue.insert(new_position, queue_item)
                    self.save()
                    return True
        return False
    
    def set_job_priority(self, job_id: str, priority: QueuePriority) -> bool:
        """Define prioridade do job e reordena fila."""
        with self._lock:
            for item in self._queue:
                if item['job_id'] == job_id:
                    item['priority'] = priority.value
                    self._queue.sort(key=lambda x: (-x['priority'], x['added_at']))
                    self.save()
                    return True
        return False
    
    def pause(self) -> bool:
        """Pausa fila."""
        with self._lock:
            self._paused = True
            self.save()
            return True
    
    def resume(self) -> bool:
        """Retoma fila."""
        with self._lock:
            self._paused = False
            self.save()
            return True
    
    def is_paused(self) -> bool:
        """Verifica se fila está pausada."""
        return self._paused
    
    def get_queue_length(self) -> int:
        """Retorna tamanho da fila."""
        return len(self._queue)
    
    def list_queue(self) -> List[Dict[str, Any]]:
        """Retorna lista completa da fila."""
        with self._lock:
            return [item.copy() for item in self._queue]
    
    def clear_queue(self) -> int:
        """Limpa fila e retorna número de itens removidos."""
        with self._lock:
            count = len(self._queue)
            self._queue = []
            self.save()
            return count
    
    def get_queue_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas da fila."""
        with self._lock:
            total = len(self._queue)
            by_priority = {
                "critical": sum(1 for i in self._queue if i['priority'] == QueuePriority.CRITICAL.value),
                "high": sum(1 for i in self._queue if i['priority'] == QueuePriority.HIGH.value),
                "normal": sum(1 for i in self._queue if i['priority'] == QueuePriority.NORMAL.value),
                "low": sum(1 for i in self._queue if i['priority'] == QueuePriority.LOW.value)
            }
            
            return {
                "total": total,
                "paused": self._paused,
                "by_priority": by_priority
            }
