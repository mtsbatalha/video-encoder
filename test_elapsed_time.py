#!/usr/bin/env python3
"""Script de teste para verificar se o tempo decorrido e exibido corretamente."""

import time
from src.ui.realtime_monitor import RealTimeEncodingMonitor
from rich.console import Console


def test_elapsed_time_display():
    """Testa a exibicao do tempo decorrido no monitor."""
    console = Console()
    monitor = RealTimeEncodingMonitor(console)
    
    print("Testando exibicao de tempo decorrido...")
    
    # Iniciar o monitor
    monitor.start(
        description="Teste de tempo decorrido",
        total_duration=100.0,  # 100 segundos de duracao total estimada
        input_file="teste_input.mp4",
        output_file="teste_output.mp4"
    )
    
    # Simular progresso por alguns segundos
    for i in range(10):
        progress = i * 10  # Incrementar progresso de 10 em 10%
        monitor.update_progress(progress, current_time=i*10)  # Simular tempo atual do video
        
        print(f"Progresso: {progress}%")
        
        time.sleep(1)  # Esperar 1 segundo entre atualizacoes
    
    # Parar o monitor
    monitor.stop()
    
    print("Teste concluido!")
    print("O tempo decorrido deve estar sendo exibido na tabela de estatisticas.")


if __name__ == "__main__":
    test_elapsed_time_display()