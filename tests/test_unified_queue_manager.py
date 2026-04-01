#!/usr/bin/env python3
"""
Testes para o UnifiedQueueManager.
"""

import sys
from pathlib import Path

# Adicionar src ao path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from managers.unified_queue_manager import (
    UnifiedQueueManager,
    JobStatus,
    QueuePriority,
    QueueJob,
    ResourceUsage
)
import shutil


def test_create_manager():
    """Testa criação do gerenciador."""
    print("=" * 60)
    print("TESTE: Criar UnifiedQueueManager")
    print("=" * 60)
    
    # Criar diretório de teste
    test_dir = Path(__file__).parent / "test_jobs"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    mgr = UnifiedQueueManager(jobs_dir=str(test_dir))
    
    print(f"[OK] Gerenciador criado com sucesso")
    print(f"  Diretorio: {mgr.jobs_dir}")
    print(f"  Max concurrent jobs: {mgr.get_max_concurrent_jobs()}")
    print(f"  Fila pausada: {mgr.is_queue_paused()}")
    print()
    
    return mgr, test_dir


def test_add_job(mgr: UnifiedQueueManager):
    """Testa adição de jobs."""
    print("=" * 60)
    print("TESTE: Adicionar Jobs")
    print("=" * 60)
    
    profile = {
        "id": "h264_1080p",
        "name": "H.264 1080p",
        "codec": "h264_nvenc",
        "resolution": "1920x1080",
        "bitrate": "8000K",
        "preset": "p5",
        "crf": 23
    }
    
    # Adicionar job 1
    job1 = mgr.add_job(
        input_path="/videos/input1.mp4",
        output_path="/videos/output1.mp4",
        profile=profile,
        priority=QueuePriority.NORMAL
    )
    print(f"[OK] Job 1 adicionado: {job1.id[:8]}")
    print(f"  Status: {job1.status}")
    print(f"  Prioridade: {job1.priority}")
    
    # Adicionar job 2 (alta prioridade)
    job2 = mgr.add_job(
        input_path="/videos/input2.mp4",
        output_path="/videos/output2.mp4",
        profile=profile,
        priority=QueuePriority.HIGH
    )
    print(f"[OK] Job 2 adicionado: {job2.id[:8]}")
    print(f"  Status: {job2.status}")
    print(f"  Prioridade: {job2.priority}")
    
    # Adicionar job 3 (prioridade crítica)
    job3 = mgr.add_job(
        input_path="/videos/input3.mp4",
        output_path="/videos/output3.mp4",
        profile=profile,
        priority=QueuePriority.CRITICAL
    )
    print(f"[OK] Job 3 adicionado: {job3.id[:8]}")
    print(f"  Status: {job3.status}")
    print(f"  Prioridade: {job3.priority}")
    
    print()
    return job1, job2, job3


def test_list_queue(mgr: UnifiedQueueManager):
    """Testa listagem da fila."""
    print("=" * 60)
    print("TESTE: Listar Fila (ordenado por prioridade)")
    print("=" * 60)
    
    jobs = mgr.list_queue()
    
    for i, job in enumerate(jobs, 1):
        print(f"  {i}. {job.id[:8]} - {job.profile_name} - Prioridade: {job.priority}")
    
    print()


def test_get_job_details(mgr: UnifiedQueueManager, job_id: str):
    """Testa obtenção de detalhes do job."""
    print("=" * 60)
    print(f"TESTE: Detalhes do Job {job_id[:8]}")
    print("=" * 60)
    
    details = mgr.get_job_details(job_id)
    
    if details:
        print(f"  ID: {details['id'][:8]}")
        print(f"  Input: {details['input_path']}")
        print(f"  Output: {details['output_path']}")
        print(f"  Perfil: {details['profile_name']}")
        print(f"  Status: {details['status_display']}")
        print(f"  Prioridade: {details['priority']}")
        print(f"  Criado em: {details['created_at']}")
    else:
        print("  Job nao encontrado!")
    
    print()


def test_pause_resume_job(mgr: UnifiedQueueManager, job_id: str):
    """Testa pausar e retomar job."""
    print("=" * 60)
    print(f"TESTE: Pausar/Retomar Job {job_id[:8]}")
    print("=" * 60)
    
    # Primeiro marcar como running
    mgr.update_job_status(job_id, JobStatus.RUNNING)
    job = mgr.get_job(job_id)
    print(f"  Status apos RUNNING: {job.status}")
    
    # Pausar
    result = mgr.pause_job(job_id)
    job = mgr.get_job(job_id)
    print(f"  Pausar: {result}, Status: {job.status}")
    
    # Retomar
    result = mgr.resume_job(job_id)
    job = mgr.get_job(job_id)
    print(f"  Retomar: {result}, Status: {job.status}")
    
    print()


def test_cancel_job(mgr: UnifiedQueueManager, job_id: str):
    """Testa cancelar job."""
    print("=" * 60)
    print(f"TESTE: Cancelar Job {job_id[:8]}")
    print("=" * 60)
    
    result = mgr.cancel_job(job_id)
    job = mgr.get_job(job_id)
    print(f"  Cancelar: {result}, Status: {job.status}")
    
    print()


def test_update_progress(mgr: UnifiedQueueManager, job_id: str):
    """Testa atualização de progresso."""
    print("=" * 60)
    print(f"TESTE: Atualizar Progresso Job {job_id[:8]}")
    print("=" * 60)
    
    # Marcar como running
    mgr.update_job_status(job_id, JobStatus.RUNNING)
    
    # Atualizar progresso
    for progress in [25, 50, 75]:
        mgr.update_progress(job_id, float(progress))
        job = mgr.get_job(job_id)
        print(f"  Progresso: {job.progress}%, Tempo: {job.elapsed_time}, ETA: {job.eta}")
    
    print()


def test_get_statistics(mgr: UnifiedQueueManager):
    """Testa obtenção de estatísticas."""
    print("=" * 60)
    print("TESTE: Estatisticas da Fila")
    print("=" * 60)
    
    stats = mgr.get_statistics()
    
    print(f"  Total de jobs: {stats['total']}")
    print(f"  Jobs ativos: {stats['active']}")
    print(f"  Fila pausada: {stats['paused']}")
    print(f"  Por status:")
    for status, count in stats['by_status'].items():
        print(f"    {status}: {count}")
    print(f"  Por prioridade:")
    for priority, count in stats['by_priority'].items():
        print(f"    {priority}: {count}")
    
    print()


def test_clear_queue(mgr: UnifiedQueueManager):
    """Testa limpar fila."""
    print("=" * 60)
    print("TESTE: Limpar Fila")
    print("=" * 60)
    
    count = mgr.clear_queue(status_filter=JobStatus.CANCELLED)
    print(f"  Jobs CANCELLED removidos: {count}")
    
    count = mgr.get_queue_length()
    print(f"  Jobs restantes na fila: {count}")
    
    print()


def test_save_load(mgr: UnifiedQueueManager):
    """Testa salvar e carregar."""
    print("=" * 60)
    print("TESTE: Salvar e Carregar")
    print("=" * 60)
    
    # Salvar
    result = mgr.save()
    print(f"  Salvar: {result}")
    
    # Criar novo manager e carregar
    new_mgr = UnifiedQueueManager(jobs_dir=str(mgr.jobs_dir))
    print(f"  Jobs apos carregar: {len(new_mgr.list_queue())}")
    
    print()


def cleanup(test_dir: Path):
    """Limpa diretório de teste."""
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print(f"Diretorio de teste removido: {test_dir}")


def main():
    """Função principal de testes."""
    print("\n" + "=" * 60)
    print("TESTES DO UNIFIED QUEUE MANAGER")
    print("=" * 60 + "\n")
    
    try:
        # Criar manager
        mgr, test_dir = test_create_manager()
        
        # Adicionar jobs
        job1, job2, job3 = test_add_job(mgr)
        
        # Listar fila
        test_list_queue(mgr)
        
        # Obter detalhes
        test_get_job_details(mgr, job1.id)
        
        # Testar pause/resume
        test_pause_resume_job(mgr, job2.id)
        
        # Testar update de progresso
        test_update_progress(mgr, job3.id)
        
        # Testar cancelamento
        test_cancel_job(mgr, job1.id)
        
        # Estatísticas
        test_get_statistics(mgr)
        
        # Limpar fila
        test_clear_queue(mgr)
        
        # Salvar/Carregar
        test_save_load(mgr)
        
        print("=" * 60)
        print("TODOS OS TESTES CONCLUIDOS COM SUCESSO!")
        print("=" * 60)
        
        # Cleanup
        cleanup(test_dir)
        
    except Exception as e:
        print(f"\n[ERRO] DURANTE TESTES: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup em caso de erro
        if 'test_dir' in locals():
            cleanup(test_dir)


if __name__ == "__main__":
    main()
