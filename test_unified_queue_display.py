"""
Script de teste para verificar exibição de jobs com UnifiedQueueManager.

Este script testa se os métodos de compatibilidade estão funcionando corretamente
e se os jobs são exibidos na UI.
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from managers.unified_queue_manager import UnifiedQueueManager, JobStatus, QueuePriority
from rich.console import Console
from rich.table import Table

def main():
    console = Console()
    
    # Inicializar UnifiedQueueManager
    console.print("\n[bold cyan]Teste de Exibição de Jobs - UnifiedQueueManager[/bold cyan]\n")
    
    queue_mgr = UnifiedQueueManager()
    
    # Carregar jobs existentes
    queue_mgr.load()
    
    # Testar métodos de compatibilidade
    console.print("[yellow]1. Testando get_running_jobs()...[/yellow]")
    running = queue_mgr.get_running_jobs()
    console.print(f"   Jobs em execução encontrados: {len(running)}")
    for job in running:
        console.print(f"   - {job['id'][:8]}: {job.get('progress', 0):.1f}%")
    
    console.print("\n[yellow]2. Testando get_pending_jobs()...[/yellow]")
    pending = queue_mgr.get_pending_jobs()
    console.print(f"   Jobs pendentes encontrados: {len(pending)}")
    for job in pending:
        console.print(f"   - {job['id'][:8]}: {job['input_path']}")
    
    console.print("\n[yellow]3. Testando list_jobs()...[/yellow]")
    all_jobs = queue_mgr.list_jobs()
    console.print(f"   Total de jobs encontrados: {len(all_jobs)}")
    
    # Exibir tabela com todos os jobs
    if all_jobs:
        console.print("\n[bold]Tabela de Jobs:[/bold]")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=10)
        table.add_column("Input", style="cyan")
        table.add_column("Status", style="white", width=15)
        table.add_column("Progresso", style="green", width=10)
        table.add_column("Prioridade", style="magenta", width=10)
        
        for job in all_jobs:
            job_id = job['id'][:8]
            input_file = Path(job['input_path']).name[:30]
            status = job['status']
            progress = f"{job.get('progress', 0):.1f}%"
            priority = str(job.get('priority', 2))
            
            table.add_row(job_id, input_file, status, progress, priority)
        
        console.print(table)
    else:
        console.print("\n[yellow]Nenhum job encontrado no sistema![/yellow]")
    
    # Estatísticas
    console.print("\n[yellow]4. Estatísticas do sistema:[/yellow]")
    stats = queue_mgr.get_statistics()
    console.print(f"   Total de jobs: {stats['total']}")
    console.print(f"   Jobs ativos: {stats['active']}")
    console.print(f"   Jobs na fila: {stats['by_status'].get('queued', 0) + stats['by_status'].get('pending', 0)}")
    console.print(f"   Jobs completados: {stats['by_status'].get('completed', 0)}")
    console.print(f"   Jobs falhados: {stats['by_status'].get('failed', 0)}")
    console.print(f"   Taxa de sucesso: {stats['success_rate']:.1f}%")
    
    # Verificar arquivo de persistência
    console.print("\n[yellow]5. Arquivo de persistência:[/yellow]")
    queue_file = Path("jobs/queue.json")
    if queue_file.exists():
        console.print(f"   ✓ Arquivo encontrado: {queue_file}")
        console.print(f"   Tamanho: {queue_file.stat().st_size} bytes")
    else:
        console.print(f"   ✗ Arquivo NÃO encontrado: {queue_file}")
    
    console.print("\n[bold green]Teste concluído![/bold green]\n")

if __name__ == "__main__":
    main()
