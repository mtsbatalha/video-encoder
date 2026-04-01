import argparse
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from .managers.config_manager import ConfigManager
from .managers.profile_manager import ProfileManager
from .managers.job_manager import JobManager, JobStatus
from .managers.stats_manager import StatsManager
from .managers.queue_manager import QueueManager
from .managers.unified_queue_manager import UnifiedQueueManager
from .core.ffmpeg_wrapper import FFmpegWrapper
from .core.hw_monitor import HardwareMonitor
from .core.hw_detector import HardwareDetector
from .core.encoder_engine import EncoderEngine, EncodingStatus
from .utils.path_utils import PathUtils
from .utils.file_utils import FileUtils, FileConflictStrategy
from .ui.menu import Menu
from .ui.progress import ProgressDisplay
from .ui.queue_menu import show_queue_submenu
from .ui.recurrent_folder_ui import RecurrentFolderUI
from .managers.recurrent_history_manager import RecurrentHistoryManager

console = Console()


def check_debug_key(encoder: EncoderEngine):
    """Verifica se a tecla 'D' foi pressionada para toggle de debug.
    
    Args:
        encoder: Instância do EncoderEngine para toggle de debug.
    
    Returns:
        True se tecla foi processada, False caso contrário.
    """
    try:
        import sys
        import msvcrt  # Windows
        
        if msvcrt.kbhit():
            char = msvcrt.getwch()
            if char.lower() == 'd':
                debug_enabled = encoder.toggle_debug()
                # Adiciona log de sistema que será exibido no monitor quando debug estiver ativo
                encoder.realtime_monitor._add_debug_log(f"Debug {'ativado' if debug_enabled else 'desativado'} via tecla D")
                return True
    except ImportError:
        # Linux/Mac - requer configuração especial de terminal
        try:
            import tty
            import termios
            import select
            
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                if select.select([sys.stdin], [], [], 0)[0]:
                    char = sys.stdin.read(1)
                    if char.lower() == 'd':
                        debug_enabled = encoder.toggle_debug()
                        encoder.realtime_monitor._add_debug_log(f"Debug {'ativado' if debug_enabled else 'desativado'} via tecla D")
                        return True
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            pass
    
    return False



def create_parser() -> argparse.ArgumentParser:
    """Cria parser de argumentos CLI."""
    parser = argparse.ArgumentParser(
        prog='vigia_nvenc',
        description='Fabrica de Conversão NVENC Pro v2.0 - Codificação de vídeo acelerada por GPU NVIDIA'
    )
    
    parser.add_argument('--version', action='version', version='%(prog)s 2.0.0')
    parser.add_argument('--config', type=str, help='Caminho para arquivo de config personalizado')
    
    group_mode = parser.add_mutually_exclusive_group()
    group_mode.add_argument('--watch', action='store_true', help='Modo watch (monitorar pastas)')
    group_mode.add_argument('-f', '--file', type=str, help='Codificar arquivo único')
    group_mode.add_argument('-F', '--folder', type=str, help='Codificar todos vídeos de uma pasta')
    group_mode.add_argument('--interactive', '-i', action='store_true', help='Modo interativo')
    
    parser.add_argument('-p', '--profile', type=str, help='Perfil de encoding (nome ou ID)')
    parser.add_argument('-o', '--output', type=str, help='Diretório de output')
    parser.add_argument('--output-file', type=str, help='Arquivo de output específico (para arquivo único)')
    
    parser.add_argument('--codec', type=str, choices=['hevc_nvenc', 'h264_nvenc', 'av1_nvenc'], help='Codec de vídeo')
    parser.add_argument('--cq', type=str, help='Constant Quality (1-51 para HEVC/H264, 1-63 para AV1)')
    parser.add_argument('--bitrate', type=str, help='Bitrate (ex: 10M, 5000K)')
    parser.add_argument('--preset', type=str, choices=['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7'], help='Preset de encoding')
    parser.add_argument('--resolution', type=str, choices=['480', '720', '1080', '1440', '2160'], help='Resolução de output')
    parser.add_argument('--two-pass', action='store_true', help='Usar two-pass encoding')
    parser.add_argument('--hdr-to-sdr', action='store_true', help='Converter HDR para SDR')
    parser.add_argument('--deinterlace', action='store_true', help='Aplicar deinterlacing')
    
    parser.add_argument('--profile-list', action='store_true', help='Listar perfis disponíveis')
    parser.add_argument('--profile-create', type=str, metavar='NAME', help='Criar novo perfil')
    parser.add_argument('--profile-export', type=str, metavar='PROFILE', help='Exportar perfil para JSON')
    parser.add_argument('--profile-import', type=str, metavar='FILE', help='Importar perfil de JSON')
    
    parser.add_argument('--stats', action='store_true', help='Mostrar estatísticas')
    parser.add_argument('--stats-export', type=str, metavar='FILE', help='Exportar estatísticas para JSON')
    parser.add_argument('--stats-reset', action='store_true', help='Resetar estatísticas')
    
    parser.add_argument('--queue', action='store_true', help='Mostrar fila de jobs')
    parser.add_argument('--queue-pause', action='store_true', help='Pausar fila')
    parser.add_argument('--queue-resume', action='store_true', help='Retomar fila')
    parser.add_argument('--queue-clear', action='store_true', help='Limpar fila')
    
    parser.add_argument('--check', action='store_true', help='Verificar instalação (FFmpeg, GPU)')
    
    parser.add_argument('--detect-hardware', action='store_true', help='Detectar hardware e mostrar codecs disponíveis')
    parser.add_argument('--hardware', type=str, choices=['nvidia_gpu', 'amd_gpu', 'intel_igpu', 'amd_igpu', 'cpu'], help='Filtrar perfis por categoria de hardware')
    
    return parser


def cmd_check(args, config: ConfigManager):
    """Verifica instalação."""
    console.print(Panel("[bold]Verificando instalação...[/bold]"))
    
    ffmpeg = FFmpegWrapper()
    if ffmpeg.verify_installation():
        console.print("[green][OK][/green] FFmpeg instalado")
        codecs = ffmpeg.get_nvenc_codecs()
        if codecs:
            console.print(f"[green][OK][/green] Codecs NVENC disponíveis: {', '.join(codecs)}")
        else:
            console.print("[yellow][!][/yellow] Nenhum codec NVENC encontrado")
    else:
        console.print("[red][X][/red] FFmpeg não encontrado")
        console.print("Instale FFmpeg com suporte NVENC")
    
    import importlib.util
    if importlib.util.find_spec('psutil') is not None:
        console.print("[green][OK][/green] psutil instalado")
    else:
        console.print("[yellow][!][/yellow] psutil não instalado (monitoramento CPU limitado)")
    
    hw = HardwareMonitor()
    hw._update_gpu_stats()
    stats = hw.get_stats()
    if stats.gpu_util >= 0 or stats.gpu_temperature > 0:
        console.print(f"[green][OK][/green] GPU detectada: {stats.gpu_temperature}°C")
    else:
        console.print("[yellow][!][/yellow] GPU não detectada ou nvidia-smi não disponível")


def cmd_detect_hardware(args, profile_mgr: ProfileManager):
    """Detecta hardware e mostra perfis recomendados."""
    console.print(Panel("[bold]Detectando hardware...[/bold]"))
    
    detector = HardwareDetector()
    caps = detector.detect()
    
    if not caps:
        console.print("[red]Erro ao detectar hardware[/red]")
        return
    
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


def cmd_profile_list(args, profile_mgr: ProfileManager):
    """Lista perfis."""
    if hasattr(args, 'hardware') and args.hardware:
        profiles = profile_mgr.get_profiles_by_hardware_category(args.hardware)
        title = f"Perfis - Hardware: {args.hardware}"
    else:
        profiles = profile_mgr.list_profiles()
        title = "Perfis Disponíveis"
    
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim")
    table.add_column("Nome", style="cyan")
    table.add_column("Codec", style="green")
    table.add_column("CQ", style="yellow")
    table.add_column("Resolução", style="blue")
    table.add_column("Hardware", style="magenta")
    table.add_column("Descrição", style="dim")
    
    for profile in profiles:
        table.add_row(
            profile.get('id', ''),
            profile.get('name', ''),
            profile.get('codec', ''),
            profile.get('cq', '-') or '-',
            profile.get('resolution', '-') or '-',
            profile.get('hardware_category', 'unknown'),
            profile.get('description', '')
        )
    
    console.print(table)


def cmd_profile_create(args, profile_mgr: ProfileManager, menu: Menu):
    """Cria novo perfil."""
    name = args.profile_create
    
    console.print(f"[bold]Criando perfil: {name}[/bold]\n")
    
    codec = menu.ask("Codec", default="hevc_nvenc")
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
    
    console.print(f"[green][OK][/green] Perfil criado com ID: [cyan]{profile_id}[/cyan]")


def cmd_profile_export(args, profile_mgr: ProfileManager):
    """Exporta perfil."""
    profile = profile_mgr.get_profile(args.profile_export) or profile_mgr.get_profile_by_name(args.profile_export)
    
    if not profile:
        console.print(f"[red][X][/red] Perfil não encontrado: {args.profile_export}")
        return
    
    output_file = f"{args.profile_export}.json"
    if profile_mgr.export_profile(args.profile_export, output_file):
        console.print(f"[green][OK][/green] Perfil exportado para: {output_file}")
    else:
        console.print("[red][X][/red] Erro ao exportar perfil")


def cmd_profile_import(args, profile_mgr: ProfileManager):
    """Importa perfil."""
    if not Path(args.profile_import).exists():
        console.print(f"[red][X][/red] Arquivo não encontrado: {args.profile_import}")
        return
    
    if profile_mgr.import_profile(args.profile_import):
        console.print("[green][OK][/green] Perfil(s) importado(s) com sucesso")
    else:
        console.print("[red][X][/red] Erro ao importar perfil")


def cmd_stats(args, stats_mgr: StatsManager):
    """Mostra estatísticas."""
    if args.stats_reset:
        if input("Tem certeza que deseja resetar estatísticas? (y/n): ").lower() == 'y':
            stats_mgr.reset_statistics()
            console.print("[green][OK][/green] Estatísticas resetadas")
        return
    
    if args.stats_export:
        if stats_mgr.export_to_json(args.stats_export):
            console.print(f"[green][OK][/green] Estatísticas exportadas para: {args.stats_export}")
        else:
            console.print("[red][X][/red] Erro ao exportar estatísticas")
        return
    
    summary = stats_mgr.get_summary()
    
    menu = Menu(console)
    menu.show_stats_panel(summary)


def cmd_queue(args, queue_mgr: QueueManager):
    """Gerencia fila."""
    if args.queue_pause:
        queue_mgr.pause()
        console.print("[green][OK][/green] Fila pausada")
        return
    
    if args.queue_resume:
        queue_mgr.resume()
        console.print("[green][OK][/green] Fila retomada")
        return
    
    if args.queue_clear:
        count = queue_mgr.clear_queue()
        console.print(f"[green][OK][/green] {count} job(s) removidos da fila")
        return
    
    queue = queue_mgr.list_queue()
    
    if not queue:
        console.print("[yellow][!][/yellow] Fila vazia")
        return
    
    table = Table(title="Fila de Jobs", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim")
    table.add_column("Job ID", style="dim")
    table.add_column("Input", style="cyan")
    table.add_column("Output", style="green")
    table.add_column("Perfil", style="blue")
    table.add_column("Prioridade", style="yellow")
    
    priorities = {1: 'LOW', 2: 'NORMAL', 3: 'HIGH', 4: 'CRITICAL'}
    
    for i, item in enumerate(queue, 1):
        table.add_row(
            str(i),
            item['job_id'][:8],
            Path(item['input_path']).name[:30],
            Path(item['output_path']).name[:30],
            item['profile'].get('name', '')[:20],
            priorities.get(item['priority'], 'NORMAL')
        )
    
    console.print(table)


def map_encoding_to_job_status(encoding_status: EncodingStatus) -> JobStatus:
    """Mapeia EncodingStatus para JobStatus."""
    mapping = {
        EncodingStatus.PENDING: JobStatus.PENDING,
        EncodingStatus.RUNNING: JobStatus.RUNNING,
        EncodingStatus.COMPLETED: JobStatus.COMPLETED,
        EncodingStatus.FAILED: JobStatus.FAILED,
        EncodingStatus.CANCELLED: JobStatus.CANCELLED,
        EncodingStatus.PAUSED: JobStatus.PAUSED
    }
    return mapping.get(encoding_status, JobStatus.PENDING)


def run_watch_mode(config: ConfigManager, profile_mgr: ProfileManager, job_mgr: JobManager, stats_mgr: StatsManager):
    """Executa modo watch."""
    watch_folders = config.get_watch_folders()
    
    if not watch_folders:
        console.print("[red][X][/red] Nenhuma pasta watch configurada")
        return
    
    console.print("[bold]Modo Watch ativado[/bold]")
    console.print(f"Monitorando {len(watch_folders)} pasta(s)...\n")
    
    for folder in watch_folders:
        console.print(f"  [cyan]{folder['nome']}[/cyan]")
        console.print(f"    Entrada: {folder['entrada']}")
        console.print(f"    Saída: {folder['saida']}")
        console.print(f"    Perfil: {folder.get('profile', 'N/A')}\n")
    
    console.print("\n[yellow]Pressione Ctrl+C para parar[/yellow]")
    
    encoder = EncoderEngine(max_concurrent=config.get('encoding.max_concurrent', 2))
    
    def on_progress(job_id: str, progress: float):
        job_mgr.update_progress(job_id, progress)
    
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
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Parando watch mode...[/yellow]")
        encoder.stop()


def process_queue_cli(config: ConfigManager, job_mgr: JobManager, queue_mgr: QueueManager, stats_mgr: StatsManager):
    """Processa a fila de jobs interativamente."""
    if queue_mgr.get_queue_length() == 0:
        console.print("[yellow][!][/yellow] Fila vazia")
        input("\nPressione Enter para continuar...")
        return

    console.print(f"\n[bold]Processando {queue_mgr.get_queue_length()} job(s) da fila...[/bold]\n")

    from .core.encoder_engine import EncodingJob
    encoder = EncoderEngine(max_concurrent=config.get('encoding.max_concurrent', 2))

    def on_progress(job_id: str, progress: float):
        job_mgr.update_progress(job_id, progress)

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
                source_dir = str(Path(job['input_path']).parent)
                output_dir = str(Path(job['output_path']).parent)
                FileUtils.copy_subtitles_to_output(source_dir, output_dir, Path(job['input_path']).stem)
            queue_mgr.remove_from_queue(job_id)
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
            queue_mgr.remove_from_queue(job_id)
        elif status == EncodingStatus.CANCELLED:
            queue_mgr.remove_from_queue(job_id)

    encoder.add_progress_callback(on_progress)
    encoder.add_status_callback(on_status)
    encoder.start()

    try:
        while True:
            running_count = len(encoder.get_active_jobs())
            pending_in_encoder = len(encoder.get_pending_jobs())
            queue_length = queue_mgr.get_queue_length()

            if (running_count + pending_in_encoder) < 1:
                next_job = queue_mgr.pop_next_job()
                if next_job:
                    encoding_job = EncodingJob(
                        id=next_job['job_id'],
                        input_path=next_job['input_path'],
                        output_path=next_job['output_path'],
                        profile=next_job['profile']
                    )
                    encoder.add_job(encoding_job)
                    console.print(f"[cyan]Iniciando job: {next_job['job_id'][:8]}[/cyan]")

            queue_empty = queue_mgr.get_queue_length() == 0
            if not running_count and not pending_in_encoder and queue_empty:
                break

            # Verifica se tecla 'D' foi pressionada para toggle de debug
            check_debug_key(encoder)
            
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Parando processamento...[/yellow]")
    finally:
        encoder.stop()

    console.print("\n[green][OK][/green] Processamento da fila concluído")
    input("\nPressione Enter para continuar...")


def run_single_file(args, config: ConfigManager, profile_mgr: ProfileManager, job_mgr: JobManager, stats_mgr: StatsManager):
    """Codifica arquivo único."""
    input_path = PathUtils.normalize_path(args.file)
    
    valid, error = validate_video_file(input_path)
    if not valid:
        console.print(f"[red][X][/red] {error}")
        return
    
    profile = None
    if args.profile:
        profile = profile_mgr.get_profile(args.profile) or profile_mgr.get_profile_by_name(args.profile)
        if not profile:
            console.print(f"[red][X][/red] Perfil não encontrado: {args.profile}")
            return
    
    if not profile:
        profile = {
            'codec': args.codec or 'hevc_nvenc',
            'cq': args.cq,
            'bitrate': args.bitrate,
            'preset': args.preset or 'p5',
            'resolution': args.resolution,
            'two_pass': args.two_pass,
            'hdr_to_sdr': args.hdr_to_sdr,
            'deinterlace': args.deinterlace,
            'plex_compatible': True
        }
    
    codec = profile.get('codec', 'hevc_nvenc')
    cq = profile.get('cq')

    # Gerar caminho de output inicial
    if args.output_file:
        output_path = PathUtils.normalize_path(args.output_file)
    elif args.output:
        ensure_directory(args.output)
        output_path = PathUtils.generate_output_path(input_path, args.output, codec=codec, cq=cq, handle_conflict=False)
    else:
        output_path = PathUtils.generate_output_path(input_path, str(Path(input_path).parent), codec=codec, cq=cq, handle_conflict=False)
    
    # Verificar conflito de arquivo existente (modo interativo)
    if Path(output_path).exists():
        console.print(f"\n[yellow]⚠️  Arquivo já existe:[/yellow] {output_path}")
        console.print("[cyan]O que deseja fazer?[/cyan]")
        
        # Opção 1: Substituir
        if Confirm.ask("\nDeseja [bold red]substituir[/bold red] o arquivo existente?", default=False):
            strategy = FileConflictStrategy.OVERWRITE
        # Opção 2: Renomear com numeração
        elif Confirm.ask("Deseja [bold green]criar uma cópia numerada[/bold green] (ex: arquivo_1.mkv)?", default=True):
            strategy = FileConflictStrategy.RENAME
            output_path = FileUtils.generate_unique_filename(output_path)
            console.print(f"[cyan]Novo caminho:[/cyan] {output_path}")
        # Opção 3: Pular
        else:
            console.print("[yellow]Arquivo pulado.[/yellow]")
            return
    
    job_id = job_mgr.create_job(
        input_path=input_path,
        output_path=output_path,
        profile_id=args.profile or 'custom',
        profile_name=profile.get('name', 'Custom') if profile.get('name') else 'Custom'
    )
    
    console.print("[bold]Iniciando encode[/bold]")
    console.print(f"  Input:  {input_path}")
    console.print(f"  Output: {output_path}")
    console.print(f"  Perfil: {profile.get('name', 'Custom')}")
    console.print()
    
    ffmpeg = FFmpegWrapper()
    
    command = ffmpeg.build_encoding_command(
        input_path=input_path,
        output_path=output_path,
        codec=profile.get('codec', 'hevc_nvenc'),
        cq=profile.get('cq'),
        bitrate=profile.get('bitrate'),
        resolution=profile.get('resolution'),
        preset=profile.get('preset', 'p5'),
        two_pass=profile.get('two_pass', False),
        hdr_to_sdr=profile.get('hdr_to_sdr', False),
        deinterlace=profile.get('deinterlace', False),
        plex_compatible=profile.get('plex_compatible', True)
    )
    
    progress_display = ProgressDisplay(console)
    progress_display.start(description="Encoding")
    
    import re
    
    def on_output(output: str):
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
                    progress = (current_seconds / total_seconds) * 100
                    progress_display.update(progress)
    
    success, error = ffmpeg.run_encoding(command, callback=on_output)
    
    progress_display.stop()
    
    if success:
        input_size = get_file_size(input_path)
        output_size = get_file_size(output_path)
        
        stats_mgr.record_encode(
            profile_id=args.profile or 'custom',
            profile_name=profile.get('name', 'Custom') if profile.get('name') else 'Custom',
            success=True,
            duration_seconds=0,
            input_size=input_size,
            output_size=output_size,
            cq_used=profile.get('cq'),
            input_path=input_path,
            output_path=output_path
        )
        
        job_status = map_encoding_to_job_status(EncodingStatus.COMPLETED)
        job_mgr.update_job_status(job_id, job_status, input_size=input_size, output_size=output_size)
        
        console.print("\n[green][OK][/green] Encoding completado!")
        console.print(f"  Output: {output_path}")
        console.print(f"  Tamanho: {PathUtils.format_size(output_size)}")
    else:
        stats_mgr.record_encode(
            profile_id=args.profile or 'custom',
            profile_name=profile.get('name', 'Custom') if profile.get('name') else 'Custom',
            success=False,
            duration_seconds=0,
            input_size=0,
            output_size=0,
            failure_reason=error
        )
        
        job_status = map_encoding_to_job_status(EncodingStatus.FAILED)
        job_mgr.update_job_status(job_id, job_status, error_message=error)
        
        console.print(f"\n[red][X][/red] Encoding falhou: {error}")


def run_folder_mode(args, config: ConfigManager, profile_mgr: ProfileManager, job_mgr: JobManager, queue_mgr: QueueManager):
    """Codifica pasta de vídeos."""
    folder_path = PathUtils.normalize_path(args.folder)
    
    valid, error = validate_directory_exists(folder_path)
    if not valid:
        console.print(f"[red][X][/red] {error}")
        return
    
    video_files = FileUtils.find_video_files(folder_path)
    
    if not video_files:
        console.print("[yellow][!][/yellow] Nenhum vídeo encontrado na pasta")
        return
    
    console.print(f"[bold]Encontrados {len(video_files)} arquivo(s)[/bold]\n")
    
    profile = None
    if args.profile:
        profile = profile_mgr.get_profile(args.profile) or profile_mgr.get_profile_by_name(args.profile)
    
    if not profile:
        console.print("[red][X][/red] Perfil necessário para modo folder. Use -p ou --profile")
        return
    
    output_dir = args.output or str(Path(folder_path) / "converted")
    ensure_directory(output_dir)

    codec = profile.get('codec', 'hevc_nvenc')
    cq = profile.get('cq')

    # Verificar e sugerir nome da pasta de saída
    output_path_obj = Path(output_dir)
    is_valid, msg, suggested_name = FileUtils.validate_output_folder_name(
        str(output_path_obj),
        codec=codec,
        quality=profile.get('resolution')
    )
    if not is_valid and suggested_name:
        console.print(f"[yellow][!][/yellow] {msg}")
        if Confirm.ask(f"Deseja usar o nome sugerido: [cyan]{suggested_name}[/cyan]?", default=True):
            output_dir = str(output_path_obj.parent / suggested_name)
            ensure_directory(output_dir)

    for video_file in video_files:
        rel_path = Path(video_file).relative_to(folder_path)
        rel_parent = rel_path.parent

        if str(rel_parent) != '.':
            # Gerar nome da pasta com codec e qualidade
            base_folder_name = PathUtils.generate_output_dir_name(str(rel_parent), codec, cq)
            
            # Validar nome da pasta gerada
            temp_folder_path = Path(output_dir) / base_folder_name
            is_valid, msg, suggested = FileUtils.validate_output_folder_name(
                str(temp_folder_path),
                codec=codec,
                quality=profile.get('resolution')
            )
            if suggested and not is_valid:
                folder_name = suggested
            else:
                folder_name = base_folder_name
            
            video_output_dir = str(Path(output_dir) / folder_name)
        else:
            video_output_dir = output_dir

        ensure_directory(video_output_dir)
        # Gerar caminho do arquivo sem lidar com conflito automaticamente
        output_path = PathUtils.generate_output_path(video_file, video_output_dir, codec=codec, cq=cq, handle_conflict=False)
        
        # Verificar conflito de arquivo existente
        if Path(output_path).exists():
            console.print(f"\n[yellow]⚠️  Arquivo já existe:[/yellow] {output_path}")
            console.print("[cyan]O que deseja fazer?[/cyan]")
            
            # Opção 1: Substituir
            if Confirm.ask("\nDeseja [bold red]substituir[/bold red] o arquivo existente?", default=False):
                pass  # Mantém output_path original
            # Opção 2: Renomear com numeração
            elif Confirm.ask("Deseja [bold green]criar uma cópia numerada[/bold green] (ex: arquivo_1.mkv)?", default=True):
                output_path = FileUtils.generate_unique_filename(output_path)
                console.print(f"[cyan]Novo caminho:[/cyan] {output_path}")
            # Opção 3: Pular este arquivo
            else:
                console.print(f"[yellow]Arquivo pulado:[/yellow] {video_file}")
                continue

        job_id = job_mgr.create_job(
            input_path=video_file,
            output_path=output_path,
            profile_id=args.profile,
            profile_name=profile['name']
        )

        queue_mgr.add_to_queue(
            job_id=job_id,
            input_path=video_file,
            output_path=output_path,
            profile=profile
        )

        source_dir = str(Path(video_file).parent)
        FileUtils.copy_subtitles_to_output(source_dir, video_output_dir, Path(video_file).stem)

    console.print(f"[green][OK][/green] {len(video_files)} job(s) adicionados à fila")
    console.print("\nUse [cyan]--queue[/cyan] para ver a fila")
    console.print("Use [cyan]--watch[/cyan] para processar a fila")


def run_folder_conversion_cli(config: ConfigManager, profile_mgr: ProfileManager, job_mgr: JobManager, queue_mgr: QueueManager, stats_mgr: StatsManager):
    """Novo workflow de conversão por pasta com scan recursivo e suporte multi-perfil e diretórios remotos."""
    from src.managers.multi_profile_conversion_manager import MultiProfileConversionManager, NamingConvention
    from src.ui.remote_connection_ui import RemoteConnectionUI
    from src.managers.remote_directory_manager import RemoteDirectoryManager, CopyProgress
    
    menu = Menu(console)
    remote_ui = RemoteConnectionUI(console, config)
    remote_manager = RemoteDirectoryManager(config)
    
    # Perguntar se diretório é local ou remoto
    directory_type = remote_ui.ask_directory_type()
    
    temp_dir = None  # Para cleanup posterior
    input_folder = ""
    
    if directory_type == "remote":
        # Configurar conexão remota
        protocol = remote_ui.ask_remote_protocol()
        remote_path, connection_config = remote_ui.configure_remote_directory(protocol)
        
        if not remote_path:
            menu.print_error("Configuração cancelada")
            input("\nPressione Enter para continuar...")
            return
        
        # Testar conexão
        if not Confirm.ask("\nDeseja testar a conexão antes de prosseguir?", default=True):
            success, msg = remote_manager.test_connection(remote_path, connection_config)
            if not success:
                menu.print_error(f"Falha na conexão: {msg}")
                input("\nPressione Enter para continuar...")
                return
        
        # Copiar arquivos para diretório temporário
        menu.print_info("Copiando arquivos do diretório remoto para diretório temporário...")
        
        def on_progress(progress: CopyProgress):
            remote_ui.show_copy_progress(progress)
        
        success, temp_dir, files = remote_manager.copy_directory_to_temp(
            remote_path,
            connection_config,
            progress_callback=on_progress
        )
        
        if not success:
            menu.print_error(f"Erro ao copiar arquivos: {temp_dir}")
            input("\nPressione Enter para continuar...")
            return
        
        input_folder = temp_dir
        menu.print_success(f"Arquivos copiados para: {temp_dir}")
        menu.print_info(f"{len(files)} arquivo(s) de vídeo encontrados")
    else:
        # Diretório local
        input_folder = menu.ask("Pasta de entrada (input)")
        valid, error = validate_directory_exists(input_folder)
        if not valid:
            menu.print_error(error)
            input("\nPressione Enter para continuar...")
            return

    output_folder = menu.ask("Pasta de saída (output)")
    ensure_directory(output_folder)

    mode_options = ["Usar perfil existente", "Selecionar múltiplos perfis", "Configuração manual"]
    mode_choice = menu.show_options(mode_options, "Como deseja configurar a conversão?")

    selected_profile_ids = []
    profile = None

    if mode_choice == 0:
        # Perfil único existente
        profiles = profile_mgr.list_profiles()
        if not profiles:
            menu.print_error("Nenhum perfil encontrado. Crie um perfil primeiro.")
            input("\nPressione Enter para continuar...")
            return
        profile_idx = menu.show_options([p['name'] for p in profiles], "Perfis disponíveis")
        profile = profiles[profile_idx]
        selected_profile_ids = [profile['id']]

    elif mode_choice == 1:
        # Múltiplos perfis
        profiles = profile_mgr.list_profiles()
        if not profiles:
            menu.print_error("Nenhum perfil encontrado. Crie um perfil primeiro.")
            input("\nPressione Enter para continuar...")
            return
        
        selected_profile_ids = menu.show_multi_profile_selection(profiles, "Selecione os Perfis para Conversão")
        
        if not selected_profile_ids:
            menu.print_error("Nenhum perfil selecionado")
            input("\nPressione Enter para continuar...")
            return
        
        # Usar primeiro perfil como referência para codec/cq
        profile = profile_mgr.get_profile(selected_profile_ids[0])

    else:
        # Configuração manual (perfil único)
        codec = menu.ask("Codec", default="hevc_nvenc")
        cq = menu.ask("CQ (Constant Quality, 1-51)", default="24")
        preset = menu.ask("Preset (p1-p7)", default="p5")
        resolution = menu.ask("Resolução (vazio = original)", default="")
        profile = {
            'id': 'manual',
            'name': f'Manual ({codec} CQ{cq})',
            'codec': codec,
            'cq': cq,
            'preset': preset,
            'resolution': resolution if resolution else None,
            'two_pass': False,
            'hdr_to_sdr': False,
            'deinterlace': False,
            'plex_compatible': True
        }
        selected_profile_ids = [profile['id']]

    codec = profile.get('codec', 'hevc_nvenc') if profile else 'hevc_nvenc'
    cq = profile.get('cq') if profile else None

    console.print(f"\n[cyan]Escaneando pasta recursivamente...[/cyan]")
    video_files = FileUtils.find_video_files(input_folder, recursive=True)

    if not video_files:
        menu.print_warning("Nenhum vídeo encontrado na pasta")
        input("\nPressione Enter para continuar...")
        return

    console.print(f"[green]Encontrados {len(video_files)} arquivo(s) de vídeo[/green]\n")

    # Exibir sumário visual dos diretórios e arquivos
    menu.show_directory_summary(input_folder, video_files)

    # Modo multi-perfil: gerar plano e exibir preview
    if len(selected_profile_ids) > 1:
        multi_mgr = MultiProfileConversionManager(
            profile_manager=profile_mgr,
            job_manager=job_mgr,
            queue_manager=queue_mgr
        )
        
        # Validar perfis
        is_valid, msg = multi_mgr.validate_profiles_compatibility(selected_profile_ids)
        if not is_valid:
            menu.print_error(msg)
            input("\nPressione Enter para continuar...")
            return
        
        # Gerar plano de conversão
        plan = multi_mgr.generate_conversion_plan(
            input_files=video_files,
            profile_ids=selected_profile_ids,
            output_folder=output_folder,
            options={
                'preserve_structure': True,
                'naming_convention': NamingConvention.PROFILE_SUFFIX.value
            }
        )
        
        # Exibir preview do plano
        while True:
            preview_action = menu.show_conversion_plan_preview(plan, video_files)
            
            if preview_action == 0:  # Confirmar
                # Criar jobs para múltiplos perfis
                jobs = multi_mgr.create_jobs_for_multiple_profiles(
                    input_files=video_files,
                    profile_ids=selected_profile_ids,
                    output_folder=output_folder,
                    options={
                        'preserve_structure': True,
                        'naming_convention': NamingConvention.PROFILE_SUFFIX.value
                    }
                )
                
                menu.print_success(f"{len(jobs)} jobs criados e adicionados à fila!")
                console.print(f"[cyan]Fila total: {queue_mgr.get_queue_length()} jobs[/cyan]")
                
                # Copiar legendas
                for job in jobs:
                    source_dir = str(Path(job['input_path']).parent)
                    output_dir = str(Path(job['output_path']).parent)
                    FileUtils.copy_subtitles_to_output(source_dir, output_dir, Path(job['input_path']).stem)
                
                console.print(f"[cyan]Legendas copiadas para os diretórios de saída[/cyan]")
                
                # Perguntar se deseja processar agora
                if menu.ask_confirm("Deseja processar a fila agora?", default=True):
                    process_queue_cli(config, job_mgr, queue_mgr, stats_mgr)
                
                break
            
            elif preview_action == 1:  # Reorganizar perfis
                # Voltar para seleção de perfis
                selected_profile_ids = menu.show_multi_profile_selection(
                    profile_mgr.list_profiles(),
                    "Selecione os Perfis para Conversão"
                )
                
                if not selected_profile_ids:
                    menu.print_warning("Operação cancelada")
                    break
                
                # Regenerar plano
                plan = multi_mgr.generate_conversion_plan(
                    input_files=video_files,
                    profile_ids=selected_profile_ids,
                    output_folder=output_folder,
                    options={
                        'preserve_structure': True,
                        'naming_convention': NamingConvention.PROFILE_SUFFIX.value
                    }
                )
            
            elif preview_action == 2:  # Editar perfis individualmente
                # Editar perfis individualmente
                edited_profiles = multi_mgr.edit_individual_profiles_interactive(
                    selected_profile_ids,
                    profile_mgr
                )
                
                # Atualizar os IDs dos perfis selecionados com os perfis editados
                edited_profile_ids = []
                for edited_profile in edited_profiles:
                    # Atualizar o perfil no gerenciador
                    profile_id = edited_profile['id']
                    profile_mgr.update_profile(profile_id, **edited_profile)
                    edited_profile_ids.append(profile_id)
                
                # Regenerar plano com os perfis editados
                plan = multi_mgr.generate_conversion_plan(
                    input_files=video_files,
                    profile_ids=edited_profile_ids,
                    output_folder=output_folder,
                    options={
                        'preserve_structure': True,
                        'naming_convention': NamingConvention.PROFILE_SUFFIX.value
                    }
                )
            
            elif preview_action == 3:  # Cancelar
                menu.print_warning("Operação cancelada")
                input("\nPressione Enter para continuar...")
                break
            
            else:  # Cancelar
                menu.print_warning("Operação cancelada")
                input("\nPressione Enter para continuar...")
                break
        
        return

    # Modo perfil único: fluxo existente
    while True:
        action_choice = menu.show_pre_conversion_summary(
            input_folder=input_folder,
            output_folder=output_folder,
            video_files=video_files,
            profile=profile
        )

        if action_choice == 0:  # 🚀 Iniciar conversão agora
            # Adicionar todos os jobs à fila e processar imediatamente
            for video_file in video_files:
                rel_path = Path(video_file).relative_to(input_folder)
                rel_parent = rel_path.parent

                if str(rel_parent) != '.':
                    folder_name = PathUtils.generate_output_dir_name(str(rel_parent), codec, cq)
                    video_output_dir = str(Path(output_folder) / folder_name)
                else:
                    root_name = Path(input_folder).name
                    folder_name = PathUtils.generate_output_dir_name(root_name, codec, cq)
                    video_output_dir = str(Path(output_folder) / folder_name)

                ensure_directory(video_output_dir)
                output_path = PathUtils.generate_output_path(video_file, video_output_dir, codec=codec, cq=cq)

                job_id = job_mgr.create_job(
                    input_path=video_file,
                    output_path=output_path,
                    profile_id=profile.get('id', 'manual'),
                    profile_name=profile.get('name', 'Manual')
                )

                queue_mgr.add_to_queue(
                    job_id=job_id,
                    input_path=video_file,
                    output_path=output_path,
                    profile=profile
                )

                source_dir = str(Path(video_file).parent)
                FileUtils.copy_subtitles_to_output(source_dir, video_output_dir, Path(video_file).stem)

            menu.print_success(f"{len(video_files)} job(s) adicionados à fila e processamento iniciado")
            console.print(f"[cyan]Legendas copiadas para os diretórios de saída[/cyan]")
            console.print()
            process_queue_cli(config, job_mgr, queue_mgr, stats_mgr)
            
            # Cleanup do diretório temporário se for diretório remoto
            if directory_type == "remote" and temp_dir and remote_manager.should_auto_cleanup():
                menu.print_info("Limpando diretório temporário...")
                remote_manager.cleanup_temp(temp_dir)
                menu.print_success("Diretório temporário removido")
            
            break

        elif action_choice == 1:  # 📋 Adicionar à fila
            # Adicionar todos os jobs à fila sem processar
            for video_file in video_files:
                rel_path = Path(video_file).relative_to(input_folder)
                rel_parent = rel_path.parent

                if str(rel_parent) != '.':
                    folder_name = PathUtils.generate_output_dir_name(str(rel_parent), codec, cq)
                    video_output_dir = str(Path(output_folder) / folder_name)
                else:
                    root_name = Path(input_folder).name
                    folder_name = PathUtils.generate_output_dir_name(root_name, codec, cq)
                    video_output_dir = str(Path(output_folder) / folder_name)

                ensure_directory(video_output_dir)
                output_path = PathUtils.generate_output_path(video_file, video_output_dir, codec=codec, cq=cq)

                job_id = job_mgr.create_job(
                    input_path=video_file,
                    output_path=output_path,
                    profile_id=profile.get('id', 'manual'),
                    profile_name=profile.get('name', 'Manual')
                )

                queue_mgr.add_to_queue(
                    job_id=job_id,
                    input_path=video_file,
                    output_path=output_path,
                    profile=profile
                )

                source_dir = str(Path(video_file).parent)
                FileUtils.copy_subtitles_to_output(source_dir, video_output_dir, Path(video_file).stem)

            menu.print_success(f"{len(video_files)} job(s) adicionados à fila")
            console.print(f"[cyan]Legendas copiadas para os diretórios de saída[/cyan]")
            console.print()
            console.print(f"[cyan]Jobs na fila: {queue_mgr.get_queue_length()}[/cyan]")
            console.print("[dim]Use a opção 'Ver fila de jobs' no menu principal para gerenciar[/dim]")
            
            # Cleanup do diretório temporário se for diretório remoto
            if directory_type == "remote" and temp_dir and remote_manager.should_auto_cleanup():
                menu.print_info("Limpando diretório temporário...")
                remote_manager.cleanup_temp(temp_dir)
                menu.print_success("Diretório temporário removido")
            
            input("\nPressione Enter para continuar...")
            break

        elif action_choice == 2:  # ⚙️ Configurações avançadas
            # Abrir editor de perfil
            profile = menu.show_advanced_profile_editor(profile, profile_mgr)
            # Atualizar codec e cq após edição
            codec = profile.get('codec', 'hevc_nvenc')
            cq = profile.get('cq')
            # Atualizar nome do perfil se for manual
            if profile.get('id') == 'manual':
                profile['name'] = f"Manual ({codec} CQ{cq or profile.get('bitrate', 'auto')})"

        elif action_choice == 3:  # ⏮ Voltar
            menu.print_warning("Operação cancelada")
            input("\nPressione Enter para continuar...")
            break


def run_folder_conversion_submenu(config: ConfigManager, profile_mgr: ProfileManager, job_mgr: JobManager, queue_mgr: QueueManager, stats_mgr: StatsManager):
    """Exibe submenu de codificação de pasta com opções única e recorrente."""
    menu = Menu(console)

    while True:
        menu.clear()
        menu.print_header("Codificação de Pasta", "Selecione o tipo de codificação")

        options = [
            {"description": "Codificação Única (manual)", "shortcut": "1"},
            {"description": "Codificação Recorrente (automática)", "shortcut": "2"},
            {"description": "Voltar", "shortcut": "0"}
        ]

        choice = menu.show_menu("Submenu", options)

        if choice == 0:
            run_single_folder_conversion(config, profile_mgr, job_mgr, queue_mgr, stats_mgr)
        elif choice == 1:
            run_recurrent_folder_from_submenu(config, profile_mgr)
        elif choice == 2:
            break


def run_single_folder_conversion(config: ConfigManager, profile_mgr: ProfileManager, job_mgr: JobManager, queue_mgr: QueueManager, stats_mgr: StatsManager):
    """Executa codificação única de pasta (funcionalidade existente)."""
    run_folder_conversion_cli(config, profile_mgr, job_mgr, queue_mgr, stats_mgr)


def run_recurrent_folder_from_submenu(config: ConfigManager, profile_mgr: ProfileManager):
    """Executa codificação recorrente a partir do submenu."""
    recurrent_ui = RecurrentFolderUI(console, config, profile_mgr)
    recurrent_ui.run()


def run_interactive_mode(config: ConfigManager, profile_mgr: ProfileManager, job_mgr: JobManager, queue_mgr: QueueManager, stats_mgr: StatsManager):
    """Executa modo interativo."""
    menu = Menu(console)

    while True:
        menu.clear()
        menu.print_header("NVENC Encoder Pro v2.0", "Modo Interativo")

        options = [
            {"description": "Codificação de Pasta", "shortcut": "1"},
            {"description": "Codificar arquivo único", "shortcut": "2"},
            {"description": "Ver fila de jobs", "shortcut": "3"},
            {"description": "Gerenciar Perfis", "shortcut": "4"},
            {"description": "Ver estatísticas", "shortcut": "5"},
            {"description": "Gerenciar Conversões Recorrentes", "shortcut": "6"},
            {"description": "Sair", "shortcut": "7"}
        ]

        choice = menu.show_menu("Menu Principal", options)

        if choice == 0:
            run_folder_conversion_submenu(config, profile_mgr, job_mgr, queue_mgr, stats_mgr)
        elif choice == 1:
            run_single_file_cli(config, profile_mgr, job_mgr, queue_mgr, stats_mgr)
        elif choice == 2:
            from .ui.queue_menu import show_queue_submenu
            show_queue_submenu(menu, queue_mgr, job_mgr)
        elif choice == 3:
            run_profile_manager_cli(menu, profile_mgr)
        elif choice == 4:
            stats = stats_mgr.get_summary()
            menu.show_stats_panel(stats)
            input("\nPressione Enter para continuar...")
        elif choice == 5:
            run_recurrent_folder_from_submenu(config, profile_mgr)
        elif choice == 6:
            break


def validate_video_file(path: str) -> tuple[bool, str]:
    """Valida se arquivo é vídeo."""
    video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpeg', '.mpg'}
    
    if not Path(path).exists():
        return False, f"Arquivo não encontrado: {path}"
    
    if not Path(path).is_file():
        return False, f"Não é um arquivo: {path}"
    
    ext = Path(path).suffix.lower()
    if ext not in video_extensions:
        return False, f"Extensão não suportada: {ext}"
    
    return True, ""


def validate_directory_exists(path: str, create_if_not: bool = False) -> tuple[bool, str]:
    """Valida se diretório existe."""
    if not path:
        return False, "Caminho vazio"
    
    path_obj = Path(path)
    
    if not path_obj.exists():
        if create_if_not:
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
                return True, ""
            except Exception as e:
                return False, f"Erro ao criar diretório: {e}"
        return False, f"Diretório não encontrado: {path}"
    
    if not path_obj.is_dir():
        return False, f"Não é um diretório: {path}"
    
    return True, ""


def ensure_directory(directory: str) -> bool:
    """Cria diretório se não existir."""
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def get_file_size(path: str) -> int:
    """Retorna tamanho do arquivo em bytes."""
    try:
        return Path(path).stat().st_size
    except Exception:
        return 0


def run_single_file_cli(config: ConfigManager, profile_mgr: ProfileManager, job_mgr: JobManager, queue_mgr: QueueManager, stats_mgr: StatsManager):
    """CLI para arquivo único."""
    menu = Menu(console)
    
    input_path = menu.ask("Caminho do arquivo de vídeo")
    
    valid, error = validate_video_file(input_path)
    if not valid:
        menu.print_error(error)
        input("\nPressione Enter para continuar...")
        return
    
    profiles = profile_mgr.list_profiles()
    if not profiles:
        menu.print_error("Nenhum perfil encontrado. Crie um perfil primeiro.")
        input("\nPressione Enter para continuar...")
        return
    profile_idx = menu.show_options([p['name'] for p in profiles], "Perfis disponíveis")
    profile = profiles[profile_idx]
    
    output_dir = menu.ask("Diretório de output", default=str(Path(input_path).parent))
    ensure_directory(output_dir)

    codec = profile.get('codec', 'hevc_nvenc')
    cq = profile.get('cq')
    output_path = PathUtils.generate_output_path(input_path, output_dir, codec=codec, cq=cq)
    
    # Exibir sumário pré-conversão para arquivo único
    while True:
        # Criar lista fictícia para o sumário
        video_files = [input_path]
        
        action_choice = menu.show_pre_conversion_summary(
            input_folder=str(Path(input_path).parent),
            output_folder=output_dir,
            video_files=video_files,
            profile=profile
        )
        
        if action_choice == 0:  # 🚀 Iniciar conversão agora
            job_id = job_mgr.create_job(
                input_path=input_path,
                output_path=output_path,
                profile_id=profile['id'],
                profile_name=profile['name']
            )
            
            queue_mgr.add_to_queue(
                job_id=job_id,
                input_path=input_path,
                output_path=output_path,
                profile=profile
            )
            
            menu.print_success("Job adicionado à fila e processamento iniciado")
            process_queue_cli(config, job_mgr, queue_mgr, stats_mgr)
            break
        
        elif action_choice == 1:  # 📋 Adicionar à fila
            job_id = job_mgr.create_job(
                input_path=input_path,
                output_path=output_path,
                profile_id=profile['id'],
                profile_name=profile['name']
            )
            
            queue_mgr.add_to_queue(
                job_id=job_id,
                input_path=input_path,
                output_path=output_path,
                profile=profile
            )
            
            menu.print_success("Job adicionado à fila")
            console.print(f"[cyan]Jobs na fila: {queue_mgr.get_queue_length()}[/cyan]")
            console.print("[dim]Use a opção 'Ver fila de jobs' no menu principal para gerenciar[/dim]")
            input("\nPressione Enter para continuar...")
            break
        
        elif action_choice == 2:  # ⚙️ Configurações avançadas
            # Abrir editor de perfil
            profile = menu.show_advanced_profile_editor(profile, profile_mgr)
            # Atualizar codec e cq após edição
            codec = profile.get('codec', 'hevc_nvenc')
            cq = profile.get('cq')
            # Regenerar output path com novas configurações
            output_path = PathUtils.generate_output_path(input_path, output_dir, codec=codec, cq=cq)
        
        elif action_choice == 3:  # ⏮ Voltar
            menu.print_warning("Operação cancelada")
            input("\nPressione Enter para continuar...")
            break


def run_folder_mode_cli(config: ConfigManager, profile_mgr: ProfileManager, job_mgr: JobManager, queue_mgr: QueueManager, stats_mgr: StatsManager):
    """CLI para pasta."""
    menu = Menu(console)

    folder_path = menu.ask("Caminho da pasta")

    valid, error = validate_directory_exists(folder_path)
    if not valid:
        menu.print_error(error)
        input("\nPressione Enter para continuar...")
        return

    profiles = profile_mgr.list_profiles()
    if not profiles:
        menu.print_error("Nenhum perfil encontrado. Crie um perfil primeiro.")
        input("\nPressione Enter para continuar...")
        return
    profile_idx = menu.show_options([p['name'] for p in profiles], "Perfis disponíveis")
    profile = profiles[profile_idx]

    output_dir = menu.ask("Diretório de output", default=str(Path(folder_path) / "converted"))
    ensure_directory(output_dir)

    codec = profile.get('codec', 'hevc_nvenc')
    cq = profile.get('cq')

    video_files = FileUtils.find_video_files(folder_path)

    if not video_files:
        menu.print_warning("Nenhum vídeo encontrado na pasta")
        input("\nPressione Enter para continuar...")
        return

    queue_was_empty = queue_mgr.get_queue_length() == 0

    for video_file in video_files:
        rel_path = Path(video_file).relative_to(folder_path)
        rel_parent = rel_path.parent

        if str(rel_parent) != '.':
            folder_name = PathUtils.generate_output_dir_name(str(rel_parent), codec, cq)
            video_output_dir = str(Path(output_dir) / folder_name)
        else:
            video_output_dir = output_dir

        ensure_directory(video_output_dir)
        output_path = PathUtils.generate_output_path(video_file, video_output_dir, codec=codec, cq=cq)

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

        source_dir = str(Path(video_file).parent)
        FileUtils.copy_subtitles_to_output(source_dir, video_output_dir, Path(video_file).stem)

    menu.print_success(f"{len(video_files)} job(s) adicionados à fila")

    if queue_was_empty:
        options = ["Iniciar conversão agora", "Voltar ao menu"]
        choice = menu.show_options(options, "Fila estava vazia - o que deseja fazer?")
        if choice == 0:
            process_queue_cli(config, job_mgr, queue_mgr, stats_mgr)
    else:
        console.print(f"[cyan]Jobs na fila: {queue_mgr.get_queue_length()}[/cyan]")
        input("\nPressione Enter para continuar...")


def run_profile_manager_cli(menu: Menu, profile_mgr: ProfileManager):
    """CLI para gerenciar perfis."""
    while True:
        menu.clear()
        menu.print_header("Gerenciador de Perfis")
        
        options = [
            {"description": "Listar perfis", "shortcut": "1"},
            {"description": "Criar novo perfil", "shortcut": "2"},
            {"description": "Voltar", "shortcut": "0"}
        ]
        
        choice = menu.show_menu("Menu", options)
        
        if choice == 0:
            profiles = profile_mgr.list_profiles()
            menu.show_profiles_table(profiles)
            input("\nPressione Enter para continuar...")
        elif choice == 1:
            name = menu.ask("Nome do perfil")
            codec = menu.ask("Codec", default="hevc_nvenc")
            cq = menu.ask("CQ", default="24")
            profile_mgr.create_profile(name=name, codec=codec, cq=cq)
            menu.print_success("Perfil criado")
            time.sleep(1)
        elif choice == 2:
            break


def main():
    """Ponto de entrada principal."""
    parser = create_parser()
    args = parser.parse_args()
    
    config = ConfigManager(args.config) if args.config else ConfigManager()
    profile_mgr = ProfileManager()
    
    # Usar o novo UnifiedQueueManager em vez de QueueManager e JobManager separados
    unified_queue_mgr = UnifiedQueueManager()
    
    # Usar UnifiedQueueManager para ambas as referências (queue_mgr E job_mgr)
    # Isso garante que toda a aplicação use um único gerenciador unificado
    job_mgr = unified_queue_mgr  # UnifiedQueueManager tem métodos de compatibilidade
    queue_mgr = unified_queue_mgr  # UnifiedQueueManager substitui ambos
    stats_mgr = StatsManager()
    menu = Menu(console)
    
    if args.check:
        cmd_check(args, config)
        return
    
    if args.detect_hardware:
        cmd_detect_hardware(args, profile_mgr)
        return
    
    if args.profile_list:
        cmd_profile_list(args, profile_mgr)
        return
    
    if args.profile_create:
        cmd_profile_create(args, profile_mgr, menu)
        return
    
    if args.profile_export:
        cmd_profile_export(args, profile_mgr)
        return
    
    if args.profile_import:
        cmd_profile_import(args, profile_mgr)
        return
    
    if args.stats or args.stats_export or args.stats_reset:
        cmd_stats(args, stats_mgr)
        return
    
    if args.queue or args.queue_pause or args.queue_resume or args.queue_clear:
        cmd_queue(args, queue_mgr)
        return
    
    if args.watch:
        run_watch_mode(config, profile_mgr, job_mgr, stats_mgr)
        return
    
    if args.file:
        run_single_file(args, config, profile_mgr, job_mgr, stats_mgr)
        return
    
    if args.folder:
        run_folder_mode(args, config, profile_mgr, job_mgr, queue_mgr)
        return
    
    if args.interactive:
        run_interactive_mode(config, profile_mgr, job_mgr, queue_mgr, stats_mgr)
        return
    
    run_interactive_mode(config, profile_mgr, job_mgr, queue_mgr, stats_mgr)


if __name__ == '__main__':
    main()
