"""
Script para limpar completamente o sistema de fila e começar do zero.
"""

import json
from pathlib import Path

def main():
    print("\n=== LIMPEZA DO SISTEMA DE FILA ===\n")
    
    # 1. Limpar jobs/queue.json (UnifiedQueueManager)
    queue_file = Path("jobs/queue.json")
    if queue_file.exists():
        print(f"Limpando {queue_file}...")
        queue_file.write_text("{}", encoding="utf-8")
        print("✓ Arquivo limpo")
    else:
        print(f"  {queue_file} não existe")
    
    # 2. Limpar jobs/jobs.json (JobManager antigo)
    jobs_file = Path("jobs/jobs.json")
    if jobs_file.exists():
        print(f"\nLimpando {jobs_file}...")
        jobs_file.write_text("{}", encoding="utf-8")
        print("✓ Arquivo limpo")
    else:
        print(f"  {jobs_file} não existe")
    
    # 3. Verificar outros arquivos de job
    jobs_dir = Path("jobs")
    if jobs_dir.exists():
        job_files = list(jobs_dir.glob("*.json"))
        if len(job_files) > 2:
            print(f"\nOutros arquivos encontrados em {jobs_dir}:")
            for f in job_files:
                if f.name not in ["queue.json", "jobs.json"]:
                    print(f"  - {f.name} ({f.stat().st_size} bytes)")
    
    print("\n✓ Limpeza concluída!")
    print("\nO sistema está pronto para receber jobs reais.")
    print("Execute: python src/cli.py --interactive")
    print()

if __name__ == "__main__":
    main()
