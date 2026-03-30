import argparse
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .managers.config_manager import ConfigManager
from .managers.profile_manager import ProfileManager
from .managers.job_manager import JobManager, JobStatus
from .managers.stats_manager import StatsManager
from .managers.queue_manager import QueueManager
from .core.ffmpeg_wrapper import FFmpegWrapper
from .core.hw_monitor import HardwareMonitor
from .core.encoder_engine import EncoderEngine, EncodingStatus
from .utils.path_utils import PathUtils
from .utils.file_utils import FileUtils
from .ui.menu import Menu
from .ui.progress import ProgressDisplay


console = Console()


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


def cmd_profile_list(args, profile_mgr: ProfileManager):
    """Lista perfis."""
    profiles = profile_mgr.list_profiles()
    
    table = Table(title="Perfis Disponíveis", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim")
    table.add_column("Nome", style="cyan")
    table.add_column("Codec", style="green")
    table.add_column("CQ", style="yellow")
    table.add_column("Resolução", style="blue")
    table.add_column("Descrição", style="dim")
    
    for profile in profiles:
        table.add_row(
            profile.get('id', ''),
            profile.get('name', ''),
            profile.get('codec', ''),
            profile.get('cq', '-') or '-',
            profile.get('resolution', '-') or '-',
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
    
    if args.output_file:
        output_path = PathUtils.normalize_path(args.output_file)
    elif args.output:
        ensure_directory(args.output)
        output_path = PathUtils.generate_output_path(input_path, args.output, suffix="-encoded")
    else:
        output_path = PathUtils.generate_output_path(input_path, str(Path(input_path).parent), suffix="-encoded")
    
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
    
    for video_file in video_files:
        output_path = PathUtils.generate_output_path(video_file, output_dir, suffix="-encoded")
        
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
    
    console.print(f"[green][OK][/green] {len(video_files)} job(s) adicionados à fila")
    console.print("\nUse [cyan]--queue[/cyan] para ver a fila")
    console.print("Use [cyan]--watch[/cyan] para processar a fila")


def run_interactive_mode(config: ConfigManager, profile_mgr: ProfileManager, job_mgr: JobManager, queue_mgr: QueueManager, stats_mgr: StatsManager):
    """Executa modo interativo."""
    menu = Menu(console)
    
    while True:
        menu.clear()
        menu.print_header("NVENC Encoder Pro v2.0", "Modo Interativo")
        
        options = [
            {"description": "Codificar arquivo único", "shortcut": "1"},
            {"description": "Codificar pasta", "shortcut": "2"},
            {"description": "Ver fila de jobs", "shortcut": "3"},
            {"description": "Gerenciar perfis", "shortcut": "4"},
            {"description": "Ver estatísticas", "shortcut": "5"},
            {"description": "Sair", "shortcut": "0"}
        ]
        
        choice = menu.show_menu("Menu Principal", options)
        
        if choice == 0:
            run_single_file_cli(config, profile_mgr, job_mgr, stats_mgr)
        elif choice == 1:
            run_folder_mode_cli(config, profile_mgr, job_mgr, queue_mgr)
        elif choice == 2:
            queue = queue_mgr.list_queue()
            if queue:
                menu.show_jobs_table([{"id": q['job_id'], "input_path": q['input_path'], "profile_name": q['profile'].get('name', ''), "status": "queued", "progress": 0} for q in queue])
            else:
                menu.print_info("Fila vazia")
            input("\nPressione Enter para continuar...")
        elif choice == 3:
            run_profile_manager_cli(menu, profile_mgr)
        elif choice == 4:
            stats = stats_mgr.get_summary()
            menu.show_stats_panel(stats)
            input("\nPressione Enter para continuar...")
        elif choice == 5:
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


def run_single_file_cli(config: ConfigManager, profile_mgr: ProfileManager, job_mgr: JobManager, stats_mgr: StatsManager):
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
    
    output_path = PathUtils.generate_output_path(input_path, output_dir, suffix="-encoded")
    
    _job_id = job_mgr.create_job(
        input_path=input_path,
        output_path=output_path,
        profile_id=profile['id'],
        profile_name=profile['name']
    )
    
    console.print("\n[bold]Iniciando encode[/bold]")
    console.print(f"  Input:  {input_path}")
    console.print(f"  Output: {output_path}")
    console.print(f"  Perfil: {profile['name']}")
    
    input("\nPressione Enter para continuar...")


def run_folder_mode_cli(config: ConfigManager, profile_mgr: ProfileManager, job_mgr: JobManager, queue_mgr: QueueManager):
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
    
    video_files = FileUtils.find_video_files(folder_path)
    
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
    
    menu.print_success(f"{len(video_files)} job(s) adicionados à fila")
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
    job_mgr = JobManager()
    queue_mgr = QueueManager()
    stats_mgr = StatsManager()
    menu = Menu(console)
    
    if args.check:
        cmd_check(args, config)
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
    
    parser.print_help()


if __name__ == '__main__':
    main()
