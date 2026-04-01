"""
Script para diagnosticar o que a UI da fila está vendo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from managers.unified_queue_manager import UnifiedQueueManager
from managers.job_manager import JobManager
from rich.console import Console

def main():
    console = Console()
    
    console.print("\n[bold cyan]=== DIAGNÓSTICO DA UI DA FILA ===[/bold cyan]\n")
    
    # 1. UnifiedQueueManager
    console.print("[yellow]1. UnifiedQueueManager:[/yellow]")
    unified_mgr = UnifiedQueueManager()
    unified_mgr.load()
    
    running_unified = unified_mgr.get_running_jobs()
    pending_unified = unified_mgr.get_pending_jobs()
    all_unified = unified_mgr.list_jobs()
    
    console.print(f"   get_running_jobs(): {len(running_unified)} jobs")
    console.print(f"   get_pending_jobs(): {len(pending_unified)} jobs")
    console.print(f"   list_jobs(): {len(all_unified)} jobs")
    
    # 2. JobManager antigo
    console.print("\n[yellow]2. JobManager (antigo):[/yellow]")
    job_mgr = JobManager()
    
    try:
        running_old = job_mgr.get_running_jobs()
        console.print(f"   get_running_jobs(): {len(running_old) if running_old else 0} jobs")
    except Exception as e:
        console.print(f"   get_running_jobs(): [red]ERRO: {e}[/red]")
    
    try:
        pending_old = job_mgr.get_pending_jobs()
        console.print(f"   get_pending_jobs(): {len(pending_old) if pending_old else 0} jobs")
    except Exception as e:
        console.print(f"   get_pending_jobs(): [red]ERRO: {e}[/red]")
    
    try:
        all_old = job_mgr.list_jobs()
        console.print(f"   list_jobs(): {len(all_old) if all_old else 0} jobs")
    except Exception as e:
        console.print(f"   list_jobs(): [red]ERRO: {e}[/red]")
    
    # 3. Arquivos de persistência
    console.print("\n[yellow]3. Arquivos de persistência:[/yellow]")
    
    queue_file = Path("jobs/queue.json")
    jobs_file = Path("jobs/jobs.json")
    
    console.print(f"   jobs/queue.json: {'EXISTE' if queue_file.exists() else 'NÃO EXISTE'}")
    if queue_file.exists():
        console.print(f"     Tamanho: {queue_file.stat().st_size} bytes")
    
    console.print(f"   jobs/jobs.json: {'EXISTE' if jobs_file.exists() else 'NÃO EXISTE'}")
    if jobs_file.exists():
        console.print(f"     Tamanho: {jobs_file.stat().st_size} bytes")
    
    # 4. Testar exatamente o que a UI usa
    console.print("\n[yellow]4. Simulação da UI (queue_menu.py linha 185-186):[/yellow]")
    console.print("   Código da UI:")
    console.print("     running = self.job_mgr.get_running_jobs()")
    console.print("     pending = self.job_mgr.get_pending_jobs()")
    console.print()
    console.print("   Se job_mgr for JobManager (antigo):")
    console.print(f"     running = {len(running_old) if running_old else 0} jobs")
    console.print(f"     pending = {len(pending_old) if pending_old else 0} jobs")
    console.print()
    console.print("   Se job_mgr for UnifiedQueueManager (novo):")
    console.print(f"     running = {len(running_unified)} jobs")
    console.print(f"     pending = {len(pending_unified)} jobs")
    
    console.print("\n[bold green]Diagnóstico concluído![/bold green]\n")

if __name__ == "__main__":
    main()
