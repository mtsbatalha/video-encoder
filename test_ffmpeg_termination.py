#!/usr/bin/env python3
"""
Script de teste para verificar se o cancelamento de jobs termina corretamente os processos FFMPEG.
"""

import os
import signal
import subprocess
import time
from pathlib import Path
from src.managers.unified_queue_manager import UnifiedQueueManager
from src.core.encoder_engine import EncoderEngine
from src.ui.queue_menu_v2 import QueueMenuUIV2
from rich.console import Console


def test_ffmpeg_termination():
    """Testa se o cancelamento de jobs termina corretamente os processos FFMPEG."""
    
    print("=== Teste de terminação de processos FFMPEG ===\n")
    
    # Criar instâncias
    queue_mgr = UnifiedQueueManager()
    console = Console()
    ui = QueueMenuUIV2(console, queue_mgr)
    
    # Criar um job de exemplo
    input_file = "test_input.mp4"
    output_file = "test_output.mp4"
    
    # Criar um arquivo de entrada de teste pequeno
    print("Criando arquivo de entrada de teste...")
    try:
        # Criar um vídeo curto de teste usando ffmpeg
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=size=1920x1080:rate=1", 
            "-vf", "hue=s=0", "-t", "10", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "ultrafast", "-tune", "zerolatency", input_file
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Erro ao criar arquivo de teste. Certifique-se de que o ffmpeg está instalado.")
        return
    
    # Criar perfil de codificação
    profile = {
        'name': 'Test Profile',
        'codec': 'libx264',
        'preset': 'ultrafast',
        'crf': 23,
        'bitrate': None
    }
    
    # Adicionar job à fila
    print(f"Adicionando job à fila: {input_file} -> {output_file}")
    job = queue_mgr.add_job(input_file, output_file, profile)
    print(f"Job criado com ID: {job.id}")
    
    # Criar encoder engine com referência ao queue manager
    encoder = EncoderEngine(max_concurrent=1, queue_manager=queue_mgr)
    encoder.start()
    
    # Iniciar o processamento da fila
    print("Iniciando processamento da fila...")
    
    # Obter o próximo job da fila
    next_job = queue_mgr.get_next_job()
    if next_job:
        from src.core.encoder_engine import EncodingJob, EncodingStatus
        
        # Converter para o formato esperado pelo encoder
        encoding_job = EncodingJob(
            id=next_job['job_id'],
            input_path=next_job['input_path'],
            output_path=next_job['output_path'],
            profile=next_job['profile']
        )
        
        # Adicionar job ao encoder
        encoder.add_job(encoding_job)
        
        # Aguardar um pouco para o encoding começar
        time.sleep(2)
        
        # Verificar se o job está em execução
        running_jobs = encoder.get_active_jobs()
        print(f"Jobs ativos: {len(running_jobs)}")
        
        if running_jobs:
            print("Job está em execução. Verificando PID do FFMPEG...")
            
            # Verificar se o PID do FFMPEG foi atualizado no job
            updated_job = queue_mgr.get_job(job.id)
            if hasattr(updated_job, 'ffmpeg_pid') and updated_job.ffmpeg_pid:
                print(f"PID do FFMPEG capturado: {updated_job.ffmpeg_pid}")
            else:
                print("PID do FFMPEG não foi capturado ainda")
        
        # Cancelar o job
        print(f"Cancelando job: {job.id}")
        success = queue_mgr.cancel_job(job.id)
        print(f"Cancelamento bem-sucedido: {success}")
        
        # Verificar se o processo FFMPEG foi terminado
        if hasattr(updated_job, 'ffmpeg_pid') and updated_job.ffmpeg_pid:
            try:
                import psutil
                process = psutil.Process(updated_job.ffmpeg_pid)
                if process.is_running():
                    print(f"AVISO: Processo FFMPEG {updated_job.ffmpeg_pid} ainda está rodando!")
                else:
                    print(f"Processo FFMPEG {updated_job.ffmpeg_pid} foi terminado corretamente.")
            except psutil.NoSuchProcess:
                print(f"Processo FFMPEG {updated_job.ffmpeg_pid} não encontrado (já terminado).")
            except Exception as e:
                print(f"Erro ao verificar processo FFMPEG: {e}")
    
    # Parar o encoder
    encoder.stop()
    
    # Limpar arquivos de teste
    try:
        os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)
    except:
        pass
    
    print("\n=== Teste concluído ===")


def test_queue_clearing():
    """Testa se limpar a fila termina corretamente os processos FFMPEG."""
    
    print("\n=== Teste de limpeza de fila com terminação de FFMPEG ===\n")
    
    # Criar instâncias
    queue_mgr = UnifiedQueueManager()
    console = Console()
    ui = QueueMenuUIV2(console, queue_mgr)
    
    # Criar um job de exemplo
    input_file = "test_input2.mp4"
    output_file = "test_output2.mp4"
    
    # Criar um arquivo de entrada de teste pequeno
    print("Criando arquivo de entrada de teste...")
    try:
        # Criar um vídeo curto de teste usando ffmpeg
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=1", 
            "-vf", "hue=s=0", "-t", "15", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "ultrafast", "-tune", "zerolatency", input_file
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Erro ao criar arquivo de teste. Certifique-se de que o ffmpeg está instalado.")
        return
    
    # Criar perfil de codificação
    profile = {
        'name': 'Test Profile 2',
        'codec': 'libx264',
        'preset': 'ultrafast',
        'crf': 25,
        'bitrate': None
    }
    
    # Adicionar job à fila
    print(f"Adicionando job à fila: {input_file} -> {output_file}")
    job = queue_mgr.add_job(input_file, output_file, profile)
    print(f"Job criado com ID: {job.id}")
    
    # Criar encoder engine com referência ao queue manager
    encoder = EncoderEngine(max_concurrent=1, queue_manager=queue_mgr)
    encoder.start()
    
    # Iniciar o processamento da fila
    print("Iniciando processamento da fila...")
    
    # Obter o próximo job da fila
    next_job = queue_mgr.get_next_job()
    if next_job:
        from src.core.encoder_engine import EncodingJob, EncodingStatus
        
        # Converter para o formato esperado pelo encoder
        encoding_job = EncodingJob(
            id=next_job['job_id'],
            input_path=next_job['input_path'],
            output_path=next_job['output_path'],
            profile=next_job['profile']
        )
        
        # Adicionar job ao encoder
        encoder.add_job(encoding_job)
        
        # Aguardar um pouco para o encoding começar
        time.sleep(3)
        
        # Verificar se o job está em execução
        running_jobs = encoder.get_active_jobs()
        print(f"Jobs ativos: {len(running_jobs)}")
        
        if running_jobs:
            print("Job está em execução. Verificando PID do FFMPEG...")
            
            # Verificar se o PID do FFMPEG foi atualizado no job
            updated_job = queue_mgr.get_job(job.id)
            if hasattr(updated_job, 'ffmpeg_pid') and updated_job.ffmpeg_pid:
                print(f"PID do FFMPEG capturado: {updated_job.ffmpeg_pid}")
            else:
                print("PID do FFMPEG não foi capturado ainda")
        
        # Limpar a fila (isso deve cancelar todos os jobs ativos)
        print("Limpando fila completa...")
        count = queue_mgr.clear_queue()
        print(f"{count} job(s) removidos da fila")
        
        # Verificar se o processo FFMPEG foi terminado
        if hasattr(updated_job, 'ffmpeg_pid') and updated_job.ffmpeg_pid:
            try:
                import psutil
                process = psutil.Process(updated_job.ffmpeg_pid)
                if process.is_running():
                    print(f"AVISO: Processo FFMPEG {updated_job.ffmpeg_pid} ainda está rodando!")
                else:
                    print(f"Processo FFMPEG {updated_job.ffmpeg_pid} foi terminado corretamente.")
            except psutil.NoSuchProcess:
                print(f"Processo FFMPEG {updated_job.ffmpeg_pid} não encontrado (já terminado).")
            except Exception as e:
                print(f"Erro ao verificar processo FFMPEG: {e}")
    
    # Parar o encoder
    encoder.stop()
    
    # Limpar arquivos de teste
    try:
        os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)
    except:
        pass
    
    print("\n=== Teste de limpeza concluído ===")


if __name__ == "__main__":
    test_ffmpeg_termination()
    test_queue_clearing()