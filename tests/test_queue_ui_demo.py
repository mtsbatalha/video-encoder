#!/usr/bin/env python3
"""
Demo da nova UI de fila com job detalhado.
"""

import sys
from pathlib import Path

# Adicionar src ao path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from rich.console import Console
from managers.unified_queue_manager import (
    UnifiedQueueManager,
    JobStatus,
    QueuePriority,
    ResourceUsage
)
import shutil


def main():
    """Demonstra a nova UI de fila."""
    console = Console()
    
    print("\n" + "=" * 60)
    print("DEMO: NOVA UI DE FILA COM JOB DETALHADO")
    print("=" * 60 + "\n")
    
    # Criar diretório de teste
    test_dir = Path(__file__).parent / "test_jobs_demo"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    # Criar manager
    queue_mgr = UnifiedQueueManager(jobs_dir=str(test_dir))
    
    # Adicionar jobs de demonstração
    print("Adicionando jobs de demonstracao...\n")
    
    profile_h264 = {
        "id": "h264_1080p",
        "name": "H.264 1080p",
        "codec": "h264_nvenc",
        "resolution": "1920x1080",
        "bitrate": "8000K",
        "preset": "p5",
        "crf": 23
    }
    
    # Adicionar job
    job1 = queue_mgr.add_job(
        input_path="C:/Videos/Raw/ferias_praia_4k.mp4",
        output_path="C:/Videos/Encoded/ferias_praia_1080p.mp4",
        profile=profile_h264,
        priority=QueuePriority.CRITICAL
    )
    print(f"[OK] Job adicionado: {job1.id[:8]} (CRITICAL)")
    
    # Simular execução
    print("\nSimulando execucao do job...\n")
    
    queue_mgr.register_active_job(job1.id)
    queue_mgr.update_progress(job1.id, 45.5)
    queue_mgr._jobs[job1.id].input_size = 2147483648  # 2GB
    queue_mgr._jobs[job1.id].output_size = 524288000  # 500MB
    queue_mgr._jobs[job1.id].resource_usage = ResourceUsage(
        gpu_usage=85.5,
        vram_usage=4.2,
        cpu_usage=25.0,
        memory_usage=1.5,
        encoder_utilization=92.0
    )
    print(f"[OK] Job: Executando a 45.5%")
    
    # Exibir detalhes do job
    print("\n" + "=" * 60)
    print("  DETALHES DO JOB (EM EXECUCAO)")
    print("=" * 60)
    
    job = queue_mgr.get_job(job1.id)
    
    print(f"\nID do Job: {job.id}")
    print(f"Status: {job.status}")
    print(f"Prioridade: {job.priority} (CRITICAL)")
    print(f"\nInput: {job.input_path}")
    print(f"Output: {job.output_path}")
    print(f"Perfil: {job.profile_name}")
    print(f"\nProgresso: {job.progress}%")
    print(f"Tempo Decorrido: {job.elapsed_time}")
    print(f"ETA Estimado: {job.eta}")
    print(f"Velocidade: {job.speed}%/min")
    print(f"\nTamanho Original: {job.input_size / (1024**3):.2f} GB")
    print(f"Tamanho Codificado: {job.output_size / (1024**3):.2f} GB")
    print(f"Compressao: {job.compression_ratio * 100:.1f}%")
    
    if job.resource_usage and job.resource_usage.gpu_usage > 0:
        print(f"\nUSO DE RECURSOS:")
        print(f"  GPU: {job.resource_usage.gpu_usage:.1f}%")
        print(f"  VRAM: {job.resource_usage.vram_usage:.1f} GB")
        print(f"  CPU: {job.resource_usage.cpu_usage:.1f}%")
        print(f"  RAM: {job.resource_usage.memory_usage:.1f} GB")
        print(f"  Encoder: {job.resource_usage.encoder_utilization:.1f}%")
    
    # Exibir estatísticas
    print("\n" + "=" * 60)
    print("  ESTATISTICAS DA FILA")
    print("=" * 60)
    
    stats = queue_mgr.get_statistics()
    print(f"\nTotal de Jobs: {stats['total']}")
    print(f"Jobs Ativos: {stats['active']}/{stats['max_concurrent']}")
    print(f"Status da Fila: {'PAUSADA' if stats['paused'] else 'ATIVA'}")
    print(f"\nPor Status:")
    for status, count in stats['by_status'].items():
        print(f"  {status}: {count}")
    print(f"\nPor Prioridade:")
    for priority, count in stats['by_priority'].items():
        print(f"  {priority}: {count}")
    print(f"\nTaxa de Sucesso: {stats['success_rate']:.1f}%")
    
    # Cleanup
    shutil.rmtree(test_dir)
    
    print("\n" + "=" * 60)
    print("DEMO CONCLUIDA!")
    print("=" * 60)
    print("\nO UnifiedQueueManager inclui:")
    print("  - Gerenciamento unificado de jobs e fila")
    print("  - Controle de execucao (pausar, retomar, cancelar)")
    print("  - Prioridades de job (LOW, NORMAL, HIGH, CRITICAL)")
    print("  - Calculo automatico de ETA e velocidade")
    print("  - Monitoramento de uso de recursos (GPU, CPU, VRAM, RAM)")
    print("  - Persistencia em JSON")
    print("  - Callbacks para atualizacoes em tempo real")
    print("  - Detecao automatica de limite de jobs por hardware")
    print("\nA UI v2 inclui:")
    print("  - Tabela detalhada com todas as informacoes")
    print("  - Painel de detalhes do job")
    print("  - Painel de estatisticas")
    print("  - Barra de progresso visual")
    print("  - Status e prioridade coloridos")
    print()


if __name__ == "__main__":
    main()
