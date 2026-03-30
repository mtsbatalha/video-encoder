from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, MofNCompleteColumn, SpinnerColumn, TaskID
from typing import Optional, Dict, Any, cast
import threading


class ProgressDisplay:
    """Exibição de progresso com Rich."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._progress: Optional[Progress] = None
        self._task_id: Optional[TaskID] = None
        self._lock = threading.Lock()
        self._hw_stats: Dict[str, Any] = {}
    
    def start(self, total: float = 100.0, description: str = "Encoding"):
        """Inicia barra de progresso."""
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=self.console,
            expand=True
        )
        
        with self._lock:
            task_id = self._progress.add_task(description, total=total)
            self._task_id = cast(TaskID, task_id)
            self._progress.start()
    
    def update(self, completed: float, description: Optional[str] = None):
        """Atualiza progresso."""
        with self._lock:
            if self._progress and self._task_id is not None:
                self._progress.update(self._task_id, completed=completed)  # type: ignore[arg-type]
                if description:
                    self._progress.update(self._task_id, description=description)  # type: ignore[arg-type]
    
    def stop(self):
        """Para barra de progresso."""
        with self._lock:
            if self._progress:
                self._progress.stop()
                self._progress = None
                self._task_id = None
    
    def set_hw_stats(self, stats: Dict[str, Any]):
        """Atualiza stats de hardware para exibição."""
        with self._lock:
            self._hw_stats = stats
    
    def get_resource_display(self) -> str:
        """Retorna string de recursos."""
        gpu_util = self._hw_stats.get('gpu_util', 0)
        gpu_temp = self._hw_stats.get('gpu_temperature', 0)
        gpu_mem = self._hw_stats.get('gpu_memory_used', 0)
        cpu_util = self._hw_stats.get('cpu_util', 0)
        
        gpu_bar = '█' * int(gpu_util / 10) + '░' * (10 - int(gpu_util / 10))
        cpu_bar = '█' * int(cpu_util / 10) + '░' * (10 - int(cpu_util / 10))
        
        temp_color = "red" if gpu_temp > 80 else "yellow" if gpu_temp > 60 else "green"
        
        return (
            f"[green]GPU:[/green] {gpu_bar} {gpu_util}%  "
            f"[{temp_color}]{gpu_temp}°C[/{temp_color}]  "
            f"[yellow]{gpu_mem}MB[/yellow]  "
            f"[blue]CPU:[/blue] {cpu_bar} {cpu_util}%"
        )


class MultiJobProgress:
    """Gerenciador de múltiplas barras de progresso."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._progress: Optional[Progress] = None
        self._tasks: Dict[str, TaskID] = {}
        self._lock = threading.Lock()
    
    def start(self):
        """Inicia display de progresso."""
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
            expand=True
        )
        self._progress.start()
    
    def add_job(self, job_id: str, description: str, total: float = 100.0):
        """Adiciona job ao display."""
        with self._lock:
            if self._progress:
                task_id = self._progress.add_task(description, total=total)
                self._tasks[job_id] = cast(TaskID, task_id)
    
    def update_job(self, job_id: str, completed: float, description: Optional[str] = None):
        """Atualiza progresso do job."""
        with self._lock:
            if self._progress and job_id in self._tasks:
                task_id = self._tasks[job_id]
                self._progress.update(task_id, completed=completed)  # type: ignore[arg-type]
                if description:
                    self._progress.update(task_id, description=description)  # type: ignore[arg-type]
    
    def remove_job(self, job_id: str):
        """Remove job do display."""
        with self._lock:
            if job_id in self._tasks:
                task_id = self._tasks[job_id]
                if self._progress:
                    self._progress.remove_task(task_id)  # type: ignore[arg-type]
                del self._tasks[job_id]
    
    def stop(self):
        """Para display de progresso."""
        with self._lock:
            if self._progress:
                self._progress.stop()
                self._progress = None
                self._tasks.clear()
