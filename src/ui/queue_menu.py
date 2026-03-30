"""UI para gerenciamento de fila de jobs."""

from rich.console import Console
from rich.table import Table
from rich.text import Text
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..managers.queue_manager import QueueManager, QueuePriority
from ..managers.job_manager import JobManager, JobStatus
from .menu import Menu


class QueueMenuUI:
    """Interface para gerenciamento de fila."""
    
    def __init__(self, console: Console, queue_mgr: QueueManager, job_mgr: JobManager):
        self.console = console
        self.queue_mgr = queue_mgr
        self.job_mgr = job_mgr
        self.menu = Menu(console)
    
    def show_submenu(self):
        """Exibe submenu de gerenciamento de fila."""
        from rich.live import Live
        from rich.panel import Panel
        from rich.table import Table
        import time
        
        running_jobs = self.job_mgr.get_running_jobs()
        
        if running_jobs:
            self._show_live_monitor_for_existing_jobs()
        
        while True:
            self.menu.clear()
            self.menu.print_header("Gerenciador de Fila")
            
            queue = self.queue_mgr.list_queue()
            is_paused = self.queue_mgr.is_paused()
            
            running = self.job_mgr.get_running_jobs()
            pending = self.job_mgr.get_pending_jobs()
            
            if running:
                self.console.print(f"[bold green]🔄 Jobs em execução: {len(running)}[/bold green]")
                for job in running[:3]:
                    progress = job.get('progress', 0)
                    self.console.print(f"  • {job['id'][:8]}: {progress:.1f}%")
                self.console.print()
            elif pending and queue:
                self.console.print(f"[bold yellow]⏳ Jobs pendentes: {len(pending)}[/bold yellow]")
                self.console.print()
            
            if queue:
                self._show_queue_table(queue)
                
                options = [
                    {"description": "Ver detalhes da fila", "shortcut": "1"},
                    {"description": "Pausar fila" if not is_paused else "Retomar fila", "shortcut": "2"},
                    {"description": "Limpar fila completa", "shortcut": "3"},
                    {"description": "Remover job específico", "shortcut": "4"},
                    {"description": "Mover prioridade do job", "shortcut": "5"},
                    {"description": "⚡ Processar fila agora", "shortcut": "6"},
                    {"description": "Voltar", "shortcut": "0"}
                ]
            else:
                self.menu.print_info("Fila vazia")
                options = [
                    {"description": "Voltar", "shortcut": "0"}
                ]
            
            choice = self.menu.show_menu("Menu", options)
            
            if choice == 0:
                if queue:
                    self._show_queue_details()
                else:
                    break
            elif choice == 1:
                if is_paused:
                    self.queue_mgr.resume()
                    self.menu.print_success("Fila retomada")
                else:
                    self.queue_mgr.pause()
                    self.menu.print_warning("Fila pausada")
                self.console.input("\nPressione Enter para continuar...")
            elif choice == 2:
                if self.menu.ask_confirm("Tem certeza que deseja limpar toda a fila?"):
                    count = self.queue_mgr.clear_queue()
                    self.menu.print_success(f"{count} job(s) removidos da fila")
                    self.console.input("\nPressione Enter para continuar...")
            elif choice == 3:
                self._remove_job_submenu()
            elif choice == 4:
                self._change_priority_submenu()
            elif choice == 5:
                self._process_queue_with_monitor()
            elif choice == 6:
                break
    
    def _show_queue_table(self, queue: List[Dict[str, Any]]):
        """Exibe tabela da fila."""
        table = Table(title="Fila de Jobs", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Job ID", style="dim", width=10)
        table.add_column("Input", style="cyan", width=35)
        table.add_column("Output", style="green", width=25)
        table.add_column("Perfil", style="blue", width=12)
        table.add_column("Status", style="white", width=12)
        table.add_column("Prog.", style="white", width=8)
        table.add_column("Prioridade", style="yellow", width=10)
        
        priorities = {1: 'LOW', 2: 'NORMAL', 3: 'HIGH', 4: 'CRITICAL'}
        
        for i, item in enumerate(queue, 1):
            # Obter status do job
            job_info = self.job_mgr.get_job(item['job_id'])
            if job_info:
                status = job_info.get('status', 'pending')
                progress = job_info.get('progress', 0)
            else:
                status = 'queued'
                progress = 0
            
            # Determinar cor e ícone do status
            if status == 'running':
                status_display = "[bold green]🔄 Execução[/bold green]"
            elif status == 'completed':
                status_display = "[green]✓ Completo[/green]"
            elif status == 'failed':
                status_display = "[red]✗ Falhou[/red]"
            elif status == 'cancelled':
                status_display = "[yellow]⊘ Cancelado[/yellow]"
            elif status == 'paused':
                status_display = "[yellow]⏸ Pausado[/yellow]"
            else:
                status_display = "[dim]⏳ Pendente[/dim]"
            
            # Formatar progresso
            if status == 'running' or progress > 0:
                progress_display = f"[cyan]{progress:.0f}%[/cyan]"
            else:
                progress_display = "[dim]--[/dim]"
            
            table.add_row(
                str(i),
                item['job_id'][:8],
                Path(item['input_path']).name[:33],
                Path(item['output_path']).name[:23],
                item['profile'].get('name', '')[:10],
                status_display,
                progress_display,
                priorities.get(item['priority'], 'NORMAL')
            )
        
        self.console.print(table)
        self.console.print()
    
    def _show_queue_details(self):
        """Exibe detalhes da fila."""
        from rich.panel import Panel
        stats = self.queue_mgr.get_queue_statistics()
        
        content = Text()
        content.append("[STATS] Fila de Jobs\n\n", style="bold magenta")
        content.append("Total de Jobs: ", style="cyan")
        content.append(f"{stats['total']}\n", style="white")
        content.append("Status: ", style="cyan")
        content.append(f"{'PAUSADA' if stats['paused'] else 'ATIVA'}\n\n", style="green" if not stats['paused'] else "yellow")
        content.append("Por Prioridade:\n", style="bold")
        content.append(f"  Critical: {stats['by_priority']['critical']}\n", style="red")
        content.append(f"  High:     {stats['by_priority']['high']}\n", style="yellow")
        content.append(f"  Normal:   {stats['by_priority']['normal']}\n", style="green")
        content.append(f"  Low:      {stats['by_priority']['low']}\n", style="dim")
        
        self.console.print(Panel(content, border_style="magenta", title="Detalhes da Fila"))
        self.console.input("\nPressione Enter para continuar...")
    
    def _remove_job_submenu(self):
        """Submenu para remover job específico."""
        queue = self.queue_mgr.list_queue()
        if not queue:
            self.menu.print_info("Fila vazia")
            return
        
        self.menu.clear()
        self.menu.print_header("Remover Job da Fila")
        
        table = Table(title="Jobs na Fila", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Job ID", style="dim", width=10)
        table.add_column("Input", style="cyan")
        table.add_column("Perfil", style="green")
        
        for i, item in enumerate(queue, 1):
            table.add_row(
                str(i),
                item['job_id'][:8],
                Path(item['input_path']).name[:40],
                item['profile'].get('name', '')[:20]
            )
        
        self.console.print(table)
        self.console.print()
        
        choice = self.menu.ask_int(
            "Número do job para remover (0 para cancelar)",
            default=0
        )
        
        if choice == 0:
            return
        
        if 1 <= choice <= len(queue):
            job_to_remove = queue[choice - 1]
            job_id = job_to_remove['job_id']
            
            if self.menu.ask_confirm(f"Remover job {job_id[:8]} da fila?"):
                if self.queue_mgr.remove_from_queue(job_id):
                    self.job_mgr.update_job_status(job_id, JobStatus.CANCELLED)
                    self.menu.print_success("Job removido da fila")
                else:
                    self.menu.print_error("Erro ao remover job")
                self.console.input("\nPressione Enter para continuar...")
        else:
            self.menu.print_error("Opção inválida")
            self.console.input("\nPressione Enter para continuar...")
    
    def _change_priority_submenu(self):
        """Submenu para mudar prioridade do job."""
        queue = self.queue_mgr.list_queue()
        if not queue:
            self.menu.print_info("Fila vazia")
            return
        
        self.menu.clear()
        self.menu.print_header("Mudar Prioridade do Job")
        
        table = Table(title="Jobs na Fila", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Job ID", style="dim", width=10)
        table.add_column("Input", style="cyan")
        table.add_column("Prioridade Atual", style="yellow")
        
        priorities = {1: 'LOW', 2: 'NORMAL', 3: 'HIGH', 4: 'CRITICAL'}
        
        for i, item in enumerate(queue, 1):
            table.add_row(
                str(i),
                item['job_id'][:8],
                Path(item['input_path']).name[:40],
                priorities.get(item['priority'], 'NORMAL')
            )
        
        self.console.print(table)
        self.console.print()
        
        choice = self.menu.ask_int(
            "Número do job para mudar prioridade (0 para cancelar)",
            default=0
        )
        
        if choice == 0:
            return
        
        if 1 <= choice <= len(queue):
            job_to_change = queue[choice - 1]
            job_id = job_to_change['job_id']
            
            priority_options = [
                {"description": "LOW", "shortcut": "1"},
                {"description": "NORMAL", "shortcut": "2"},
                {"description": "HIGH", "shortcut": "3"},
                {"description": "CRITICAL", "shortcut": "4"}
            ]
            
            priority_choice = self.menu.show_menu("Selecione a prioridade", priority_options)
            
            if 0 <= priority_choice <= 3:
                priority = QueuePriority(priority_choice + 1)
                if self.queue_mgr.set_job_priority(job_id, priority):
                    self.menu.print_success(f"Prioridade alterada para {priority.name}")
                else:
                    self.menu.print_error("Erro ao alterar prioridade")
                self.console.input("\nPressione Enter para continuar...")
        else:
            self.menu.print_error("Opção inválida")
            self.console.input("\nPressione Enter para continuar...")
    
    def _process_queue_with_monitor(self):
        """Processa fila com monitor em tempo real."""
        from ..core.encoder_engine import EncoderEngine, EncodingJob, EncodingStatus
        from ..core.hw_monitor import HardwareMonitor
        import time
        
        queue = self.queue_mgr.list_queue()
        if not queue:
            self.menu.print_info("Fila vazia")
            return
        
        self.menu.clear()
        self.console.print("[bold cyan]Iniciando processamento da fila com monitor em tempo real...[/bold cyan]\n")
        
        encoder = EncoderEngine(max_concurrent=1)
        hw_monitor = HardwareMonitor()
        
        def on_progress(job_id: str, progress: float):
            self.job_mgr.update_progress(job_id, progress)
        
        def map_encoding_to_job_status(encoding_status: EncodingStatus) -> JobStatus:
            mapping = {
                EncodingStatus.PENDING: JobStatus.PENDING,
                EncodingStatus.RUNNING: JobStatus.RUNNING,
                EncodingStatus.COMPLETED: JobStatus.COMPLETED,
                EncodingStatus.FAILED: JobStatus.FAILED,
                EncodingStatus.CANCELLED: JobStatus.CANCELLED,
                EncodingStatus.PAUSED: JobStatus.PAUSED
            }
            return mapping.get(encoding_status, JobStatus.PENDING)
        
        def on_status(job_id: str, status: EncodingStatus):
            job_status = map_encoding_to_job_status(status)
            self.job_mgr.update_job_status(job_id, job_status)
        
        encoder.add_progress_callback(on_progress)
        encoder.add_status_callback(on_status)
        encoder.start()
        hw_monitor.start()
        
        try:
            while True:
                active_count = len(encoder.get_all_jobs())
                max_concurrent = 1
                
                if active_count < max_concurrent:
                    next_job = self.queue_mgr.get_next_job()
                    if next_job:
                        job = EncodingJob(
                            id=next_job['job_id'],
                            input_path=next_job['input_path'],
                            output_path=next_job['output_path'],
                            profile=next_job['profile']
                        )
                        encoder.add_job(job)
                        self.queue_mgr.mark_job_started(next_job['job_id'])
                        self.console.print(f"\n[cyan]Iniciando job: {next_job['job_id'][:8]}[/cyan]")
                
                queue_remaining = self.queue_mgr.list_queue()
                pending_queue = [j for j in queue_remaining if not j.get('started_at')]
                
                if active_count == 0 and not pending_queue:
                    self.console.print("\n[green]✓ Todos os jobs foram processados![/green]")
                    break
                
                time.sleep(1)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Processamento interrompido pelo usuário[/yellow]")
        finally:
            encoder.stop()
            hw_monitor.stop()
        
        self.console.input("\nPressione Enter para continuar...")
    
    def _show_live_monitor_for_existing_jobs(self):
        """Mostra monitor em tempo real para jobs já em execução."""
        from ..core.encoder_engine import EncoderEngine, EncodingJob, EncodingStatus
        from ..core.hw_monitor import HardwareMonitor
        from ..ui.realtime_monitor import RealTimeEncodingMonitor, FFmpegProgressParser
        from ..core.ffmpeg_wrapper import FFmpegWrapper
        import time
        
        self.menu.clear()
        self.console.print("[bold cyan]Verificando jobs em execução...[/bold cyan]\n")
        
        running_jobs = self.job_mgr.get_running_jobs()
        if not running_jobs:
            return
        
        self.console.print(f"[green]Encontrados {len(running_jobs)} job(s) em execução[/green]\n")
        
        for job in running_jobs:
            self.console.print(f"Job: {job['id'][:8]}")
            self.console.print(f"  Input: {Path(job['input_path']).name}")
            self.console.print(f"  Progresso: {job.get('progress', 0):.1f}%")
            self.console.print()
        
        if self.menu.ask_confirm("Deseja monitorar o progresso destes jobs?", default=True):
            encoder = EncoderEngine(max_concurrent=1)
            hw_monitor = HardwareMonitor()
            
            def on_progress(job_id: str, progress: float):
                self.job_mgr.update_progress(job_id, progress)
            
            def map_encoding_to_job_status(encoding_status: EncodingStatus) -> JobStatus:
                mapping = {
                    EncodingStatus.PENDING: JobStatus.PENDING,
                    EncodingStatus.RUNNING: JobStatus.RUNNING,
                    EncodingStatus.COMPLETED: JobStatus.COMPLETED,
                    EncodingStatus.FAILED: JobStatus.FAILED,
                    EncodingStatus.CANCELLED: JobStatus.CANCELLED,
                    EncodingStatus.PAUSED: JobStatus.PAUSED
                }
                return mapping.get(encoding_status, JobStatus.PENDING)
            
            def on_status(job_id: str, status: EncodingStatus):
                job_status = map_encoding_to_job_status(status)
                self.job_mgr.update_job_status(job_id, job_status)
            
            encoder.add_progress_callback(on_progress)
            encoder.add_status_callback(on_status)
            encoder.start()
            hw_monitor.start()
            
            try:
                while True:
                    active_count = len(encoder.get_all_jobs())
                    
                    if active_count < 1:
                        next_job = self.queue_mgr.get_next_job()
                        if next_job:
                            job = EncodingJob(
                                id=next_job['job_id'],
                                input_path=next_job['input_path'],
                                output_path=next_job['output_path'],
                                profile=next_job['profile']
                            )
                            encoder.add_job(job)
                            self.queue_mgr.mark_job_started(next_job['job_id'])
                    
                    queue_remaining = self.queue_mgr.list_queue()
                    pending_queue = [j for j in queue_remaining if not j.get('started_at')]
                    
                    if active_count == 0 and not pending_queue:
                        self.console.print("\n[green]✓ Todos os jobs foram processados![/green]")
                        break
                    
                    time.sleep(1)
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Monitoramento interrompido[/yellow]")
            finally:
                encoder.stop()
                hw_monitor.stop()


def show_queue_submenu(menu: Menu, queue_mgr: QueueManager, job_mgr: JobManager):
    """Função helper para exibir submenu de fila."""
    ui = QueueMenuUI(Console(), queue_mgr, job_mgr)
    ui.show_submenu()
