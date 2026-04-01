"""UI para gerenciamento de fila de jobs."""

import sys
from rich.console import Console
from rich.table import Table
from rich.text import Text
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    from ..managers.queue_manager import QueueManager, QueuePriority
    from ..managers.job_manager import JobManager, JobStatus
except ImportError:
    # Para testes diretos
    from managers.queue_manager import QueueManager, QueuePriority
    from managers.job_manager import JobManager, JobStatus
from .menu import Menu


def check_debug_key(encoder):
    """Verifica se a tecla 'D' foi pressionada para toggle de debug."""
    try:
        import msvcrt  # Windows
        
        if msvcrt.kbhit():
            char = msvcrt.getwch()
            if char.lower() == 'd':
                debug_enabled = encoder.toggle_debug()
                # Adiciona log de sistema que será exibido no monitor quando debug estiver ativo
                encoder.realtime_monitor._add_debug_log(f"Debug {'ativado' if debug_enabled else 'desativado'} via tecla D")
                return True
    except ImportError:
        # Linux/Mac
        try:
            import tty
            import termios
            import select
            
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                if select.select([sys.stdin], [], [], 0)[0]:
                    char = sys.stdin.read(1)
                    if char.lower() == 'd':
                        debug_enabled = encoder.toggle_debug()
                        encoder.realtime_monitor._add_debug_log(f"Debug {'ativado' if debug_enabled else 'desativado'} via tecla D")
                        return True
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            pass
    
    return False


class QueueMenuUI:
    """Interface para gerenciamento de fila."""
    
    def __init__(self, console: Console, queue_mgr: QueueManager, job_mgr: JobManager):
        self.console = console
        self.queue_mgr = queue_mgr
        self.job_mgr = job_mgr
        self.menu = Menu(console)
    
    def _get_status_display(self, status: str) -> str:
        """Retorna a representação formatada do status para exibição."""
        if status == 'running':
            return "[bold green]🔄 Execução[/bold green]"
        elif status == 'completed':
            return "[green]✓ Completo[/green]"
        elif status == 'failed':
            return "[red]✗ Falhou[/red]"
        elif status == 'cancelled':
            return "[yellow]⊘ Cancelado[/yellow]"
        elif status == 'paused':
            return "[yellow]⏸ Pausado[/yellow]"
        else:
            return "[dim]⏳ Pendente[/dim]"
    
    def _calculate_eta_and_speed(self, job_info: Dict[str, Any]) -> tuple:
        """Calcula ETA e velocidade de encoding para um job."""
        import math
        from datetime import datetime
        
        if not job_info.get('started_at'):
            return ("--", "--", "--")
        
        try:
            started_at = datetime.fromisoformat(job_info['started_at'])
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
            eta_str = self._format_duration(eta_seconds) if eta_seconds > 0 else "--"
            
            # Formatar velocidade
            speed_str = f"{speed_percent_per_min:.1f}%/min" if speed_percent_per_min > 0 else "--"
            
            # Formatar tempo decorrido
            elapsed_str = self._format_duration(elapsed_seconds)
            
            return (elapsed_str, eta_str, speed_str)
        except Exception:
            return ("--", "--", "--")
    
    def _format_duration(self, seconds: float) -> str:
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
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Formata tamanho de arquivo em unidades legíveis."""
        if size_bytes <= 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def _get_job_resources_usage(self, job_id: str) -> str:
        """Obtém uso de recursos para um job específico (placeholder)."""
        # Esta função seria implementada com dados reais de uso de recursos
        # Por enquanto, retornamos um placeholder
        return "N/A"
    
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
                    {"description": "Processar fila agora", "shortcut": "6"},
                    {"description": "Gerenciar job individual", "shortcut": "7"},
                    {"description": "Voltar", "shortcut": "8"}
                ]
            else:
                self.menu.print_info("Fila vazia")
                options = [
                    {"description": "Voltar", "shortcut": "1"}
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
                self._manage_individual_job()
            elif choice == 7:
                break
    
    def _show_queue_table(self, queue: List[Dict[str, Any]]):
        """Exibe tabela da fila com informações detalhadas."""
        table = Table(title="Fila de Jobs", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Job ID", style="dim", width=10)
        table.add_column("Input", style="cyan", width=25)
        table.add_column("Output", style="green", width=15)
        table.add_column("Perfil", style="blue", width=10)
        table.add_column("Status", style="white", width=12)
        table.add_column("Prog.", style="white", width=8)
        table.add_column("Tempo", style="yellow", width=10)
        table.add_column("ETA", style="magenta", width=10)
        table.add_column("Veloc.", style="cyan", width=10)
        table.add_column("Tamanho", style="white", width=15)
        table.add_column("Prioridade", style="yellow", width=10)
        
        priorities = {1: 'LOW', 2: 'NORMAL', 3: 'HIGH', 4: 'CRITICAL'}
        
        for i, item in enumerate(queue, 1):
            job_info = self.job_mgr.get_job(item['job_id'])
            if job_info:
                status = job_info.get('status', 'pending')
                progress = job_info.get('progress', 0)
            else:
                status = 'queued'
                progress = 0
            
            status_display = self._get_status_display(status)
            
            if status == 'running' or progress > 0:
                progress_display = f"[cyan]{progress:.0f}%[/cyan]"
            else:
                progress_display = "[dim]--[/dim]"
            
            # Calcular informações detalhadas
            elapsed_time = "--"
            eta = "--"
            speed = "--"
            
            if job_info and status == 'running':
                elapsed_time, eta, speed = self._calculate_eta_and_speed(job_info)
            
            # Formatar tamanhos
            input_size = "--"
            output_size = "--"
            if job_info:
                input_size = self._format_file_size(job_info.get('input_size', 0))
                output_size = self._format_file_size(job_info.get('output_size', 0))
            
            size_display = f"{input_size}→{output_size}"
            
            table.add_row(
                str(i),
                item['job_id'][:8],
                Path(item['input_path']).name[:23],
                Path(item['output_path']).name[:13],
                item['profile'].get('name', '')[:8],
                status_display,
                progress_display,
                elapsed_time,
                eta,
                speed,
                size_display,
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
        from rich.panel import Panel
        from datetime import datetime
        
        queue = self.queue_mgr.list_queue()
        if not queue:
            self.menu.print_info("Fila vazia")
            return
        
        self.menu.clear()
        self.menu.print_header("Remover Job da Fila")
        
        priorities = {1: 'LOW', 2: 'NORMAL', 3: 'HIGH', 4: 'CRITICAL'}
        
        table = Table(title="Jobs na Fila", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Job ID", style="dim", width=10)
        table.add_column("Input", style="cyan")
        table.add_column("Perfil", style="green")
        table.add_column("Status", style="white", width=15)
        
        for i, item in enumerate(queue, 1):
            job_info = self.job_mgr.get_job(item['job_id'])
            if job_info:
                status = job_info.get('status', 'pending')
            else:
                status = 'queued'
            
            status_display = self._get_status_display(status)
            
            table.add_row(
                str(i),
                item['job_id'][:8],
                Path(item['input_path']).name[:40],
                item['profile'].get('name', '')[:20],
                status_display
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
            
            job_info = self.job_mgr.get_job(job_id)
            
            self.console.print()
            content = Text()
            content.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", style="dim")
            content.append("DETALHES DO JOB SELECIONADO\n", style="bold yellow")
            content.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n", style="dim")
            
            content.append("📋 Job ID: ", style="cyan")
            content.append(f"{job_id}\n", style="white")
            
            content.append("📁 Input: ", style="cyan")
            content.append(f"{Path(job_to_remove['input_path']).name}\n", style="white")
            
            content.append("💾 Output: ", style="cyan")
            content.append(f"{Path(job_to_remove['output_path']).name}\n", style="white")
            
            content.append("🎬 Perfil: ", style="cyan")
            content.append(f"{job_to_remove['profile'].get('name', 'N/A')}\n", style="white")
            
            if job_info:
                status = job_info.get('status', 'pending')
                progress = job_info.get('progress', 0)
                content.append("📊 Status: ", style="cyan")
                content.append(f"{self._get_status_display(status)}\n", style="white")
                
                content.append("📈 Progresso: ", style="cyan")
                if status == 'running' or progress > 0:
                    content.append(f"{progress:.1f}%\n", style="green")
                else:
                    content.append("Não iniciado\n", style="dim")
                
                created_at = job_info.get('created_at')
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at)
                        content.append("🕐 Criado em: ", style="cyan")
                        content.append(f"{dt.strftime('%d/%m/%Y %H:%M:%S')}\n", style="white")
                    except Exception:
                        pass
                
                started_at = job_info.get('started_at')
                if started_at:
                    try:
                        dt = datetime.fromisoformat(started_at)
                        content.append("▶️ Iniciado em: ", style="cyan")
                        content.append(f"{dt.strftime('%d/%m/%Y %H:%M:%S')}\n", style="white")
                    except Exception:
                        pass
                
                completed_at = job_info.get('completed_at')
                if completed_at:
                    try:
                        dt = datetime.fromisoformat(completed_at)
                        content.append("✅ Concluído em: ", style="cyan")
                        content.append(f"{dt.strftime('%d/%m/%Y %H:%M:%S')}\n", style="white")
                    except Exception:
                        pass
                
                error_message = job_info.get('error_message')
                if error_message:
                    content.append("❌ Erro: ", style="red")
                    content.append(f"{error_message}\n", style="red")
            else:
                content.append("📊 Status: ", style="cyan")
                content.append("Na fila (aguardando)\n", style="dim")
            
            priority_value = job_to_remove.get('priority', 2)
            priority_name = priorities.get(priority_value, 'NORMAL')
            content.append("\n🏷️ Prioridade: ", style="cyan")
            content.append(f"{priority_name}\n", style="yellow")
            
            content.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", style="dim")
            
            self.console.print(Panel(content, border_style="yellow", title="[bold red]⚠ Job Selecionado para Remoção[/bold red]"))
            self.console.print()
            
            if self.menu.ask_confirm(f"Confirma a remoção do job {job_id[:8]} da fila?"):
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
        try:
            from ..core.encoder_engine import EncoderEngine, EncodingJob, EncodingStatus
            from ..core.hw_monitor import HardwareMonitor
        except ImportError:
            # Para testes diretos
            from core.encoder_engine import EncoderEngine, EncodingJob, EncodingStatus
            from core.hw_monitor import HardwareMonitor
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
        
        def on_status_queue(job_id: str, status: EncodingStatus):
            on_status(job_id, status)
            if status in (EncodingStatus.COMPLETED, EncodingStatus.FAILED, EncodingStatus.CANCELLED):
                self.queue_mgr.remove_from_queue(job_id)

        encoder.add_progress_callback(on_progress)
        encoder.add_status_callback(on_status_queue)
        encoder.start()
        hw_monitor.start()

        try:
            while True:
                running_count = len(encoder.get_active_jobs())
                pending_in_encoder = len(encoder.get_pending_jobs())

                if (running_count + pending_in_encoder) < 1:
                    next_job = self.queue_mgr.pop_next_job()
                    if next_job:
                        job = EncodingJob(
                            id=next_job['job_id'],
                            input_path=next_job['input_path'],
                            output_path=next_job['output_path'],
                            profile=next_job['profile']
                        )
                        encoder.add_job(job)
                        self.console.print(f"\n[cyan]Iniciando job: {next_job['job_id'][:8]}[/cyan]")

                queue_empty = self.queue_mgr.get_queue_length() == 0
                if not running_count and not pending_in_encoder and queue_empty:
                    self.console.print("\n[green]Todos os jobs foram processados![/green]")
                    break

                # Verifica se tecla 'D' foi pressionada para toggle de debug
                check_debug_key(encoder)

                time.sleep(1)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Processamento interrompido pelo usuário[/yellow]")
        finally:
            encoder.stop()
            hw_monitor.stop()
        
        self.console.input("\nPressione Enter para continuar...")
    
    def _manage_individual_job(self):
        """Submenu para gerenciar job individual."""
        from rich.panel import Panel
        from datetime import datetime
        
        # Obter todos os jobs (ativos e na fila)
        all_jobs = self.job_mgr.list_jobs()
        if not all_jobs:
            self.menu.print_info("Nenhum job encontrado")
            return
        
        self.menu.clear()
        self.menu.print_header("Gerenciar Job Individual")
        
        # Filtrar jobs que podem ser gerenciados (não-completos)
        manageable_jobs = [job for job in all_jobs if job['status'] not in ['completed', 'cancelled', 'failed']]
        
        if not manageable_jobs:
            self.menu.print_info("Nenhum job ativo para gerenciar")
            return
        
        table = Table(title="Jobs Disponíveis", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Job ID", style="dim", width=10)
        table.add_column("Input", style="cyan")
        table.add_column("Status", style="white", width=15)
        table.add_column("Progresso", style="green", width=10)
        
        for i, job in enumerate(manageable_jobs, 1):
            status_display = self._get_status_display(job['status'])
            progress = job.get('progress', 0)
            progress_display = f"{progress:.1f}%" if progress > 0 else "--"
            
            table.add_row(
                str(i),
                job['id'][:8],
                Path(job['input_path']).name[:40],
                status_display,
                progress_display
            )
        
        self.console.print(table)
        self.console.print()
        
        choice = self.menu.ask_int(
            "Número do job para gerenciar (0 para cancelar)",
            default=0
        )
        
        if choice == 0:
            return
        
        if 1 <= choice <= len(manageable_jobs):
            selected_job = manageable_jobs[choice - 1]
            self._show_job_management_options(selected_job)
        else:
            self.menu.print_error("Opção inválida")
            self.console.input("\nPressione Enter para continuar...")
    
    def _show_job_management_options(self, job: Dict[str, Any]):
        """Mostra opções de gerenciamento para um job específico."""
        from rich.panel import Panel
        from datetime import datetime
        
        self.menu.clear()
        self.menu.print_header(f"Gerenciar Job: {job['id'][:8]}")
        
        # Exibir detalhes do job
        content = Text()
        content.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", style="dim")
        content.append("DETALHES DO JOB\n", style="bold yellow")
        content.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n", style="dim")
        
        content.append("📋 Job ID: ", style="cyan")
        content.append(f"{job['id']}\n", style="white")
        
        content.append("📁 Input: ", style="cyan")
        content.append(f"{Path(job['input_path']).name}\n", style="white")
        
        content.append("💾 Output: ", style="cyan")
        content.append(f"{Path(job['output_path']).name}\n", style="white")
        
        content.append("🎬 Perfil: ", style="cyan")
        content.append(f"{job['profile_name']}\n", style="white")
        
        content.append("📊 Status: ", style="cyan")
        content.append(f"{self._get_status_display(job['status'])}\n", style="white")
        
        progress = job.get('progress', 0)
        content.append("📈 Progresso: ", style="cyan")
        content.append(f"{progress:.1f}%\n", style="green")
        
        # Mostrar informações de tempo se estiver em execução
        if job['status'] == 'running':
            elapsed, eta, speed = self._calculate_eta_and_speed(job)
            content.append("⏱️ Tempo decorrido: ", style="cyan")
            content.append(f"{elapsed}\n", style="white")
            content.append("⏰ ETA estimada: ", style="cyan")
            content.append(f"{eta}\n", style="white")
            content.append("⚡ Velocidade: ", style="cyan")
            content.append(f"{speed}\n", style="white")
        
        created_at = job.get('created_at')
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at)
                content.append("🕐 Criado em: ", style="cyan")
                content.append(f"{dt.strftime('%d/%m/%Y %H:%M:%S')}\n", style="white")
            except Exception:
                pass
        
        started_at = job.get('started_at')
        if started_at:
            try:
                dt = datetime.fromisoformat(started_at)
                content.append("▶️ Iniciado em: ", style="cyan")
                content.append(f"{dt.strftime('%d/%m/%Y %H:%M:%S')}\n", style="white")
            except Exception:
                pass
        
        # Tamanhos
        input_size = self._format_file_size(job.get('input_size', 0))
        output_size = self._format_file_size(job.get('output_size', 0))
        content.append("📏 Tamanho: ", style="cyan")
        content.append(f"{input_size} → {output_size}\n", style="white")
        
        content.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", style="dim")
        
        self.console.print(Panel(content, border_style="yellow", title=f"[bold]Job {job['id'][:8]}[/bold]"))
        self.console.print()
        
        # Opções de gerenciamento
        options = [
            {"description": "Cancelar job", "shortcut": "1"},
            {"description": "Pausar job" if job['status'] == 'running' else "Retomar job", "shortcut": "2"},
            {"description": "Ver logs detalhados", "shortcut": "3"},
            {"description": "Voltar", "shortcut": "4"}
        ]
        
        choice = self.menu.show_menu("Opções de Gerenciamento", options)
        
        if choice == 0:  # Cancelar job
            self._cancel_job_confirmation(job['id'])
        elif choice == 1:  # Pausar/Retomar
            if job['status'] == 'running':
                self._pause_job(job['id'])
            else:
                self._resume_job(job['id'])
        elif choice == 2:  # Ver logs
            self._view_job_logs(job['id'])
        elif choice == 3:  # Voltar
            return
    
    def _cancel_job_confirmation(self, job_id: str):
        """Confirmação para cancelar job."""
        job = self.job_mgr.get_job(job_id)
        if not job:
            self.menu.print_error("Job não encontrado")
            return
        
        self.console.print(f"\n[bold red]⚠ ATENÇÃO: Cancelar job {job_id[:8]}?[/bold red]")
        self.console.print("[yellow]Esta operação não pode ser desfeita.[/yellow]")
        
        if self.menu.ask_confirm("Confirmar cancelamento?"):
            # Atualizar status do job para cancelled
            try:
                from ..managers.job_manager import JobStatus
            except ImportError:
                from managers.job_manager import JobStatus
                
            if self.job_mgr.update_job_status(job_id, JobStatus.CANCELLED):
                # Remover da fila se estiver lá
                self.queue_mgr.remove_from_queue(job_id)
                
                self.menu.print_success(f"Job {job_id[:8]} cancelado")
            else:
                self.menu.print_error("Erro ao cancelar job")
        
        self.console.input("\nPressione Enter para continuar...")
    
    def _pause_job(self, job_id: str):
        """Pausa um job em execução."""
        try:
            from ..managers.job_manager import JobStatus
        except ImportError:
            from managers.job_manager import JobStatus
            
        job = self.job_mgr.get_job(job_id)
        if not job:
            self.menu.print_error("Job não encontrado")
            return
        
        # Atualizar status do job para paused
        if self.job_mgr.update_job_status(job_id, JobStatus.PAUSED):
            self.menu.print_success(f"Job {job_id[:8]} pausado")
        else:
            self.menu.print_error("Erro ao pausar job")
        
        self.console.input("\nPressione Enter para continuar...")
    
    def _resume_job(self, job_id: str):
        """Retoma um job pausado."""
        try:
            from ..managers.job_manager import JobStatus
        except ImportError:
            from managers.job_manager import JobStatus
            
        job = self.job_mgr.get_job(job_id)
        if not job:
            self.menu.print_error("Job não encontrado")
            return
        
        # Atualizar status do job para running
        if self.job_mgr.update_job_status(job_id, JobStatus.RUNNING):
            self.menu.print_success(f"Job {job_id[:8]} retomado")
        else:
            self.menu.print_error("Erro ao retomar job")
        
        self.console.input("\nPressione Enter para continuar...")
    
    def _view_job_logs(self, job_id: str):
        """Visualiza logs detalhados do job."""
        # Placeholder para visualização de logs
        self.menu.print_info("Visualização de logs detalhados não implementada")
        self.console.input("\nPressione Enter para continuar...")
    
    def _show_live_monitor_for_existing_jobs(self):
        """Mostra monitor em tempo real para jobs já em execução."""
        try:
            from ..core.encoder_engine import EncoderEngine, EncodingJob, EncodingStatus
            from ..core.hw_monitor import HardwareMonitor
        except ImportError:
            # Para testes diretos
            from core.encoder_engine import EncoderEngine, EncodingJob, EncodingStatus
            from core.hw_monitor import HardwareMonitor
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
            
            def on_status_queue(job_id: str, status: EncodingStatus):
                on_status(job_id, status)
                if status in (EncodingStatus.COMPLETED, EncodingStatus.FAILED, EncodingStatus.CANCELLED):
                    self.queue_mgr.remove_from_queue(job_id)

            encoder.add_progress_callback(on_progress)
            encoder.add_status_callback(on_status_queue)
            encoder.start()
            hw_monitor.start()

            try:
                while True:
                    running_count = len(encoder.get_active_jobs())
                    pending_in_encoder = len(encoder.get_pending_jobs())

                    if (running_count + pending_in_encoder) < 1:
                        next_job = self.queue_mgr.pop_next_job()
                        if next_job:
                            job = EncodingJob(
                                id=next_job['job_id'],
                                input_path=next_job['input_path'],
                                output_path=next_job['output_path'],
                                profile=next_job['profile']
                            )
                            encoder.add_job(job)

                    queue_empty = self.queue_mgr.get_queue_length() == 0
                    if not running_count and not pending_in_encoder and queue_empty:
                        self.console.print("\n[green]Todos os jobs foram processados![/green]")
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