import subprocess
import threading
import time
from typing import Optional, Callable
from dataclasses import dataclass


@dataclass
class HardwareStats:
    gpu_util: int = 0
    gpu_memory_used: int = 0
    gpu_memory_total: int = 0
    gpu_temperature: int = 0
    cpu_util: float = 0.0
    cpu_memory_used: int = 0
    cpu_memory_total: int = 0
    disk_free_gb: float = 0.0


class HardwareMonitor:
    """Monitoramento de hardware (GPU, CPU, disco) em tempo real."""
    
    def __init__(self, monitoring_interval: float = 1.0):
        self.interval = monitoring_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._callbacks: list[Callable[[HardwareStats], None]] = []
        self._stats = HardwareStats()
        self._psutil_available = False
        
        import importlib.util
        if importlib.util.find_spec('psutil') is not None:
            self._psutil_available = True
    
    def start(self):
        """Inicia monitoramento em thread separada."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Para monitoramento."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
    
    def add_callback(self, callback: Callable[[HardwareStats], None]):
        """Adiciona callback para atualizações de stats."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[HardwareStats], None]):
        """Remove callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def get_stats(self) -> HardwareStats:
        """Retorna stats atuais."""
        with self._lock:
            return self._stats
    
    def _monitor_loop(self):
        """Loop principal de monitoramento."""
        while self._running:
            self._update_gpu_stats()
            self._update_cpu_stats()
            self._update_disk_stats()
            
            with self._lock:
                stats_copy = HardwareStats(
                    gpu_util=self._stats.gpu_util,
                    gpu_memory_used=self._stats.gpu_memory_used,
                    gpu_memory_total=self._stats.gpu_memory_total,
                    gpu_temperature=self._stats.gpu_temperature,
                    cpu_util=self._stats.cpu_util,
                    cpu_memory_used=self._stats.cpu_memory_used,
                    cpu_memory_total=self._stats.cpu_memory_total,
                    disk_free_gb=self._stats.disk_free_gb
                )
            
            for callback in self._callbacks:
                try:
                    callback(stats_copy)
                except Exception:
                    pass
            
            time.sleep(self.interval)
    
    def _update_gpu_stats(self):
        """Atualiza stats da GPU via nvidia-smi."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,memory.total,memory.used,temperature.gpu',
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                parts = result.stdout.strip().split(',')
                if len(parts) >= 4:
                    with self._lock:
                        self._stats.gpu_util = int(parts[0].strip())
                        self._stats.gpu_memory_total = int(parts[1].strip())
                        self._stats.gpu_memory_used = int(parts[2].strip())
                        self._stats.gpu_temperature = int(parts[3].strip())
        except Exception:
            pass
    
    def _update_cpu_stats(self):
        """Atualiza stats da CPU via psutil."""
        if not self._psutil_available:
            return
        
        try:
            import psutil
            
            with self._lock:
                self._stats.cpu_util = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                self._stats.cpu_memory_used = memory.used
                self._stats.cpu_memory_total = memory.total
        except Exception:
            pass
    
    def _update_disk_stats(self, path: str = 'C:'):
        """Atualiza stats do disco."""
        if not self._psutil_available:
            return
        
        try:
            import psutil
            
            disk = psutil.disk_usage(path)
            with self._lock:
                self._stats.disk_free_gb = disk.free / (1024 ** 3)
        except Exception:
            pass
    
    def is_gpu_overheating(self, threshold: int = 85) -> bool:
        """Verifica se GPU está superaquecendo."""
        with self._lock:
            return self._stats.gpu_temperature >= threshold
    
    def is_gpu_memory_high(self, threshold_percent: int = 90) -> bool:
        """Verifica se uso de memória da GPU está alto."""
        with self._lock:
            if self._stats.gpu_memory_total == 0:
                return False
            return (self._stats.gpu_memory_used / self._stats.gpu_memory_total) * 100 >= threshold_percent
    
    def has_enough_disk_space(self, required_gb: float) -> bool:
        """Verifica se há espaço em disco suficiente."""
        with self._lock:
            return self._stats.disk_free_gb >= required_gb
