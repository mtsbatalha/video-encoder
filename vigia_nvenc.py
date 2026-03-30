#!/usr/bin/env python3
"""
Fabrica de Conversão NVENC Pro v2.0
Codificação de vídeo acelerada por GPU NVIDIA

Este é o ponto de entrada principal. Para a nova interface CLI, use:
    python vigia_nvenc.py --help

Ou importe o módulo src.cli.main diretamente.
"""

import sys
import signal
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

console = Console()


def handler_sigint(signum, frame):
    """Handler para SIGINT (Ctrl+C)."""
    console.print("\n[yellow]Interrupção recebida. Encerrando...[/yellow]")
    sys.exit(0)


signal.signal(signal.SIGINT, handler_sigint)


def show_banner():
    """Exibe banner do aplicativo."""
    banner = """
[bold magenta]╔═══════════════════════════════════════════════════════════╗[/bold magenta]
[bold magenta]║[/bold magenta]     [bold white]Fabrica de Conversão NVENC Pro v2.0[/bold white]             [bold magenta]║[/bold magenta]
[bold magenta]║[/bold magenta]     [dim]Codificação de vídeo acelerada por GPU NVIDIA[/dim]   [bold magenta]║[/bold magenta]
[bold magenta]╚═══════════════════════════════════════════════════════════╝[/bold magenta]
    """
    console.print(Panel(banner, border_style="magenta"))


def run_single_file_cli_setup(config, profile_mgr, job_mgr, stats_mgr):
    """Setup para codificação de arquivo único. Retorna (input_path, profile, output_path) ou (None, None, None) se cancelado."""
    from src.ui.menu import Menu
    from src.utils.path_utils import PathUtils
    from src.utils.file_utils import FileUtils
    from pathlib import Path
    
    console = Console()
    menu = Menu(console)
    
    input_path = menu.ask("Caminho do arquivo de vídeo")
    
    video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpeg', '.mpg'}
    if not Path(input_path).exists():
        menu.print_error(f"Arquivo não encontrado: {input_path}")
        input("\nPressione Enter para continuar...")
        return None, None, None
    
    if not Path(input_path).is_file():
        menu.print_error(f"Não é um arquivo: {input_path}")
        input("\nPressione Enter para continuar...")
        return None, None, None
    
    ext = Path(input_path).suffix.lower()
    if ext not in video_extensions:
        menu.print_error(f"Extensão não suportada: {ext}")
        input("\nPressione Enter para continuar...")
        return None, None, None
    
    profiles = profile_mgr.list_profiles()
    if not profiles:
        menu.print_error("Nenhum perfil encontrado. Crie um perfil primeiro.")
        input("\nPressione Enter para continuar...")
        return None, None, None
    
    profile_idx = menu.show_options([p['name'] for p in profiles], "Perfis disponíveis")
    profile = profiles[profile_idx]
    
    output_dir = menu.ask("Diretório de output", default=str(Path(input_path).parent))
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    output_path = PathUtils.generate_output_path(input_path, output_dir, suffix="-encoded")
    
    return input_path, profile, output_path


def _process_single_job_immediate(console, menu, config, job_mgr, stats_mgr, input_path, output_path, profile):
    """Processa job único imediatamente com monitor em tempo real."""
    from src.core.encoder_engine import EncoderEngine, EncodingJob, EncodingStatus
    from src.core.hw_monitor import HardwareMonitor
    from src.core.ffmpeg_wrapper import FFmpegWrapper
    import time
    from pathlib import Path
    
    console.print("\n[bold]Iniciando codificação com monitor em tempo real...[/bold]\n")
    
    encoder = EncoderEngine(max_concurrent=1)
    hw_monitor = HardwareMonitor()
    
    def on_progress(job_id: str, progress: float):
        job_mgr.update_progress(job_id, progress)
    
    def map_encoding_to_job_status(encoding_status: EncodingStatus):
        from src.managers.job_manager import JobStatus
        mapping = {
            EncodingStatus.PENDING: JobStatus.PENDING,
            EncodingStatus.RUNNING: JobStatus.RUNNING,
            EncodingStatus.COMPLETED: JobStatus.COMPLETED,
            EncodingStatus.FAILED: JobStatus.FAILED,
            EncodingStatus.CANCELLED: JobStatus.CANCELLED,
            EncodingStatus.PAUSED: JobStatus.PAUSED
        }
        return mapping.get(encoding_status, JobStatus.PENDING)
    
    def on_status(job_id: str, status: EncodingStatus):
        job_status = map_encoding_to_job_status(status)
        job_mgr.update_job_status(job_id, job_status)
        if status == EncodingStatus.COMPLETED:
            job = job_mgr.get_job(job_id)
            if job:
                stats_mgr.record_encode(
                    profile_id=profile.get('id', 'custom'),
                    profile_name=profile.get('name', 'Custom'),
                    success=True,
                    duration_seconds=0,
                    input_size=job.get('input_size', 0),
                    output_size=job.get('output_size', 0)
                )
        elif status == EncodingStatus.FAILED:
            job = job_mgr.get_job(job_id)
            if job:
                stats_mgr.record_encode(
                    profile_id=profile.get('id', 'custom'),
                    profile_name=profile.get('name', 'Custom'),
                    success=False,
                    duration_seconds=0,
                    input_size=0,
                    output_size=0,
                    failure_reason=job.get('error_message', '')
                )
    
    encoder.add_progress_callback(on_progress)
    encoder.add_status_callback(on_status)
    encoder.start()
    hw_monitor.start()
    
    job_id = job_mgr.create_job(
        input_path=input_path,
        output_path=output_path,
        profile_id=profile.get('id', 'custom'),
        profile_name=profile.get('name', 'Custom')
    )
    
    job = EncodingJob(
        id=job_id,
        input_path=input_path,
        output_path=output_path,
        profile=profile
    )
    encoder.add_job(job)
    
    try:
        while True:
            active_count = len(encoder.get_all_jobs())
            
            if active_count == 0:
                console.print("\n[green]✓ Codificação completada![/green]")
                break
            
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Processamento interrompido[/yellow]")
    finally:
        encoder.stop()
        hw_monitor.stop()
    
    console.input("\nPressione Enter para continuar...")


def run_folder_mode_cli_setup(config, profile_mgr, job_mgr, queue_mgr):
    """Setup para codificação de pasta. Retorna lista de arquivos ou None se cancelado."""
    from src.ui.menu import Menu
    from src.utils.path_utils import PathUtils
    from src.utils.file_utils import FileUtils
    from pathlib import Path
    
    console = Console()
    menu = Menu(console)
    
    folder_path = menu.ask("Caminho da pasta")
    
    if not Path(folder_path).exists():
        menu.print_error(f"Pasta não encontrada: {folder_path}")
        input("\nPressione Enter para continuar...")
        return None
    
    if not Path(folder_path).is_dir():
        menu.print_error(f"Não é uma pasta: {folder_path}")
        input("\nPressione Enter para continuar...")
        return None
    
    video_files = FileUtils.find_video_files(folder_path)
    
    if not video_files:
        menu.print_error("Nenhum vídeo encontrado na pasta")
        input("\nPressione Enter para continuar...")
        return None
    
    profiles = profile_mgr.list_profiles()
    if not profiles:
        menu.print_error("Nenhum perfil encontrado. Crie um perfil primeiro.")
        input("\nPressione Enter para continuar...")
        return None
    
    profile_idx = menu.show_options([p['name'] for p in profiles], "Perfis disponíveis")
    profile = profiles[profile_idx]
    
    output_dir = menu.ask("Diretório de output", default=str(Path(folder_path) / "converted"))
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    for video_file in video_files:
        output_path = PathUtils.generate_output_path(video_file, output_dir, suffix="-encoded")
        
        job_id = job_mgr.create_job(
            input_path=video_file,
            output_path=output_path,
            profile_id=profile['id'],
            profile_name=profile['name']
        )
        
        queue_mgr.add_to_queue(
            job_id=job_id,
            input_path=video_file,
            output_path=output_path,
            profile=profile
        )
    
    return video_files


def _process_queue_immediate(console, menu, config, job_mgr, queue_mgr, stats_mgr):
    """Processa fila imediatamente com monitor em tempo real."""
    from src.core.encoder_engine import EncoderEngine, EncodingJob, EncodingStatus
    from src.core.hw_monitor import HardwareMonitor
    import time
    from pathlib import Path
    
    queue = queue_mgr.list_queue()
    if not queue:
        console.print("[yellow]Fila vazia[/yellow]")
        console.input("Pressione Enter para continuar...")
        return
    
    console.print(f"\n[bold]Processando {len(queue)} job(s) com monitor em tempo real...[/bold]\n")
    
    encoder = EncoderEngine(max_concurrent=config.get('encoding.max_concurrent', 1))
    hw_monitor = HardwareMonitor()
    
    def on_progress(job_id: str, progress: float):
        job_mgr.update_progress(job_id, progress)
    
    def map_encoding_to_job_status(encoding_status: EncodingStatus):
        from src.managers.job_manager import JobStatus
        mapping = {
            EncodingStatus.PENDING: JobStatus.PENDING,
            EncodingStatus.RUNNING: JobStatus.RUNNING,
            EncodingStatus.COMPLETED: JobStatus.COMPLETED,
            EncodingStatus.FAILED: JobStatus.FAILED,
            EncodingStatus.CANCELLED: JobStatus.CANCELLED,
            EncodingStatus.PAUSED: JobStatus.PAUSED
        }
        return mapping.get(encoding_status, JobStatus.PENDING)
    
    def on_status(job_id: str, status: EncodingStatus):
        job_status = map_encoding_to_job_status(status)
        job_mgr.update_job_status(job_id, job_status)
        if status == EncodingStatus.COMPLETED:
            job = job_mgr.get_job(job_id)
            if job:
                stats_mgr.record_encode(
                    profile_id=job.get('profile_id', ''),
                    profile_name=job.get('profile_name', ''),
                    success=True,
                    duration_seconds=0,
                    input_size=job.get('input_size', 0),
                    output_size=job.get('output_size', 0)
                )
        elif status == EncodingStatus.FAILED:
            job = job_mgr.get_job(job_id)
            if job:
                stats_mgr.record_encode(
                    profile_id=job.get('profile_id', ''),
                    profile_name=job.get('profile_name', ''),
                    success=False,
                    duration_seconds=0,
                    input_size=0,
                    output_size=0,
                    failure_reason=job.get('error_message', '')
                )
    
    encoder.add_progress_callback(on_progress)
    encoder.add_status_callback(on_status)
    encoder.start()
    hw_monitor.start()
    
    try:
        while True:
            active_count = len(encoder.get_all_jobs())
            max_concurrent = config.get('encoding.max_concurrent', 1)
            
            if active_count < max_concurrent:
                next_job = queue_mgr.get_next_job()
                if next_job:
                    job = EncodingJob(
                        id=next_job['job_id'],
                        input_path=next_job['input_path'],
                        output_path=next_job['output_path'],
                        profile=next_job['profile']
                    )
                    encoder.add_job(job)
                    queue_mgr.mark_job_started(next_job['job_id'])
                    console.print(f"\n[cyan]▶ Iniciando: {Path(next_job['input_path']).name}[/cyan]")
            
            queue_remaining = queue_mgr.list_queue()
            pending_queue = [j for j in queue_remaining if not j.get('started_at')]
            
            if active_count == 0 and not pending_queue:
                console.print("\n[bold green]✓ Todos os jobs foram processados![/bold green]")
                break
            
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Processamento interrompido[/yellow]")
    finally:
        encoder.stop()
        hw_monitor.stop()
    
    console.input("\nPressione Enter para continuar...")


def main_menu():
    """Exibe menu principal legado (compatibilidade)."""
    from src.ui.menu import Menu
    from src.managers.config_manager import ConfigManager
    from src.managers.profile_manager import ProfileManager
    from src.managers.job_manager import JobManager, JobStatus
    from src.managers.queue_manager import QueueManager
    from src.managers.stats_manager import StatsManager
    from src.core.ffmpeg_wrapper import FFmpegWrapper
    from src.core.hw_monitor import HardwareMonitor
    from src.core.encoder_engine import EncoderEngine, EncodingStatus
    from src.ui.progress import ProgressDisplay
    import time
    
    menu = Menu(console)
    config = ConfigManager()
    profile_mgr = ProfileManager()
    job_mgr = JobManager()
    queue_mgr = QueueManager()
    stats_mgr = StatsManager()
    
    while True:
        menu.clear()
        show_banner()
        
        # Verificar status da fila
        queue_count = queue_mgr.get_queue_length()
        pending_jobs = len(job_mgr.get_pending_jobs())
        running_jobs = len(job_mgr.get_running_jobs())
        
        # Atualizar status da fila
        queue_count = queue_mgr.get_queue_length()
        
        queue_status = ""
        if queue_count > 0:
            queue_status = f" [yellow]({queue_count} jobs na fila)[/yellow]"
        
        options = [
            {"description": "Codificar arquivo único", "shortcut": "1"},
            {"description": "Codificar pasta", "shortcut": "2"},
            {"description": "Modo Watch (monitorar pastas)", "shortcut": "3"},
            {"description": f"Ver fila de jobs{queue_status}", "shortcut": "4"},
            {"description": "Gerenciar perfis", "shortcut": "5"},
            {"description": "Ver estatísticas", "shortcut": "6"},
            {"description": "Verificar instalação", "shortcut": "7"},
            {"description": "Detectar hardware", "shortcut": "8"},
            {"description": "Gerenciar pastas watch", "shortcut": "9"},
            {"description": "Sair", "shortcut": "0"}
        ]
        
        choice = menu.show_menu("Menu Principal", options)
        
        if choice == 0:
            console.print("\n[yellow]Use a CLI moderna para mais opções:[/yellow]")
            console.print("  [cyan]python vigia_nvenc.py -f video.mkv -p \"Filmes 4K\"[/cyan]")
            console.print("  [cyan]python vigia_nvenc.py --help[/cyan]\n")
            
            input_path, profile, output_path = run_single_file_cli_setup(config, profile_mgr, job_mgr, stats_mgr)
            
            if input_path is None or profile is None or output_path is None:
                continue
            
            console.print("\n[bold]Opções de processamento:[/bold]")
            if menu.ask_confirm("Deseja iniciar a conversão agora?", default=True):
                _process_single_job_immediate(
                    console, menu, config, job_mgr, stats_mgr,
                    input_path, output_path, profile
                )
            else:
                from src.managers.queue_manager import QueueManager
                job_id = job_mgr.create_job(
                    input_path=input_path,
                    output_path=output_path,
                    profile_id=profile.get('id', 'custom'),
                    profile_name=profile.get('name', 'Custom')
                )
                queue_mgr.add_to_queue(
                    job_id=job_id,
                    input_path=input_path,
                    output_path=output_path,
                    profile=profile
                )
                console.print(f"\n[green]✓ Job adicionado à fila![/green]")
                console.input("Pressione Enter para continuar...")
            
        elif choice == 1:
            files_info = run_folder_mode_cli_setup(config, profile_mgr, job_mgr, queue_mgr)
            
            if files_info is None or len(files_info) == 0:
                continue
            
            console.print(f"\n[bold]{len(files_info)} arquivo(s) adicionado(s) à fila[/bold]")
            if menu.ask_confirm("Deseja iniciar o processamento agora?", default=True):
                _process_queue_immediate(
                    console, menu, config, job_mgr, queue_mgr, stats_mgr
                )
            else:
                console.print(f"\n[yellow]Jobs adicionados à fila. Processe depois em 'Ver fila de jobs'.[/yellow]")
                console.input("Pressione Enter para continuar...")
            
        elif choice == 2:
            console.print("\n[bold]Iniciando Modo Watch...[/bold]\n")
            
            watch_folders = config.get_watch_folders()
            if not watch_folders:
                menu.print_warning("Nenhuma pasta watch configurada em config.json")
                input("\nPressione Enter para continuar...")
                continue
            
            console.print(f"Monitorando {len(watch_folders)} pasta(s)...\n")
            
            for folder in watch_folders:
                console.print(f"  [cyan]{folder['nome']}[/cyan]")
                console.print(f"    Entrada: {folder['entrada']}")
                console.print(f"    Saída: {folder['saida']}")
                console.print(f"    Perfil: {folder.get('profile', 'N/A')}\n")
            
            console.print("\n[yellow]Pressione Ctrl+C para parar[/yellow]\n")
            
            from src.ui.realtime_monitor import RealTimeEncodingMonitor
            encoder = EncoderEngine(max_concurrent=config.get('encoding.max_concurrent', 2))
            hw_monitor = HardwareMonitor()
            
            def on_progress(job_id: str, progress: float):
                job_mgr.update_progress(job_id, progress)
            
            def map_encoding_to_job_status(encoding_status: EncodingStatus):
                from src.managers.job_manager import JobStatus
                mapping = {
                    EncodingStatus.PENDING: JobStatus.PENDING,
                    EncodingStatus.RUNNING: JobStatus.RUNNING,
                    EncodingStatus.COMPLETED: JobStatus.COMPLETED,
                    EncodingStatus.FAILED: JobStatus.FAILED,
                    EncodingStatus.CANCELLED: JobStatus.CANCELLED,
                    EncodingStatus.PAUSED: JobStatus.PAUSED
                }
                return mapping.get(encoding_status, JobStatus.PENDING)
            
            def on_status(job_id: str, status: EncodingStatus):
                job_status = map_encoding_to_job_status(status)
                job_mgr.update_job_status(job_id, job_status)
                if status == EncodingStatus.COMPLETED:
                    job = job_mgr.get_job(job_id)
                    if job:
                        stats_mgr.record_encode(
                            profile_id=job.get('profile_id', ''),
                            profile_name=job.get('profile_name', ''),
                            success=True,
                            duration_seconds=0,
                            input_size=job.get('input_size', 0),
                            output_size=job.get('output_size', 0)
                        )
                elif status == EncodingStatus.FAILED:
                    job = job_mgr.get_job(job_id)
                    if job:
                        stats_mgr.record_encode(
                            profile_id=job.get('profile_id', ''),
                            profile_name=job.get('profile_name', ''),
                            success=False,
                            duration_seconds=0,
                            input_size=0,
                            output_size=0,
                            failure_reason=job.get('error_message', '')
                        )
            
            encoder.add_progress_callback(on_progress)
            encoder.add_status_callback(on_status)
            encoder.start()
            hw_monitor.start()
            
            try:
                while True:
                    active_count = len(encoder.get_all_jobs())
                    max_concurrent = config.get('encoding.max_concurrent', 2)
                    
                    if active_count < max_concurrent:
                        next_job = queue_mgr.get_next_job()
                        if next_job:
                            from src.core.encoder_engine import EncodingJob
                            job = EncodingJob(
                                id=next_job['job_id'],
                                input_path=next_job['input_path'],
                                output_path=next_job['output_path'],
                                profile=next_job['profile']
                            )
                            encoder.add_job(job)
                            queue_mgr.mark_job_started(next_job['job_id'])
                    
                    time.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]Parando watch mode...[/yellow]")
                encoder.stop()
                hw_monitor.stop()
            
        elif choice == 3:
            _process_queue_immediate(
                console, menu, config, job_mgr, queue_mgr, stats_mgr
            )
            
        elif choice == 4:
            while True:
                menu.clear()
                menu.print_header("Gerenciador de Perfis")
                
                profile_options = [
                    {"description": "Listar perfis", "shortcut": "1"},
                    {"description": "Criar novo perfil", "shortcut": "2"},
                    {"description": "Exportar perfil", "shortcut": "3"},
                    {"description": "Importar perfil", "shortcut": "4"},
                    {"description": "Voltar", "shortcut": "0"}
                ]
                
                profile_choice = menu.show_menu("Menu", profile_options)
                
                if profile_choice == 0:
                    profiles = profile_mgr.list_profiles()
                    menu.show_profiles_table(profiles)
                    input("\nPressione Enter para continuar...")
                    
                elif profile_choice == 1:
                    name = menu.ask("Nome do perfil")
                    codec = menu.ask("Codec (hevc_nvenc/h264_nvenc/av1_nvenc)", default="hevc_nvenc")
                    cq = menu.ask("CQ (Constant Quality)", default="24")
                    preset = menu.ask("Preset (p1-p7)", default="p5")
                    resolution = menu.ask("Resolução (opcional)", default="")
                    
                    profile_id = profile_mgr.create_profile(
                        name=name,
                        codec=codec,
                        cq=cq if cq else None,
                        preset=preset,
                        resolution=resolution if resolution else None
                    )
                    
                    menu.print_success(f"Perfil criado com ID: {profile_id}")
                    input("\nPressione Enter para continuar...")
                    
                elif profile_choice == 2:
                    profile_name = menu.ask("Nome do perfil para exportar")
                    profile = profile_mgr.get_profile(profile_name) or profile_mgr.get_profile_by_name(profile_name)
                    
                    if profile:
                        output_file = f"{profile_name}.json"
                        if profile_mgr.export_profile(profile_name, output_file):
                            menu.print_success(f"Perfil exportado para: {output_file}")
                        else:
                            menu.print_error("Erro ao exportar perfil")
                    else:
                        menu.print_error("Perfil não encontrado")
                    input("\nPressione Enter para continuar...")
                    
                elif profile_choice == 3:
                    import_file = menu.ask("Arquivo JSON para importar")
                    if Path(import_file).exists():
                        if profile_mgr.import_profile(import_file):
                            menu.print_success("Perfil(s) importado(s) com sucesso")
                        else:
                            menu.print_error("Erro ao importar perfil")
                    else:
                        menu.print_error("Arquivo não encontrado")
                    input("\nPressione Enter para continuar...")
                    
                elif profile_choice == 4:
                    break
            
        elif choice == 5:
            summary = stats_mgr.get_summary()
            menu.show_stats_panel(summary)
            input("\nPressione Enter para continuar...")
            
        elif choice == 6:
            summary = stats_mgr.get_summary()
            menu.show_stats_panel(summary)
            input("\nPressione Enter para continuar...")
            
        elif choice == 7:
            console.print(Panel("[bold]Verificando instalação...[/bold]"))
            
            ffmpeg = FFmpegWrapper()
            if ffmpeg.verify_installation():
                menu.print_success("FFmpeg instalado")
                codecs = ffmpeg.get_nvenc_codecs()
                if codecs:
                    console.print(f"[green][OK][/green] Codecs NVENC disponíveis: {', '.join(codecs)}")
                else:
                    menu.print_warning("Nenhum codec NVENC encontrado")
            else:
                menu.print_error("FFmpeg não encontrado")
                console.print("Instale FFmpeg com suporte NVENC")
            
            import importlib.util
            if importlib.util.find_spec('psutil') is not None:
                menu.print_success("psutil instalado")
            else:
                menu.print_warning("psutil não instalado (monitoramento CPU limitado)")
            
            hw_monitor_check = HardwareMonitor()
            hw_monitor_check._update_gpu_stats()
            stats = hw_monitor_check.get_stats()
            if stats.gpu_util >= 0 or stats.gpu_temperature > 0:
                console.print(f"[green][OK][/green] GPU detectada: {stats.gpu_temperature}°C")
            else:
                menu.print_warning("GPU não detectada ou nvidia-smi não disponível")
            
            input("\nPressione Enter para continuar...")
            
        elif choice == 8:
            from src.core.hw_detector import HardwareDetector
            
            console.print(Panel("[bold]Detectando hardware...[/bold]"))
            
            detector = HardwareDetector()
            caps = detector.detect()
            
            if not caps:
                console.print("[red]Erro ao detectar hardware[/red]")
                input("\nPressione Enter para continuar...")
                continue
            
            hw_info = caps.to_dict()
            
            console.print(f"\n[bold cyan]Hardware Detectado:[/bold cyan]")
            
            if hw_info.get('gpus_nvidia'):
                for gpu in hw_info['gpus_nvidia']:
                    console.print(f"  [green]•[/green] {gpu.get('name', 'NVIDIA GPU')} ({gpu.get('memory_gb', 0)}GB VRAM)")
                    console.print(f"      NVENC: {'[green]Suportado[/green]' if gpu.get('nvenc_supported') else '[red]Não suportado[/red]'}")
            else:
                console.print("  [yellow]Nenhuma GPU NVIDIA detectada[/yellow]")
            
            if hw_info.get('gpus_amd'):
                for gpu in hw_info['gpus_amd']:
                    console.print(f"  [green]•[/green] {gpu.get('name', 'AMD GPU')}")
                    console.print(f"      AMF: {'[green]Suportado[/green]' if gpu.get('amf_supported') else '[red]Não suportado[/red]'}")
            else:
                console.print("  [dim]Nenhuma GPU AMD detectada[/dim]")
            
            if hw_info.get('igpu_intel'):
                igpu = hw_info['igpu_intel']
                console.print(f"  [green]•[/green] {igpu.get('name', 'Intel iGPU')}")
                console.print(f"      QSV: {'[green]Suportado[/green]' if igpu.get('qsv_supported') else '[red]Não suportado[/red]'}")
            else:
                console.print("  [dim]Nenhuma iGPU Intel detectada[/dim]")
            
            if hw_info.get('igpu_amd'):
                igpu = hw_info['igpu_amd']
                console.print(f"  [green]•[/green] {igpu.get('name', 'AMD iGPU')}")
                console.print(f"      AMF: {'[green]Suportado[/green]' if igpu.get('amf_supported') else '[red]Não suportado[/red]'}")
            else:
                console.print("  [dim]Nenhuma iGPU AMD detectada[/dim]")
            
            console.print(f"\n[bold cyan]CPU:[/bold cyan] {hw_info.get('cpu_cores', 0)} núcleos, {hw_info.get('cpu_threads', 0)} threads")
            console.print(f"[bold cyan]RAM:[/bold cyan] {hw_info.get('ram_gb', 0)} GB")
            
            console.print(f"\n[bold cyan]Backend recomendado:[/bold cyan] {hw_info.get('recommended_backend', 'unknown')}")
            
            console.print(f"\n[bold cyan]Codecs Disponíveis (FFmpeg):[/bold cyan]")
            available_codecs = caps.available_codecs
            if available_codecs:
                for codec in available_codecs:
                    console.print(f"  [green]•[/green] {codec}")
            else:
                console.print("  [yellow]Nenhum codec encontrado[/yellow]")
            
            console.print(f"\n[bold cyan]Perfis por Categoria:[/bold cyan]")
            hw_summary = profile_mgr.get_hardware_detection_summary()
            for category, count in hw_summary['profiles_by_category'].items():
                console.print(f"  {category}: [cyan]{count}[/cyan] perfis")
            
            input("\nPressione Enter para continuar...")
            
        elif choice == 9:
            from src.ui.watch_folders_ui import WatchFoldersUI
            watch_ui = WatchFoldersUI(console, config, profile_mgr)
            watch_ui.show_submenu()
            
        elif choice == 0:
            break


if __name__ == '__main__':
    if len(sys.argv) > 1:
        from src.cli import main as cli_main
        cli_main()
    else:
        show_banner()
        console.print("\n[dim]Nenhum argumento fornecido. Iniciando menu interativo...[/dim]\n")
        console.print("[yellow]Dica: Use --help para ver todas as opções da CLI[/yellow]\n")
        main_menu()
