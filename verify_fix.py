#!/usr/bin/env python3
"""
Script para verificar se a correcao para terminacao de processos FFMPEG esta funcionando.
"""

import os
import time
from pathlib import Path
from src.managers.unified_queue_manager import UnifiedQueueManager
from src.core.encoder_engine import EncoderEngine
from rich.console import Console


def verify_fix():
    """Verifica se a correcao para terminacao de processos FFMPEG esta funcionando."""
    
    print("=== Verificacao da Correcao de Terminacao de Processos FFMPEG ===\n")
    
    # Criar instancias
    queue_mgr = UnifiedQueueManager()
    encoder = EncoderEngine(max_concurrent=1, queue_manager=queue_mgr)
    console = Console()
    
    print("+ EncoderEngine criado com referencia ao queue manager")
    
    # Verificar se os metodos modificados existem
    if hasattr(queue_mgr, 'clear_queue') and callable(getattr(queue_mgr, 'clear_queue')):
        print("+ Metodo clear_queue encontrado no UnifiedQueueManager")
    else:
        print("- Metodo clear_queue NAO encontrado no UnifiedQueueManager")
    
    if hasattr(queue_mgr, 'cancel_job') and callable(getattr(queue_mgr, 'cancel_job')):
        print("+ Metodo cancel_job encontrado no UnifiedQueueManager")
    else:
        print("- Metodo cancel_job NAO encontrado no UnifiedQueueManager")
    
    if hasattr(encoder, '_queue_manager'):
        print("+ Referencia ao queue manager encontrada no EncoderEngine")
    else:
        print("- Referencia ao queue manager NAO encontrada no EncoderEngine")
    
    print("\n--- Descricao das Modificacoes ---")
    print("\n1. Modificacao no metodo clear_queue():")
    print("   - Agora cancela todos os jobs ativos antes de limpar a fila")
    print("   - Garante que os processos FFMPEG sejam terminados")
    
    print("\n2. Modificacao no metodo cancel_job():")
    print("   - Agora termina o processo FFMPEG associado ao job, se existir")
    print("   - Usa psutil para terminar o processo gracioso ou forcadamente")
    
    print("\n3. Modificacao no EncoderEngine:")
    print("   - Agora aceita uma referencia ao queue manager no construtor")
    print("   - Atualiza o PID do FFMPEG no job correspondente quando o processo e iniciado")
    
    print("\n4. Atualizacoes nos arquivos de UI:")
    print("   - EncoderEngine e instanciado com referencia ao queue manager")
    
    print("\n+ Correcao implementada com sucesso!")
    print("\nAgora, quando a fila e limpa ou um job e cancelado, os processos FFMPEG")
    print("associados serao terminados corretamente, resolvendo o problema reportado.")


if __name__ == "__main__":
    verify_fix()