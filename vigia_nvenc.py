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
        
        options = [
            {"description": "Codificar arquivo único", "shortcut": "1"},
            {"description": "Codificar pasta", "shortcut": "2"},
            {"description": "Modo Watch (monitorar pastas)", "shortcut": "3"},
            {"description": "Ver fila de jobs", "shortcut": "4"},
            {"description": "Gerenciar perfis", "shortcut": "5"},
            {"description": "Ver estatísticas", "shortcut": "6"},
            {"description": "Verificar instalação", "shortcut": "7"},
            {"description": "Gerenciar pastas watch", "shortcut": "8"},
            {"description": "Sair", "shortcut": "9"}
        ]
        
        choice = menu.show_menu("Menu Principal", options)
        
        if choice == 0:
            console.print("\n[yellow]Use a CLI moderna para mais opções:[/yellow]")
            console.print("  [cyan]python vigia_nvenc.py -f video.mkv -p \"Filmes 4K\"[/cyan]")
            console.print("  [cyan]python vigia_nvenc.py --help[/cyan]\n")
            
            from src.cli import run_single_file_cli
            run_single_file_cli(config, profile_mgr, job_mgr, stats_mgr)
            
        elif choice == 1:
            from src.cli import run_folder_mode_cli
            run_folder_mode_cli(config, profile_mgr, job_mgr, queue_mgr)
            
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
            
            encoder = EncoderEngine(max_concurrent=config.get('encoding.max_concurrent', 2))
            hw_monitor = HardwareMonitor()
            progress_display = ProgressDisplay(console)
            
            def on_progress(job_id: str, progress: float):
                job_mgr.update_progress(job_id, progress)
                hw_stats = hw_monitor.get_stats()
                progress_display.set_hw_stats({
                    'gpu_util': hw_stats.gpu_util,
                    'gpu_temperature': hw_stats.gpu_temperature,
                    'gpu_memory_used': hw_stats.gpu_memory_used,
                    'cpu_util': hw_stats.cpu_util
                })
            
            def map_encoding_to_job_status(encoding_status: EncodingStatus) -> JobStatus:
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
                    hw_stats = hw_monitor.get_stats()
                    progress_display.set_hw_stats({
                        'gpu_util': hw_stats.gpu_util,
                        'gpu_temperature': hw_stats.gpu_temperature,
                        'gpu_memory_used': hw_stats.gpu_memory_used,
                        'cpu_util': hw_stats.cpu_util
                    })
                    time.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]Parando watch mode...[/yellow]")
                encoder.stop()
                hw_monitor.stop()
            
        elif choice == 3:
            queue = queue_mgr.list_queue()
            if queue:
                menu.show_jobs_table([
                    {
                        "id": q['job_id'],
                        "input_path": q['input_path'],
                        "profile_name": q['profile'].get('name', ''),
                        "status": "queued",
                        "progress": 0
                    } for q in queue
                ])
            else:
                menu.print_info("Fila vazia")
            input("\nPressione Enter para continuar...")
            
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
            
        elif choice == 7:
            from src.ui.watch_folders_ui import WatchFoldersUI
            watch_ui = WatchFoldersUI(console, config, profile_mgr)
            watch_ui.show_submenu()
            
        elif choice == 8:
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
