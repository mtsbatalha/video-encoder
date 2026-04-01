"""Script de teste para validar correções de debug toggle."""
import time
from pathlib import Path
from src.core.encoder_engine import EncoderEngine, EncodingJob
from src.core.ffmpeg_wrapper import FFmpegWrapper
from src.core.hw_monitor import HardwareMonitor
from src.ui.realtime_monitor import RealTimeEncodingMonitor
from rich.console import Console

console = Console()

def main():
    """Testa o sistema de debug toggle."""
    
    console.print("\n[bold cyan]🧪 Teste de Debug Toggle[/bold cyan]\n")
    console.print("Este teste irá:")
    console.print("1. Iniciar uma conversão de vídeo")
    console.print("2. Pressione 'D' para ATIVAR o debug (logs aparecerão EMBAIXO do monitor)")
    console.print("3. Pressione 'D' novamente para DESATIVAR o debug (logs desaparecerão)")
    console.print("\n[yellow]Observações:[/yellow]")
    console.print("• Com debug DESATIVADO: Nenhuma mensagem de debug deve aparecer no topo")
    console.print("• Com debug ATIVADO: Logs de debug devem aparecer EMBAIXO do painel de monitoramento")
    console.print("• O toggle deve funcionar imediatamente ao pressionar 'D'\n")
    
    input("Pressione Enter para iniciar o teste...")
    
    # Verifica se existe um arquivo de vídeo de teste
    test_video = None
    possible_paths = [
        Path("test_video.mp4"),
        Path("sample.mp4"),
        Path("test.mkv"),
    ]
    
    for path in possible_paths:
        if path.exists():
            test_video = path
            break
    
    if not test_video:
        console.print("\n[yellow]⚠️  Nenhum arquivo de vídeo de teste encontrado.[/yellow]")
        console.print("Por favor, coloque um arquivo de vídeo de teste (test_video.mp4) na pasta raiz.")
        console.print("\n[dim]Você pode usar qualquer vídeo pequeno para teste.[/dim]")
        return
    
    console.print(f"\n[green]✓[/green] Arquivo de teste encontrado: {test_video}")
    
    # Cria output path
    output_path = Path("output_test") / f"encoded_{test_video.name}"
    output_path.parent.mkdir(exist_ok=True)
    
    # Cria instâncias
    ffmpeg = FFmpegWrapper()
    hw_monitor = HardwareMonitor()
    realtime_monitor = RealTimeEncodingMonitor()
    encoder = EncoderEngine(
        ffmpeg_wrapper=ffmpeg,
        hw_monitor=hw_monitor,
        realtime_monitor=realtime_monitor,
        max_concurrent=1
    )
    
    # Profile de teste
    profile = {
        'name': 'Test Profile',
        'codec': 'hevc_nvenc',
        'cq': '25',
        'preset': 'p5',
        'plex_compatible': True
    }
    
    # Cria job
    job = EncodingJob(
        id='test-job-001',
        input_path=str(test_video),
        output_path=str(output_path),
        profile=profile
    )
    
    console.print(f"\n[cyan]Iniciando conversão...[/cyan]")
    console.print(f"[dim]Input: {test_video}[/dim]")
    console.print(f"[dim]Output: {output_path}[/dim]\n")
    
    # Registra callbacks para monitorar o progresso
    def on_progress(job_id: str, progress: float):
        pass  # O realtime_monitor já exibe o progresso
    
    def on_status(job_id: str, status):
        if status.value == 'completed':
            console.print(f"\n[green]✓[/green] Conversão concluída!")
        elif status.value == 'failed':
            console.print(f"\n[red]✗[/red] Conversão falhou")
    
    encoder.add_progress_callback(on_progress)
    encoder.add_status_callback(on_status)
    
    # Inicia engine
    encoder.start()
    encoder.add_job(job)
    
    # Loop de monitoramento com verificação de tecla D
    from src.cli import check_debug_key
    
    try:
        while True:
            # Verifica se a tecla D foi pressionada
            check_debug_key(encoder)
            
            # Verifica status dos jobs
            active = encoder.get_active_jobs()
            pending = encoder.get_pending_jobs()
            
            if not active and not pending:
                break
            
            time.sleep(0.5)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrompido pelo usuário[/yellow]")
    finally:
        encoder.stop()
    
    console.print("\n[bold green]✓ Teste concluído![/bold green]\n")
    
    # Verifica se o arquivo de saída foi criado
    if output_path.exists():
        console.print(f"[green]✓[/green] Arquivo de saída criado: {output_path}")
    else:
        console.print(f"[yellow]⚠️[/yellow] Arquivo de saída não foi criado")

if __name__ == "__main__":
    main()
