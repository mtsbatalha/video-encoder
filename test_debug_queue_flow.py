#!/usr/bin/env python3
"""
Script de debug para diagnosticar o problema da fila não iniciar conversão.
"""

import sys
import os
from pathlib import Path
import time
import subprocess

# Adicionar o diretório raiz ao path para importar os módulos corretamente
sys.path.insert(0, str(Path(__file__).parent))

from src.managers.queue_manager import QueueManager
from src.managers.job_manager import JobManager
from src.core.encoder_engine import EncoderEngine, EncodingJob, EncodingStatus
from src.managers.config_manager import ConfigManager
from src.core.ffmpeg_wrapper import FFmpegWrapper


def create_test_video():
    """Cria um vídeo de teste usando FFmpeg."""
    print("Criando vídeo de teste...")
    test_input = Path(__file__).parent / "test_input.mkv"
    
    # Criar vídeo de teste de 5 segundos
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', 'color=c=blue:s=640x480:d=5',
        '-f', 'lavfi',
        '-i', 'anullsrc=r=44100:cl=stereo',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-t', '5',
        '-shortest',
        str(test_input)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"Vídeo de teste criado: {test_input}")
            return str(test_input)
        else:
            print(f"Erro ao criar vídeo: {result.stderr}")
    except Exception as e:
        print(f"Erro ao criar vídeo: {e}")
    
    return None


def test_queue_flow():
    """Testa o fluxo completo de processamento da fila."""
    print("=== Debug: Fluxo da Fila ===\n")
    
    # Carregar config
    config = ConfigManager()
    
    # Criar managers
    queue_mgr = QueueManager()
    job_mgr = JobManager()
    
    # Criar vídeo de teste se não existir
    test_input_path = create_test_video()
    if not test_input_path:
        print("[ERRO] Não foi possível criar vídeo de teste")
        return
    
    test_output_path = str(Path(__file__).parent / "test_output.mkv")
    
    # Verificar estado inicial da fila
    queue_length = queue_mgr.get_queue_length()
    print(f"Tamanho da fila: {queue_length}")
    
    if queue_length == 0:
        print("\n[ALERTA] Fila vazia! Adicionando job de teste...")
        
        # Criar um job de teste
        test_profile = {
            "name": "Test Profile",
            "codec": "hevc_nvenc",
            "cq": 20,
            "preset": "p5"
        }
        
        # Adicionar job à fila (simulado)
        job_id = "test-job-debug-001"
        queue_mgr.add_to_queue(
            job_id=job_id,
            input_path=test_input_path,
            output_path=test_output_path,
            profile=test_profile
        )
        
        queue_length = queue_mgr.get_queue_length()
        print(f"Novo tamanho da fila: {queue_length}")
    
    # Listar jobs na fila
    print("\n--- Jobs na fila ---")
    queue_items = queue_mgr.list_queue()
    for item in queue_items:
        print(f"  Job ID: {item['job_id'][:8]}")
        print(f"    Input: {item['input_path']}")
        print(f"    Output: {item['output_path']}")
        print(f"    Started: {item.get('started_at', 'N/A')}")
    
    # Testar pop_next_job
    print("\n--- Testando pop_next_job() ---")
    next_job = queue_mgr.pop_next_job()
    if next_job:
        print(f"Job retornado: {next_job['job_id'][:8]}")
        print(f"  Input: {next_job['input_path']}")
        print(f"  Profile: {next_job['profile'].get('name', 'Unknown')}")
        
        # Criar EncodingJob
        encoding_job = EncodingJob(
            id=next_job['job_id'],
            input_path=next_job['input_path'],
            output_path=next_job['output_path'],
            profile=next_job['profile']
        )
        print(f"\nEncodingJob criado:")
        print(f"  Status: {encoding_job.status}")
        print(f"  Progress: {encoding_job.progress}")
        
        # Testar encoder
        print("\n--- Testando EncoderEngine ---")
        max_concurrent = config.get('encoding.max_concurrent', 2)
        print(f"Max concurrent jobs: {max_concurrent}")
        
        encoder = EncoderEngine(max_concurrent=max_concurrent, queue_manager=queue_mgr)
        
        # Adicionar callbacks
        def on_progress(job_id: str, progress: float):
            print(f"  [PROGRESS] {job_id[:8]}: {progress}%")
        
        def on_status(job_id: str, status: EncodingStatus):
            print(f"  [STATUS] {job_id[:8]}: {status.value}")
            
        def on_encoding_stats(job_id: str, stats: dict):
            print(f"  [STATS] {job_id[:8]}: {stats}")
        
        encoder.add_progress_callback(on_progress)
        encoder.add_status_callback(on_status)
        encoder.add_encoding_stats_callback(on_encoding_stats)
        
        # Adicionar job ao encoder
        encoder.add_job(encoding_job)
        print(f"\nJob adicionado ao encoder")
        
        # Verificar jobs pendentes
        pending = encoder.get_pending_jobs()
        print(f"Jobs pendentes no encoder: {len(pending)}")
        
        # Iniciar encoder
        print("\nIniciando encoder...")
        encoder.start()
        
        # Aguardar encoding completar (vídeo de 5 segundos)
        print("Aguardando encoding (pode levar alguns segundos)...")
        elapsed = 0
        max_wait = 60  # máximo 60 segundos
        while elapsed < max_wait:
            time.sleep(1)
            elapsed += 1
            
            # Verificar jobs ativos
            active = encoder.get_active_jobs()
            pending = encoder.get_pending_jobs()
            completed = encoder._completed_jobs
            
            if completed:
                break
                
            if elapsed % 5 == 0:
                print(f"  ... aguardando ({elapsed}s) - ativos: {len(active)}, pendentes: {len(pending)}")
        
        # Verificar jobs ativos
        active = encoder.get_active_jobs()
        print(f"Jobs ativos no encoder: {len(active)}")
        
        pending = encoder.get_pending_jobs()
        print(f"Jobs pendentes no encoder: {len(pending)}")
        
        # Verificar jobs completados (com erro)
        completed = encoder._completed_jobs
        print(f"Jobs completados: {len(completed)}")
        for job_id, job in completed.items():
            print(f"  Job {job_id[:8]}: status={job.status}, error={job.error_message}")
        
        # Parar encoder
        encoder.stop()
        print("\nEncoder parado.")
        
        # Verificar se arquivo de saída foi criado
        if Path(test_output_path).exists():
            print(f"Arquivo de saída criado: {test_output_path}")
            print(f"Tamanho: {Path(test_output_path).stat().st_size} bytes")
        else:
            print(f"Arquivo de saída NÃO foi criado: {test_output_path}")
        
    else:
        print("Nenhum job disponível na fila!")
    
    print("\n=== Fim do Debug ===")


if __name__ == "__main__":
    test_queue_flow()
