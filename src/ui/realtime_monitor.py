"""Monitor de encoding em tempo real com interface completa."""

from rich.console import Console
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from typing import Optional, Dict, Any, List
import threading
import time
import re


def format_size(size_mb: float) -> str:
    """Formata tamanho em GB, MB ou KB dependendo do valor.
    
    Args:
        size_mb: Tamanho em megabytes.
    
    Returns:
        String formatada com unidade apropriada.
    """
    if size_mb <= 0:
        return "--"
    
    # Converte para bytes para facilitar cálculo
    size_bytes = size_mb * 1024 * 1024
    
    if size_bytes >= 1024 * 1024 * 1024:  # >= 1 GB
        size_gb = size_bytes / (1024 * 1024 * 1024)
        return f"{size_gb:.2f} GB"
    elif size_bytes >= 1024 * 1024:  # >= 1 MB
        return f"{size_mb:.1f} MB"
    else:  # < 1 MB
        size_kb = size_bytes / (1024 * 1024) * 1024
        return f"{size_kb:.1f} KB"


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
        
        # Informações detalhadas de mídia (entrada vs saída)
        self._input_media_info: Dict[str, Any] = {}
        self._output_media_info: Dict[str, Any] = {}
        self._transcode_status: Dict[str, str] = {}  # 'video', 'audio', 'subtitle'
    
    def start(self, description: str = "Encoding", total_duration: float = 0,
              input_file: str = "", output_file: str = "",
              input_media_info: Optional[Dict[str, Any]] = None,
              profile: Optional[Dict[str, Any]] = None):
        """Inicia monitor em tempo real."""
        self._running = True
        self._description = description
        self._total_duration = total_duration
        self._start_time = time.time()
        self._input_file = input_file
        self._output_file = output_file
        
        # Processa informações de mídia de entrada
        if input_media_info:
            self._input_media_info = self._process_input_media_info(input_media_info)
            self._output_media_info = self._generate_output_media_info(profile or {})
            self._transcode_status = self._determine_transcode_status(profile or {})

        self._live = Live(
            self._generate_display(),
            console=self.console,
            refresh_per_second=2,
            screen=False
        )
        self._live.start()

        self._refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self._refresh_thread.start()

    def _refresh_loop(self):
        """Atualiza o Live display periodicamente."""
        while self._running and self._live:
            try:
                self._live.update(self._generate_display())
            except Exception:
                pass
            time.sleep(0.5)

    def stop(self):
        """Para monitor."""
        self._running = False
        # Garante que o status esteja como finalizado antes de parar
        with self._lock:
            if self._progress >= 100.0:
                self._status = "Finalizado"
        if self._live:
            try:
                self._live.stop()
            except Exception:
                pass
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
            
            # Quando o progresso atinge 100%, atualiza o status automaticamente
            if progress >= 100.0:
                self._status = "Finalizado"
    
    def update_hw_stats(self, stats: Dict[str, Any]):
        """Atualiza stats de hardware."""
        with self._lock:
            self._hw_stats.update(stats)
    
    def update_encoding_stats(self, fps: float = None, speed: float = None, bitrate: float = None):
        """Atualiza estatísticas de encoding."""
        with self._lock:
            if fps is not None:
                print(f"🎯 MONITOR: Recebeu FPS={fps}, atualizando de {self._encoding_stats['fps']} para {fps}")
                self._encoding_stats['fps'] = fps
            if speed is not None:
                print(f"🎯 MONITOR: Recebeu Speed={speed}x, atualizando de {self._encoding_stats['speed']} para {speed}")
                self._encoding_stats['speed'] = speed
            if bitrate is not None:
                print(f"🎯 MONITOR: Recebeu Bitrate={bitrate} Kbps, atualizando de {self._encoding_stats['bitrate']} para {bitrate}")
                self._encoding_stats['bitrate'] = bitrate
            
            # Log do estado atual
            if fps is not None or speed is not None or bitrate is not None:
                print(f"📊 MONITOR: Estado atual - FPS={self._encoding_stats['fps']}, Speed={self._encoding_stats['speed']}x, Bitrate={self._encoding_stats['bitrate']} Kbps")
    
    def update_status(self, status: str):
        """Atualiza status."""
        with self._lock:
            self._status = status
    
    def _process_input_media_info(self, media_info: Dict[str, Any]) -> Dict[str, Any]:
        """Processa informações de mídia de entrada."""
        streams = media_info.get('streams', [])
        format_info = media_info.get('format', {})
        
        video_streams = [s for s in streams if s.get('codec_type') == 'video']
        audio_streams = [s for s in streams if s.get('codec_type') == 'audio']
        subtitle_streams = [s for s in streams if s.get('codec_type') == 'subtitle']
        
        # Calcula tamanho em MB
        size_bytes = float(format_info.get('size', 0))
        size_mb = size_bytes / (1024 * 1024) if size_bytes > 0 else 0
        
        # Calcula bitrate total
        bitrate = float(format_info.get('bit_rate', 0))
        
        return {
            'video': video_streams[0] if video_streams else None,
            'audio': audio_streams,
            'subtitle': subtitle_streams,
            'format': format_info,
            'duration': float(format_info.get('duration', 0)),
            'size_mb': size_mb,
            'bitrate': bitrate
        }
    
    def _generate_output_media_info(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Gera informações de mídia de saída baseadas no profile."""
        codec = profile.get('codec', 'hevc_nvenc')
        
        # Mapeamento de codecs para nomes amigáveis
        codec_names = {
            'hevc_nvenc': 'HEVC (NVENC)',
            'h264_nvenc': 'H.264 (NVENC)',
            'av1_nvenc': 'AV1 (NVENC)',
            'hevc_amf': 'HEVC (AMF)',
            'h264_amf': 'H.264 (AMF)',
            'hevc_qsv': 'HEVC (QSV)',
            'h264_qsv': 'H.264 (QSV)',
            'libx265': 'HEVC (x265)',
            'libx264': 'H.264 (x264)'
        }
        
        # Determina codec de áudio de saída
        audio_codec = 'AAC' if profile.get('audio_tracks') is not None or not profile.get('keep_audio', True) else 'Copy'
        
        # Determina codec de legenda de saída
        subtitle_codec = 'Copy' if not profile.get('subtitle_burn', False) else 'Burned'
        
        # Calcula estimativa de tamanho de arquivo de saída
        estimated_size_mb = self._estimate_output_size(profile)
        
        return {
            'video': {'codec_name': codec_names.get(codec, codec)},
            'audio': [{'codec_name': audio_codec}],
            'subtitle': [{'codec_name': subtitle_codec}],
            'profile': profile,
            'estimated_size_mb': estimated_size_mb
        }
    
    def _estimate_output_size(self, profile: Dict[str, Any]) -> float:
        """Estima tamanho de arquivo de saída baseado em bitrate e duração."""
        duration = self._input_media_info.get('duration', 0)
        input_bitrate = self._input_media_info.get('bitrate', 0)
        input_size_mb = self._input_media_info.get('size_mb', 0)
        
        if duration <= 0:
            return 0
        
        # Fatores de compressão estimados por codec
        compression_factors = {
            'hevc_nvenc': 0.5,    # HEVC geralmente reduz para ~50% do tamanho original
            'h264_nvenc': 0.7,    # H264 reduz para ~70%
            'av1_nvenc': 0.4,     # AV1 é mais eficiente, ~40%
            'hevc_amf': 0.5,
            'h264_amf': 0.7,
            'hevc_qsv': 0.5,
            'h264_qsv': 0.7,
            'libx265': 0.45,      # x265 software é mais eficiente
            'libx264': 0.65
        }
        
        codec = profile.get('codec', 'hevc_nvenc').lower()
        
        # Ajusta fator baseado no CQ/CRF se disponível
        cq = profile.get('cq')
        base_factor = compression_factors.get(codec, 0.5)
        
        if cq:
            cq_value = int(cq) if cq.isdigit() else 20
            # CQ menor = maior qualidade = maior arquivo
            # CQ típico: 18-30 para HEVC
            if codec in ['hevc_nvenc', 'hevc_amf', 'hevc_qsv', 'libx265']:
                # HEVC: CQ 20 é ponto de referência
                factor_adjustment = (25 - cq_value) * 0.05  # Cada ponto de CQ = ~5% de tamanho
            elif codec in ['h264_nvenc', 'h264_amf', 'h264_qsv', 'libx264']:
                # H264: CQ 23 é ponto de referência
                factor_adjustment = (28 - cq_value) * 0.05
            else:
                factor_adjustment = 0
            base_factor = max(0.2, min(0.9, base_factor + factor_adjustment))
        
        # Calcula tamanho estimado
        estimated_size_mb = input_size_mb * base_factor
        
        # Se tiver bitrate de entrada, usa como referência alternativa
        if input_bitrate > 0:
            # Calcula bitrate de saída estimado
            output_bitrate = input_bitrate * base_factor
            
            # Se profile tem bitrate definido, usa esse valor
            if profile.get('bitrate'):
                try:
                    bitrate_str = profile['bitrate']
                    if bitrate_str.endswith('M'):
                        output_bitrate = float(bitrate_str[:-1]) * 1000
                    elif bitrate_str.endswith('K'):
                        output_bitrate = float(bitrate_str[:-1])
                    else:
                        output_bitrate = float(bitrate_str)
                except ValueError:
                    pass
            
            # Calcula tamanho baseado no bitrate: (bitrate * duration) / 8 / 1024
            estimated_size_mb = (output_bitrate * duration) / 8 / 1024
        
        return estimated_size_mb
    
    def _determine_transcode_status(self, profile: Dict[str, Any]) -> Dict[str, str]:
        """Determina status de transcodificação para cada stream."""
        # Mapeamento de codecs equivalentes
        hevc_codecs = ['hevc', 'hevc_nvenc', 'hevc_amf', 'hevc_qsv', 'libx265', 'h265']
        h264_codecs = ['h264', 'h264_nvenc', 'h264_amf', 'h264_qsv', 'libx264', 'avc1']
        
        input_video_codec = self._input_media_info.get('video', {}).get('codec_name', 'unknown').lower() if self._input_media_info.get('video') else 'unknown'
        output_codec = profile.get('codec', 'hevc_nvenc').lower()
        
        # Verifica se é o mesmo tipo de codec (HEVC ou H264)
        input_is_hevc = any(c in input_video_codec for c in hevc_codecs)
        input_is_h264 = any(c in input_video_codec for c in h264_codecs)
        output_is_hevc = any(c in output_codec for c in hevc_codecs)
        output_is_h264 = any(c in output_codec for c in h264_codecs)
        
        # Vídeo: transcode se codec de saída for diferente tipo
        if input_is_hevc and output_is_hevc:
            video_status = 'copy'
        elif input_is_h264 and output_is_h264:
            video_status = 'copy'
        else:
            video_status = 'transcode'
        
        # Áudio: copy se keep_audio for True, senão transcode para AAC
        audio_status = 'copy' if profile.get('keep_audio', True) else 'transcode'
        
        # Legenda: copy ou burned
        subtitle_status = 'burn' if profile.get('subtitle_burn', False) else 'copy'
        
        return {
            'video': video_status,
            'audio': audio_status,
            'subtitle': subtitle_status
        }
    
    def _get_status_icon(self, status: str) -> str:
        """Retorna ícone para status de transcodificação."""
        icons = {
            'transcode': '⚡',  # Relâmpago para transcodificação
            'copy': '📋',       # Clipboard para cópia
            'burn': '🔥'        # Fogo para burn-in
        }
        return icons.get(status, '❓')
    
    def _get_status_color(self, status: str) -> str:
        """Retorna cor para status de transcodificação."""
        colors = {
            'transcode': 'yellow',
            'copy': 'green',
            'burn': 'red'
        }
        return colors.get(status, 'white')
    
    def _generate_media_info_panel(self) -> Table:
        """Gera tabela side-by-side de informações de mídia."""
        table = Table(show_header=True, box=None, padding=(0, 2), expand=True)
        table.add_column("Stream", style="cyan", width=12)
        table.add_column("Entrada", style="white", width=30)
        table.add_column("→", style="dim", justify="center")
        table.add_column("Saída", style="white", width=30)
        table.add_column("Status", style="dim", width=10)
        
        # Adiciona linha de informações de arquivo (tamanho e duração)
        input_size_mb = self._input_media_info.get('size_mb', 0)
        input_duration = self._input_media_info.get('duration', 0)
        input_bitrate = self._input_media_info.get('bitrate', 0)
        
        if input_size_mb > 0:
            size_str = f"[bold]{format_size(input_size_mb)}[/bold]"
        else:
            size_str = "[dim]--[/dim]"
        
        if input_duration > 0:
            hours = int(input_duration // 3600)
            minutes = int((input_duration % 3600) // 60)
            seconds = int(input_duration % 60)
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            duration_str = "--:--:--"
        
        if input_bitrate > 0:
            bitrate_str = f"{input_bitrate / 1000:.1f} Kbps"
        else:
            bitrate_str = "[dim]--[/dim]"
        
        input_file_info = f"{size_str}\n[dim]Duração: {duration_str}[/dim]\n[dim]Bitrate: {bitrate_str}[/dim]"
        
        # Output file info (estimado)
        output_profile = self._output_media_info.get('profile', {})
        output_codec_name = self._output_media_info.get('video', {}).get('codec_name', 'Unknown')
        cq = output_profile.get('cq', 'CQ20')
        estimated_size_mb = self._output_media_info.get('estimated_size_mb', 0)
        
        # Calcula economia de espaço estimada
        if estimated_size_mb > 0 and input_size_mb > 0:
            space_saved = input_size_mb - estimated_size_mb
            space_saved_pct = ((input_size_mb - estimated_size_mb) / input_size_mb) * 100
            if space_saved_pct > 0:
                size_info = f"[green]~{format_size(estimated_size_mb)}[/green]\n[dim]Economia: {space_saved_pct:.1f}%[/dim]"
            else:
                size_info = f"[yellow]~{format_size(estimated_size_mb)}[/yellow]\n[dim]Similar ao original[/dim]"
        elif estimated_size_mb > 0:
            size_info = f"[bold]~{format_size(estimated_size_mb)}[/bold]"
        else:
            size_info = "[dim]Calculando...[/dim]"
        
        output_file_info = f"[dim]Codec: {output_codec_name}[/dim]\n[dim]Quality: {cq}[/dim]\n{size_info}"
        
        table.add_row(
            "📁 Arquivo",
            input_file_info,
            "→",
            output_file_info,
            ""
        )
        
        # Vídeo
        input_video = self._input_media_info.get('video', {})
        output_video = self._output_media_info.get('video', {})
        
        if input_video:
            input_video_info = f"[bold]{input_video.get('codec_name', 'unknown').upper()}[/bold]"
            if input_video.get('width') and input_video.get('height'):
                input_video_info += f"\n[dim]{input_video['width']}x{input_video['height']}[/dim]"
            if input_video.get('color_transfer') or input_video.get('color_primaries') == 'bt2020':
                input_video_info += f"\n[bold magenta]HDR[/bold magenta]"
        else:
            input_video_info = "[dim]--[/dim]"
        
        output_video_info = f"[bold]{output_video.get('codec_name', 'unknown')}[/bold]"
        video_status = self._transcode_status.get('video', 'unknown')
        
        table.add_row(
            "🎬 Vídeo",
            input_video_info,
            "→",
            output_video_info,
            f"[{self._get_status_color(video_status)}]{self._get_status_icon(video_status)} {video_status.upper()}[/{self._get_status_color(video_status)}]"
        )
        
        # Áudio
        input_audio_streams = self._input_media_info.get('audio', [])
        output_audio = self._output_media_info.get('audio', [{}])
        
        if input_audio_streams:
            audio_codecs = set()
            for stream in input_audio_streams:
                codec = stream.get('codec_name', 'unknown')
                lang = stream.get('tags', {}).get('language', '')
                audio_codecs.add(f"{codec.upper()}" + (f" ({lang})" if lang else ""))
            input_audio_info = "\n".join(audio_codecs) if audio_codecs else "[dim]--[/dim]"
        else:
            input_audio_info = "[dim]--[/dim]"
        
        audio_status = self._transcode_status.get('audio', 'unknown')
        output_audio_info = output_audio[0].get('codec_name', 'Copy') if output_audio else 'Copy'
        
        table.add_row(
            "🔊 Áudio",
            input_audio_info,
            "→",
            f"[bold]{output_audio_info}[/bold]",
            f"[{self._get_status_color(audio_status)}]{self._get_status_icon(audio_status)} {audio_status.upper()}[/{self._get_status_color(audio_status)}]"
        )
        
        # Legendas
        input_subtitle_streams = self._input_media_info.get('subtitle', [])
        output_subtitle = self._output_media_info.get('subtitle', [{}])
        
        if input_subtitle_streams:
            subtitle_codecs = set()
            for stream in input_subtitle_streams:
                codec = stream.get('codec_name', 'unknown')
                lang = stream.get('tags', {}).get('language', '')
                subtitle_codecs.add(f"{codec.upper()}" + (f" ({lang})" if lang else ""))
            input_subtitle_info = f"{len(input_subtitle_streams)} stream(s): " + ", ".join(list(subtitle_codecs)[:3])
            if len(subtitle_codecs) > 3:
                input_subtitle_info += f" +{len(subtitle_codecs) - 3}"
        else:
            input_subtitle_info = "[dim]--[/dim]"
        
        subtitle_status = self._transcode_status.get('subtitle', 'unknown')
        output_subtitle_info = output_subtitle[0].get('codec_name', 'Copy') if output_subtitle else 'Copy'
        
        table.add_row(
            "📝 Legendas",
            input_subtitle_info,
            "→",
            f"[bold]{output_subtitle_info}[/bold]",
            f"[{self._get_status_color(subtitle_status)}]{self._get_status_icon(subtitle_status)} {subtitle_status.upper()}[/{self._get_status_color(subtitle_status)}]"
        )
        
        return table
    
    def _generate_status_legend(self) -> Text:
        """Gera legenda para ícones de status."""
        legend = Text()
        legend.append("Legenda: ", style="dim")
        legend.append("⚡ ", style="yellow")
        legend.append("Transcode  ", style="white")
        legend.append("📋 ", style="green")
        legend.append("Copy  ", style="white")
        legend.append("🔥 ", style="red")
        legend.append("Burn-in", style="white")
        return legend
    
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
            
            # Painel de informações de mídia (side-by-side)
            media_info_panel = self._generate_media_info_panel()
            
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
            
            # Formata VRAM usando format_size (que espera MB)
            gpu_mem_display = format_size(gpu_mem) if gpu_mem > 0 else "--"
            if gpu_mem_total > 0:
                gpu_mem_display += f"/{format_size(gpu_mem_total)}"
            
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
            files_parts = []
            if self._input_file:
                files_parts.append(Text.from_markup(f"[dim]Input: {self._input_file}[/dim]"))
            if self._output_file:
                files_parts.append(Text.from_markup(f"[dim]Output: {self._output_file}[/dim]"))

            # Layout principal usando Group para renderizar tabelas corretamente
            renderables = [
                Text.from_markup(f"[bold white]{self._description}[/bold white]"),
                Text.from_markup(f"[dim]{self._status}[/dim]"),
                Text(""),
                Text.from_markup(progress_bar),
                Text(""),
                Text.from_markup("[bold magenta]📊 Stream Information:[/bold magenta]"),
                media_info_panel,
                self._generate_status_legend(),
                Text(""),
                Text.from_markup("[bold cyan]⚡ Encoding Stats:[/bold cyan]"),
                encoding_table,
                Text(""),
                Text.from_markup("[bold green]🖥️  Hardware:[/bold green]"),
                hw_table,
                Text(""),
            ]
            renderables.extend(files_parts)

            return Panel(
                Group(*renderables),
                border_style="magenta",
                title="🎬 NVENC Encoder - Tempo Real"
            )
    
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
        
        # 🔍 DEBUG: Log da linha completa recebida (apenas se contiver indicadores de progresso)
        if any(indicator in line.lower() for indicator in ['fps=', 'speed=', 'time=', 'frame=']):
            print(f"🔍 PARSER DEBUG: Linha FFmpeg detectada: {repr(line[:150])}")  # Primeiros 150 chars
        
        fps_match = self._fps_pattern.search(line)
        if fps_match:
            fps_value = float(fps_match.group(1))
            stats['fps'] = fps_value
            print(f"✅ PARSER: FPS extraído = {fps_value}")
        elif 'fps=' in line.lower():
            print(f"⚠️ PARSER: 'fps=' encontrado mas regex NÃO fez match. Linha: {repr(line[:150])}")
        
        speed_match = self._speed_pattern.search(line)
        if speed_match:
            speed_value = float(speed_match.group(1))
            stats['speed'] = speed_value
            print(f"✅ PARSER: Speed extraído = {speed_value}x")
        elif 'speed=' in line.lower():
            print(f"⚠️ PARSER: 'speed=' encontrado mas regex NÃO fez match. Linha: {repr(line[:150])}")
        
        bitrate_match = self._bitrate_pattern.search(line)
        if bitrate_match:
            bitrate_value = float(bitrate_match.group(1))
            stats['bitrate'] = bitrate_value
            print(f"✅ PARSER: Bitrate extraído = {bitrate_value} Kbps")
        elif 'bitrate=' in line.lower():
            print(f"⚠️ PARSER: 'bitrate=' encontrado mas regex NÃO fez match. Linha: {repr(line[:150])}")
        
        time_match = self._time_pattern.search(line)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = int(time_match.group(3))
            decimals = int(time_match.group(4))
            current_seconds = hours * 3600 + minutes * 60 + seconds + decimals / 100
            stats['current_time'] = current_seconds
            
            if self._duration_seconds > 0:
                progress_pct = (current_seconds / self._duration_seconds) * 100
                stats['progress'] = progress_pct
                print(f"✅ PARSER: Progresso = {progress_pct:.1f}% (tempo: {current_seconds:.1f}s / {self._duration_seconds:.1f}s)")
        elif 'time=' in line.lower():
            print(f"⚠️ PARSER: 'time=' encontrado mas regex NÃO fez match. Linha: {repr(line[:150])}")
        
        frame_match = self._frame_pattern.search(line)
        if frame_match:
            stats['frame'] = int(frame_match.group(1))
        
        if stats:
            print(f"📊 PARSER: Stats completos extraídos: {stats}")
        
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
