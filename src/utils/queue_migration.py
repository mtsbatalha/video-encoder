"""
Queue Migration Utility - Migra dados do antigo sistema (QueueManager + JobManager)
para o novo UnifiedQueueManager.
"""

import json
from pathlib import Path
from datetime import datetime


def migrate_queue_data(
    old_queue_file: str,
    old_jobs_file: str,
    new_queue_file: str
) -> dict:
    """
    Migra dados dos antigos QueueManager e JobManager para UnifiedQueueManager.
    
    Args:
        old_queue_file: Caminho para o arquivo queue.json antigo
        old_jobs_file: Caminho para o arquivo jobs.json antigo
        new_queue_file: Caminho para o novo arquivo queue.json unificado
    
    Returns:
        dict: Estatísticas da migração
    """
    old_queue_path = Path(old_queue_file)
    old_jobs_path = Path(old_jobs_file)
    new_queue_path = Path(new_queue_file)
    
    stats = {
        "queue_items_migrated": 0,
        "jobs_migrated": 0,
        "jobs_skipped": 0,
        "errors": []
    }
    
    # Carregar dados antigos
    old_queue_data = {}
    old_jobs_data = {}
    
    if old_queue_path.exists():
        try:
            with open(old_queue_path, 'r', encoding='utf-8') as f:
                old_queue_data = json.load(f)
            print(f"[OK] Carregado queue.json antigo: {len(old_queue_data.get('queue', []))} itens")
        except Exception as e:
            stats["errors"].append(f"Erro ao carregar queue.json: {e}")
    
    if old_jobs_path.exists():
        try:
            with open(old_jobs_path, 'r', encoding='utf-8') as f:
                old_jobs_data = json.load(f)
            print(f"[OK] Carregado jobs.json antigo: {len(old_jobs_data)} jobs")
        except Exception as e:
            stats["errors"].append(f"Erro ao carregar jobs.json: {e}")
    
    # Criar novo dados unificados
    new_data = {
        "version": "2.0",
        "schema_version": 1,
        "last_updated": datetime.now().isoformat(),
        "queue_paused": old_queue_data.get("paused", False),
        "max_concurrent_jobs": 2,  # Default
        "jobs": {},
        "queue_order": [],
        "active_jobs": [],
        "history": {
            "completed": [],
            "failed": [],
            "cancelled": []
        }
    }
    
    # Migrar jobs do JobManager
    for job_id, job in old_jobs_data.items():
        try:
            # Mapear status antigo para novo
            status_mapping = {
                "pending": "queued",
                "running": "running",
                "completed": "completed",
                "failed": "failed",
                "cancelled": "cancelled",
                "paused": "paused"
            }
            
            new_status = status_mapping.get(job.get("status", "pending"), "queued")
            
            # Criar novo job unificado
            new_job = {
                "id": job_id,
                "input_path": job.get("input_path", ""),
                "output_path": job.get("output_path", ""),
                "profile": {
                    "id": job.get("profile_id", ""),
                    "name": job.get("profile_name", "")
                },
                "profile_name": job.get("profile_name", ""),
                "status": new_status,
                "progress": job.get("progress", 0.0),
                "priority": 2,  # NORMAL
                "created_at": job.get("created_at", datetime.now().isoformat()),
                "started_at": job.get("started_at"),
                "paused_at": None,
                "resumed_at": None,
                "completed_at": job.get("completed_at"),
                "elapsed_time": "00:00:00",
                "eta": "--:--:--",
                "speed": 0.0,
                "input_size": job.get("input_size", 0),
                "output_size": job.get("output_size", 0),
                "compression_ratio": 0.0,
                "error_message": job.get("error_message"),
                "retry_count": job.get("retry_count", 0),
                "resource_usage": {
                    "gpu_usage": 0.0,
                    "vram_usage": 0.0,
                    "cpu_usage": 0.0,
                    "memory_usage": 0.0,
                    "encoder_utilization": 0.0
                },
                "ffmpeg_pid": None,
                "log_file": None
            }
            
            new_data["jobs"][job_id] = new_job
            stats["jobs_migrated"] += 1
            
            # Adicionar à fila se estiver pendente/running
            if new_status in ["queued", "running", "paused"]:
                new_data["queue_order"].append(job_id)
                stats["queue_items_migrated"] += 1
            
            # Adicionar a ativos se estiver running
            if new_status == "running":
                new_data["active_jobs"].append(job_id)
            
            # Adicionar ao histórico
            if new_status == "completed":
                new_data["history"]["completed"].append(job_id)
            elif new_status == "failed":
                new_data["history"]["failed"].append(job_id)
            elif new_status == "cancelled":
                new_data["history"]["cancelled"].append(job_id)
                
        except Exception as e:
            stats["errors"].append(f"Erro ao migrar job {job_id}: {e}")
            stats["jobs_skipped"] += 1
    
    # Migrar itens da fila do QueueManager que não estão nos jobs
    for queue_item in old_queue_data.get("queue", []):
        job_id = queue_item.get("job_id")
        if job_id and job_id not in new_data["jobs"]:
            try:
                new_job = {
                    "id": job_id,
                    "input_path": queue_item.get("input_path", ""),
                    "output_path": queue_item.get("output_path", ""),
                    "profile": queue_item.get("profile", {}),
                    "profile_name": queue_item.get("profile", {}).get("name", ""),
                    "status": "queued",
                    "progress": 0.0,
                    "priority": queue_item.get("priority", 2),
                    "created_at": queue_item.get("added_at", datetime.now().isoformat()),
                    "started_at": queue_item.get("started_at"),
                    "paused_at": None,
                    "resumed_at": None,
                    "completed_at": None,
                    "elapsed_time": "00:00:00",
                    "eta": "--:--:--",
                    "speed": 0.0,
                    "input_size": 0,
                    "output_size": 0,
                    "compression_ratio": 0.0,
                    "error_message": None,
                    "retry_count": 0,
                    "resource_usage": {
                        "gpu_usage": 0.0,
                        "vram_usage": 0.0,
                        "cpu_usage": 0.0,
                        "memory_usage": 0.0,
                        "encoder_utilization": 0.0
                    },
                    "ffmpeg_pid": None,
                    "log_file": None
                }
                
                new_data["jobs"][job_id] = new_job
                new_data["queue_order"].append(job_id)
                stats["queue_items_migrated"] += 1
                stats["jobs_migrated"] += 1
                
            except Exception as e:
                stats["errors"].append(f"Erro ao migrar queue item {job_id}: {e}")
    
    # Salvar novo arquivo unificado
    try:
        # Criar diretório se não existir
        new_queue_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Fazer backup do arquivo antigo se existir
        if new_queue_path.exists():
            backup_path = new_queue_path.with_suffix('.json.bak')
            new_queue_path.rename(backup_path)
            print(f"[OK] Backup criado: {backup_path}")
        
        with open(new_queue_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Novo queue.json unificado criado: {new_queue_path}")
        
    except Exception as e:
        stats["errors"].append(f"Erro ao salvar novo queue.json: {e}")
        return stats
    
    # Imprimir estatísticas
    print("\n" + "=" * 60)
    print("MIGRAÇÃO CONCLUÍDA")
    print("=" * 60)
    print(f"Jobs migrados: {stats['jobs_migrated']}")
    print(f"Itens da fila migrados: {stats['queue_items_migrated']}")
    print(f"Jobs ignorados: {stats['jobs_skipped']}")
    
    if stats["errors"]:
        print(f"\nErros ({len(stats['errors'])}):")
        for error in stats["errors"]:
            print(f"  - {error}")
    
    return stats


def main():
    """Função principal de migração."""
    print("=" * 60)
    print("MIGRAÇÃO DE FILA - QueueManager + JobManager -> UnifiedQueueManager")
    print("=" * 60 + "\n")
    
    # Caminhos padrão
    jobs_dir = Path(__file__).parent.parent.parent / "jobs"
    
    old_queue_file = jobs_dir / "queue.json"
    old_jobs_file = jobs_dir / "jobs.json"
    new_queue_file = jobs_dir / "queue.json"
    
    print(f"Diretório de jobs: {jobs_dir}")
    print(f"Queue antigo: {old_queue_file}")
    print(f"Jobs antigo: {old_jobs_file}")
    print(f"Queue novo (unificado): {new_queue_file}")
    print()
    
    # Verificar se existem arquivos antigos
    if not old_queue_file.exists() and not old_jobs_file.exists():
        print("[AVISO] Nenhum arquivo antigo encontrado. Migração não necessária.")
        return
    
    # Executar migração automaticamente
    print("[INFO] Executando migração automaticamente...")
    
    # Executar migração
    stats = migrate_queue_data(
        str(old_queue_file),
        str(old_jobs_file),
        str(new_queue_file)
    )
    
    print("\n[OK] Migração concluída!")
    print("\nAgora você pode usar o novo UnifiedQueueManager.")
    print("Os arquivos antigos foram preservados com extensão .bak")


if __name__ == "__main__":
    main()
