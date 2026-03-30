"""Monitor de encoding em tempo real com interface completa."""

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from typing import Optional, Dict, Any
import threading
import time
import re


class RealTimeEncodingMonitor:
    """Monitor de encoding em tempo real com interface completa."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._lock = threading.Lock()
        self._running = False
        self._live: Optional[Live] = None
        
        self._hw_stats: Dict[str, Any] = {
            'gpu_util': 0,
            'gpu_temperature': 0,
            'gpu_memory_used': 0,
            'gpu_memory_total': 0,
            'cpu_util': 0
        }
        
        self._encoding_stats: Dict[str, Any] = {
            'fps': 0,
            'speed': 0,
            'bitrate': 0
        }
        
        self._progress: float = 0
        self._description: str = "Encoding"
        self._time_remaining: str = "--:--:--"
        self._status: str = "Aguardando..."
        self._start_time: float = 0
        self._total_duration: float = 0
        self._current_time: float = 0
        self._input_file: str = ""
        self._output_file: str = ""
    
    def start(self, description: str = "Encoding", total_duration: float = 0, 
              input_file: str = "", output_file: str = ""):
        """Inicia monitor em tempo real."""
        self._running = True
        self._description = description
        self._total_duration = total_duration
        self._start_time = time.time()
        self._input_file = input_file
        self._output_file = output_file
        
        self._live = Live(
            self._generate_display(),
            console=self.console,
            refresh_per_second=2,
            screen=False
        )
        self._live.start()
    
    def stop(self):
        """Para monitor."""
        self._running = False
        if self._live:
            self._live.stop()
            self._live = None
    
    def update_progress(self, progress: float, current_time: float = 0):
        """Atualiza progresso."""
        with self._lock:
            self._progress = progress
            self._current_time = current_time
            if self._total_duration > 0 and current_time > 0:
                elapsed = time.time() - self._start_time
                if progress > 0:
                    estimated_total = elapsed / (progress / 100)
                    remaining = estimated_total - elapsed
                    self._time_remaining = time.strftime('%H:%M:%S', time.gmtime(max(0, remaining)))
    
    def update_hw_stats(self, stats: Dict[str, Any]):
        """Atualiza stats de hardware."""
        with self._lock:
            self._hw_stats.update(stats)
    
    def update_encoding_stats(self, fps: float = None, speed: float = None, bitrate: float = None):
        """Atualiza estatísticas de encoding."""
        with self._lock:
            if fps is not None:
                self._encoding_stats['fps'] = fps
            if speed is not None:
                self._encoding_stats['speed'] = speed
            if bitrate is not None:
                self._encoding_stats['bitrate'] = bitrate
    
    def update_status(self, status: str):
        """Atualiza status."""
        with self._lock:
            self._status = status
    
    def _generate_display(self) -> Panel:
        """Gera display completo."""
        with self._lock:
            # Tabela de estatísticas de encoding
            encoding_table = Table(show_header=False, box=None, padding=(0, 1))
            encoding_table.add_column("Label", style="cyan", width=15)
            encoding_table.add_column("Value", style="white")
            
            fps_val = f"{self._encoding_stats['fps']:.1f}" if self._encoding_stats['fps'] > 0 else "--"
            speed_val = f"{self._encoding_stats['speed']:.2f}x" if self._encoding_stats['speed'] > 0 else "--"
            bitrate_val = f"{self._encoding_stats['bitrate']:.0f} Kbps" if self._encoding_stats['bitrate'] > 0 else "--"
            
            encoding_table.add_row("FPS:", fps_val)
            encoding_table.add_row("Speed:", speed_val)
            encoding_table.add_row("Bitrate:", bitrate_val)
            encoding_table.add_row("Progresso:", f"{self._progress:.1f}%")
            encoding_table.add_row("Tempo Restante:", self._time_remaining)
            
            # Barra de progresso
            progress_bar = self._generate_progress_bar(self._progress)
            
            # Tabela de hardware
            hw_table = Table(show_header=False, box=None, padding=(0, 1))
            hw_table.add_column("Component", style="bold", width=10)
            hw_table.add_column("Usage", style="white")
            hw_table.add_column("Temp", style="white")
            
            gpu_util = self._hw_stats.get('gpu_util', 0)
            gpu_temp = self._hw_stats.get('gpu_temperature', 0)
            gpu_mem = self._hw_stats.get('gpu_memory_used', 0)
            gpu_mem_total = self._hw_stats.get('gpu_memory_total', 0)
            cpu_util = self._hw_stats.get('cpu_util', 0)
            
            gpu_mem_display = f"{gpu_mem}MB" if gpu_mem > 0 else "--"
            if gpu_mem_total > 0:
                gpu_mem_display += f"/{gpu_mem_total}MB"
            
            temp_color = "red" if gpu_temp > 80 else "yellow" if gpu_temp > 60 else "green"
            
            hw_table.add_row(
                "GPU:",
                f"[green]{'█' * int(gpu_util / 10)}{'░' * (10 - int(gpu_util / 10))}[/green] {gpu_util}%",
                f"[{temp_color}]{gpu_temp}°C[/{temp_color}]"
            )
            hw_table.add_row(
                "VRAM:",
                f"[yellow]{gpu_mem_display}[/yellow]",
                ""
            )
            hw_table.add_row(
                "CPU:",
                f"[blue]{'█' * int(cpu_util / 10)}{'░' * (10 - int(cpu_util / 10))}[/blue] {cpu_util}%",
                ""
            )
            
            # Informações dos arquivos
            files_info = ""
            if self._input_file:
                files_info += f"[dim]Input: {self._input_file}[/dim]\n"
            if self._output_file:
                files_info += f"[dim]Output: {self._output_file}[/dim]"
            
            # Layout principal
            content = f"""[bold white]{self._description}[/bold white]
[dim]{self._status}[/dim]

{progress_bar}

[bold cyan]⚡ Encoding Stats:[/bold cyan]
{encoding_table}

[bold green]🖥️  Hardware:[/bold green]
{hw_table}

{files_info}
"""
            
            return Panel(content, border_style="magenta", title="🎬 NVENC Encoder - Tempo Real")
    
    def _generate_progress_bar(self, percent: float, width: int = 50) -> str:
        """Gera barra de progresso ASCII."""
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[magenta][{bar}][/magenta] {percent:.1f}%"


class FFmpegProgressParser:
    """Parser para extrair estatísticas do output do FFmpeg."""
    
    def __init__(self):
        self._fps_pattern = re.compile(r'fps=(\d+\.?\d*)')
        self._speed_pattern = re.compile(r'speed=(\d+\.?\d*)x')
        self._bitrate_pattern = re.compile(r'bitrate=(\d+\.?\d*)kbits/s')
        self._time_pattern = re.compile(r'time=(\d+):(\d+):(\d+)\.(\d+)')
        self._frame_pattern = re.compile(r'frame=\s*(\d+)')
        self._duration_pattern = re.compile(r'Duration:\s*(\d+):(\d+):(\d+)\.(\d+)')
        
        self._total_frames = 0
        self._duration_seconds = 0
    
    def set_duration(self, duration_seconds: float):
        """Define duração total do vídeo."""
        self._duration_seconds = duration_seconds
    
    def parse_line(self, line: str) -> Dict[str, Any]:
        """Extrai estatísticas de uma linha de output."""
        stats = {}
        
        fps_match = self._fps_pattern.search(line)
        if fps_match:
            stats['fps'] = float(fps_match.group(1))
        
        speed_match = self._speed_pattern.search(line)
        if speed_match:
            stats['speed'] = float(speed_match.group(1))
        
        bitrate_match = self._bitrate_pattern.search(line)
        if bitrate_match:
            stats['bitrate'] = float(bitrate_match.group(1))
        
        time_match = self._time_pattern.search(line)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = int(time_match.group(3))
            decimals = int(time_match.group(4))
            current_seconds = hours * 3600 + minutes * 60 + seconds + decimals / 100
            stats['current_time'] = current_seconds
            
            if self._duration_seconds > 0:
                stats['progress'] = (current_seconds / self._duration_seconds) * 100
        
        frame_match = self._frame_pattern.search(line)
        if frame_match:
            stats['frame'] = int(frame_match.group(1))
        
        return stats
    
    def parse_duration(self, output: str) -> float:
        """Extrai duração total do vídeo."""
        match = self._duration_pattern.search(output)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            decimals = int(match.group(4))
            return hours * 3600 + minutes * 60 + seconds + decimals / 100
        return 0
