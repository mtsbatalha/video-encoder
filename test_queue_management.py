#!/usr/bin/env python3
"""
Script de teste para as novas funcionalidades de gerenciamento de fila.
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório src ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).parent / "src"))

from managers.job_manager import JobManager


def test_hardware_based_limits():
    """Testa a detecção de hardware e limites de jobs."""
    print("=== Testando Limites Baseados em Hardware ===")
    
    # Criar JobManager com detecção automática de hardware
    job_manager = JobManager()
    
    max_jobs = job_manager.get_max_concurrent_jobs()
    current_running = job_manager.get_current_running_jobs_count()
    
    print(f"Máximo de jobs simultâneos: {max_jobs}")
    print(f"Jobs atualmente em execução: {current_running}")
    print(f"Pode iniciar novo job: {job_manager.can_start_new_job()}")
    
    # Testar registro de jobs ativos
    test_job_id = "test-job-123"
    if job_manager.register_active_job(test_job_id):
        print(f"Job {test_job_id} registrado como ativo")
        print(f"Jobs em execução após registro: {job_manager.get_current_running_jobs_count()}")
        
        # Tentar registrar outro job
        test_job_id_2 = "test-job-456"
        can_register_second = job_manager.register_active_job(test_job_id_2)
        print(f"Pode registrar segundo job: {can_register_second}")
        
        # Desregistrar primeiro job
        job_manager.unregister_active_job(test_job_id)
        print(f"Jobs em execução após desregistrar: {job_manager.get_current_running_jobs_count()}")
    
    print()


def test_job_creation_and_management():
    """Testa criação e gerenciamento de jobs."""
    print("=== Testando Criação e Gerenciamento de Jobs ===")
    
    job_manager = JobManager()
    
    # Criar alguns jobs de teste
    job_ids = []
    for i in range(3):
        job_id = job_manager.create_job(
            f"/input/test_{i}.mp4",
            f"/output/test_{i}_out.mp4",
            f"profile_{i}",
            f"Profile {i}"
        )
        job_ids.append(job_id)
        print(f"Criado job: {job_id[:8]}")
    
    # Listar jobs
    all_jobs = job_manager.list_jobs()
    print(f"Total de jobs criados: {len(all_jobs)}")
    
    # Atualizar progresso de um job
    if job_ids:
        job_manager.update_progress(job_ids[0], 50.0)
        print(f"Progresso do job {job_ids[0][:8]} atualizado para 50%")
    
    # Atualizar status de um job para running
    from managers.job_manager import JobStatus
    if job_ids:
        job_manager.update_job_status(job_ids[0], JobStatus.RUNNING)
        print(f"Status do job {job_ids[0][:8]} atualizado para RUNNING")
    
    print()


def test_eta_calculation():
    """Testa o cálculo de ETA e velocidade (simulado)."""
    print("=== Testando Cálculo de ETA e Velocidade (simulado) ===")
    
    # Importar os métodos necessários
    from datetime import datetime, timedelta
    
    # Simular o cálculo de ETA e velocidade
    def calculate_eta_and_speed_simulated(job_info):
        if not job_info.get('started_at'):
            return ("--", "--", "--")
        
        try:
            # Converter strings para datetime
            started_at = datetime.fromisoformat(job_info['started_at'].replace('Z', '+00:00'))
            current_time = datetime.now()
            elapsed_time = current_time - started_at
            
            progress = job_info.get('progress', 0)
            
            if progress <= 0:
                return ("--", "--", "--")
            
            # Calcular velocidade (tempo por percentagem)
            elapsed_seconds = elapsed_time.total_seconds()
            speed_percent_per_sec = progress / elapsed_seconds if elapsed_seconds > 0 else 0
            speed_percent_per_min = speed_percent_per_sec * 60 if speed_percent_per_sec > 0 else 0
            
            # Calcular ETA
            remaining_percent = 100 - progress
            eta_seconds = remaining_percent / speed_percent_per_sec if speed_percent_per_sec > 0 else 0
            eta_str = format_duration_simulated(eta_seconds) if eta_seconds > 0 else "--"
            
            # Formatar velocidade
            speed_str = f"{speed_percent_per_min:.1f}%/min" if speed_percent_per_min > 0 else "--"
            
            # Formatar tempo decorrido
            elapsed_str = format_duration_simulated(elapsed_seconds)
            
            return (elapsed_str, eta_str, speed_str)
        except Exception:
            return ("--", "--", "--")
    
    def format_duration_simulated(seconds):
        """Formata duração em segundos para HH:MM:SS."""
        if seconds <= 0:
            return "--"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def format_file_size_simulated(size_bytes):
        """Formata tamanho de arquivo em unidades legíveis."""
        if size_bytes <= 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    # Criar um job de exemplo em execução
    sample_job = {
        "id": "test-job-123",
        "input_path": "/path/to/input.mp4",
        "output_path": "/path/to/output.mp4",
        "profile_name": "Test Profile",
        "status": "running",
        "progress": 25.0,
        "started_at": datetime.now() - timedelta(minutes=10),  # 10 minutos atrás
        "input_size": 1073741824,  # 1GB
        "output_size": 104857600   # 100MB
    }
    
    # Converter datetime para string ISO para simulação
    sample_job["started_at"] = sample_job["started_at"].isoformat()
    
    elapsed, eta, speed = calculate_eta_and_speed_simulated(sample_job)
    print(f"Tempo decorrido: {elapsed}")
    print(f"ETA estimada: {eta}")
    print(f"Velocidade: {speed}")
    
    # Testar formatação de tamanho
    input_size_formatted = format_file_size_simulated(sample_job["input_size"])
    output_size_formatted = format_file_size_simulated(sample_job["output_size"])
    print(f"Tamanho: {input_size_formatted} → {output_size_formatted}")
    
    print()


def main():
    """Função principal de teste."""
    print("Iniciando testes de gerenciamento de fila...\n")
    
    try:
        test_hardware_based_limits()
        test_job_creation_and_management()
        test_eta_calculation()
        
        print("=== Todos os testes básicos concluídos ===")
        print("Os testes verificaram:")
        print("- Detecção de hardware e limites de jobs")
        print("- Cálculo de ETA e velocidade (simulado)")
        print("- Formatação de tamanhos")
        print("- Criação e gerenciamento de jobs")
        
    except Exception as e:
        print(f"Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()