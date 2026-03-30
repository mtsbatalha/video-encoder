#!/usr/bin/env python3
"""
Demo do Monitor em Tempo Real
Este script demonstra a interface do monitor sem precisar de um vídeo real.
"""

import time
import random
from rich.console import Console
from src.ui.realtime_monitor import RealTimeEncodingMonitor

console = Console()

def main():
    console.print("[bold magenta]╭──────────────────────────────────────────────────────────────╮[/bold magenta]")
    console.print("[bold magenta]│[/bold magenta]  [bold white]Demo do Monitor em Tempo Real - NVENC Encoder[/bold white]  [bold magenta]│[/bold magenta]")
    console.print("[bold magenta]╰──────────────────────────────────────────────────────────────╯[/bold magenta]")
    console.print()
    console.print("[yellow]Este é um teste da interface do monitor em tempo real.[/yellow]")
    console.print("[yellow]Pressione Ctrl+C para parar a qualquer momento.[/yellow]")
    console.print()
    input("Pressione Enter para iniciar a demo...")
    
    # Criar monitor
    monitor = RealTimeEncodingMonitor(console)
    
    # Iniciar monitor com dados fictícios
    monitor.start(
        description="Demo: Tubarão.1975.1080p.mkv",
        total_duration=7200,  # 2 horas em segundos
        input_file="C:/Videos/Tubarão.1975.1080p.mkv",
        output_file="C:/Videos/Output/Tubarão.1975.1080p_encoded.mkv"
    )
    
    start_time = time.time()
    progress = 0
    
    try:
        while progress < 100:
            # Simular progresso
            elapsed = time.time() - start_time
            progress = min(100, (elapsed / 30) * 100)  # 30 segundos para completar
            
            # Simular tempo atual do vídeo
            current_time = (progress / 100) * 7200
            
            # Simular estatísticas de encoding
            fps = random.uniform(45, 65)
            speed = random.uniform(1.5, 2.5)
            bitrate = random.uniform(8000, 12000)
            
            # Simular stats de hardware
            gpu_util = random.randint(75, 95)
            gpu_temp = random.randint(65, 78)
            gpu_memory = random.randint(5500, 6500)
            cpu_util = random.randint(40, 70)
            
            # Atualizar monitor
            monitor.update_progress(progress, current_time)
            monitor.update_encoding_stats(fps=fps, speed=speed, bitrate=bitrate)
            monitor.update_hw_stats({
                'gpu_util': gpu_util,
                'gpu_temperature': gpu_temp,
                'gpu_memory_used': gpu_memory,
                'gpu_memory_total': 8192,
                'cpu_util': cpu_util
            })
            
            monitor.update_status("Processando job...")
            
            time.sleep(0.5)
        
        monitor.update_status("✓ Completado!")
        time.sleep(2)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrompida pelo usuário.[/yellow]")
    finally:
        monitor.stop()
    
    console.print("\n[green]✓ Demo finalizada com sucesso![/green]")
    console.print()
    console.print("Agora você pode usar o monitor em tempo real com seus vídeos:")
    console.print("  1. Execute [cyan]python vigia_nvenc.py[/cyan]")
    console.print("  2. Adicione vídeos à fila (opção 1 ou 2)")
    console.print("  3. Vá em [cyan]Ver fila de jobs[/cyan] (opção 4)")
    console.print("  4. Selecione [cyan]⚡ Processar fila agora[/cyan] (opção 6)")
    console.print()

if __name__ == '__main__':
    main()
