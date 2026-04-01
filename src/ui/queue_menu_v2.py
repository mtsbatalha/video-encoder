"""
Queue Menu UI v2 - Interface de gerenciamento de fila de encoding.

Esta módulo implementa uma interface de usuário moderna e completa para
gerenciamento da fila de encoding usando a biblioteca Rich.

Author: Video Encoder Team
Version: 2.0.0
"""

import sys
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

try:
    from ..managers.unified_queue_manager import (
        UnifiedQueueManager,
        JobStatus,
        QueuePriority,
        QueueJob
    )
except ImportError:
    from managers.unified_queue_manager import (
        UnifiedQueueManager,
        JobStatus,
        QueuePriority,
        QueueJob
    )

def _get_menu_class():
    """Obtém a classe Menu dinamicamente para evitar importação circular."""
    try:
        from ..ui.menu import Menu
        return Menu
    except (ImportError, ValueError):
        try:
            from ui.menu import Menu
            return Menu
        except ImportError:
            # Fallback: criar classe mínima
            class MinimalMenu:
                def __init__(self, console):
                    self.console = console
                def clear(self):
                    self.console.clear()
                def print_header(self, text):
                    self.console.print(f"\n[bold magenta]═{text}═[/bold magenta]\n")
                def print_info(self, text):
                    self.console.print(f"[cyan]{text}[/cyan]")
                def print_success(self, text):
                    self.console.print(f"[green]{text}[/green]")
                def print_warning(self, text):
                    self.console.print(f"[yellow]{text}[/yellow]")
                def print_error(self, text):
                    self.console.print(f"[red]{text}[/red]")
                def ask_int(self, prompt, default=0):
                    try:
                        return int(input(f"{prompt} [{default}]: ") or default)
                    except ValueError:
                        return default
                def ask_confirm(self, prompt, default=False):
                    resp = input(f"{prompt} [{'y/N' if not default else 'Y/n'}]: ").lower()
                    if default:
                        return resp != 'n'
                    return resp in ('y', 's')
                def show_menu(self, title, options):
                    self.console.print(f"\n[bold]{title}:[/bold]")
                    for i, opt in enumerate(options):
                        self.console.print(f"  [{opt['shortcut']}] {opt['description']}")
                    try:
                        choice = int(input("Escolha: ") or -1)
                        return choice - 1 if choice > 0 else -1
                    except ValueError:
                        return -1
            return MinimalMenu

Menu = _get_menu_class()


class QueueMenuUIV2:
    """
    Interface de usuário para gerenciamento de fila de encoding.
    
    Funcionalidades:
    - Tabela detalhada com todos os jobs
    - Informações em tempo real (progresso, ETA, velocidade)
    - Gerenciamento individual de jobs (pausar, retomar, cancelar)
    - Gerenciamento em lote da fila
    - Estatísticas visuais
    - Monitoramento em tempo real
    """
    
    def __init__(self, console: Console, queue_mgr: UnifiedQueueManager):
        """
        Inicializa a UI da fila.
        
        Args:
            console: Instância do Rich Console
            queue_mgr: Instância do UnifiedQueueManager
        """
        self.console = console
        self.queue_mgr = queue_mgr
        self.menu = Menu(console)
    
    # =========================================================================
    # MÉTODOS UTILITÁRIOS DE FORMATAÇÃO
    # =========================================================================
    
    def _get_status_style(self, status: str) -> str:
        """Retorna o estilo de cor para um status."""
        styles = {
            JobStatus.PENDING.value: "dim",
            JobStatus.QUEUED.value: "cyan",
            JobStatus.RUNNING.value: "bold green",
            JobStatus.PAUSED.value: "yellow",
            JobStatus.COMPLETED.value: "green",
            JobStatus.FAILED.value: "bold red",
            JobStatus.CANCELLED.value: "dim red"
        }
        return styles.get(status, "white")
    
    def _get_status_label(self, status: str) -> str:
        """Retorna label formatado para um status."""
        labels = {
            JobStatus.PENDING.value: "[dim]Pendente[/dim]",
            JobStatus.QUEUED.value: "[cyan]Na Fila[/cyan]",
            JobStatus.RUNNING.value: "[bold green]Executando[/bold green]",
            JobStatus.PAUSED.value: "[yellow]Pausado[/yellow]",
            JobStatus.COMPLETED.value: "[green]Completo[/green]",
            JobStatus.FAILED.value: "[bold red]Falhou[/bold red]",
            JobStatus.CANCELLED.value: "[dim red]Cancelado[/dim red]"
        }
        return labels.get(status, status)
    
    def _get_priority_label(self, priority: int) -> str:
        """Retorna label formatado para prioridade."""
        labels = {
            QueuePriority.LOW.value: "[dim]LOW[/dim]",
            QueuePriority.NORMAL.value: "[green]NORMAL[/green]",
            QueuePriority.HIGH.value: "[yellow]HIGH[/yellow]",
            QueuePriority.CRITICAL.value: "[bold red]CRITICAL[/bold red]"
        }
        return labels.get(priority, f"[white]{priority}[/white]")
    
    def _format_duration(self, seconds: float) -> str:
        """Formata duração em segundos para HH:MM:SS."""
        if seconds <= 0:
            return "--:--:--"
        
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
    
    def _format_percentage(self, value: float, max_value: float = 100.0) -> str:
        """Formata porcentagem com barra de progresso."""
        if value <= 0:
            return "[dim]0%[/dim]"
        
        pct = (value / max_value) * 100 if max_value > 0 else 0
        
        if pct < 25:
            color = "red"
        elif pct < 50:
            color = "yellow"
        elif pct < 75:
            color = "cyan"
        else:
            color = "green"
        
        # Criar barra de progresso
        bar_width = 20
        filled = int((pct / 100) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        return f"[{color}][{bar}] {pct:.1f}%[/{color}]"
    
    def _calculate_eta_and_speed(self, job: QueueJob) -> tuple:
        """
        Calcula ETA e velocidade de encoding para um job.
        
        Returns:
            tuple: (elapsed_str, eta_str, speed_str)
        """
        if not job.started_at:
            return ("--:--:--", "--:--:--", "--")
        
        try:
            started_at = datetime.fromisoformat(job.started_at)
            now = datetime.now()
            elapsed = now - started_at
            elapsed_seconds = elapsed.total_seconds()
            
            # Tempo decorrido
            elapsed_str = self._format_duration(elapsed_seconds)
            
            # Calcular velocidade e ETA
            if job.progress > 0 and elapsed_seconds > 0:
                # Velocidade em %/min
                speed_per_min = (job.progress / elapsed_seconds) * 60
                speed_str = f"{speed_per_min:.1f}%/min" if speed_per_min > 0 else "--"
                
                # ETA
                remaining_percent = 100 - job.progress
                eta_seconds = remaining_percent / (job.progress / elapsed_seconds)
                eta_str = self._format_duration(eta_seconds)
            else:
                speed_str = "--"
                eta_str = "--:--:--"
            
            return (elapsed_str, eta_str, speed_str)
            
        except Exception:
            return ("--:--:--", "--:--:--", "--")
    
    # =========================================================================
    # MÉTODOS DE EXIBIÇÃO
    # =========================================================================
    
    def _show_queue_table(self, queue: List[QueueJob]):
        """
        Exibe tabela da fila com informações detalhadas.
        
        Args:
            queue: Lista de jobs para exibir
        """
        table = Table(
            title="[bold magenta]Fila de Jobs[/bold magenta]",
            show_header=True,
            header_style="bold magenta",
            border_style="dim",
            show_lines=True
        )
        
        # Adicionar colunas
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Job ID", style="dim", width=10)
        table.add_column("Input", style="cyan", width=25)
        table.add_column("Output", style="green", width=20)
        table.add_column("Perfil", style="blue", width=15)
        table.add_column("Status", style="white", width=15)
        table.add_column("Progresso", style="white", width=25)
        table.add_column("Tempo", style="yellow", width=10)
        table.add_column("ETA", style="magenta", width=10)
        table.add_column("Veloc.", style="cyan", width=10)
        table.add_column("Tamanho", style="white", width=18)
        table.add_column("Prioridade", style="yellow", width=12)
        
        for i, job in enumerate(queue, 1):
            # Calcular informações de tempo
            elapsed, eta, speed = self._calculate_eta_and_speed(job)
            
            # Formatar tamanhos
            input_size = self._format_file_size(job.input_size)
            output_size = self._format_file_size(job.output_size)
            size_display = f"{input_size} → {output_size}"
            
            # Extrair nomes dos arquivos
            input_name = Path(job.input_path).name[:23]
            output_name = Path(job.output_path).name[:18]
            
            table.add_row(
                str(i),
                job.id[:8],
                input_name,
                output_name,
                job.profile_name[:13],
                self._get_status_label(job.status),
                self._format_percentage(job.progress),
                elapsed,
                eta,
                speed,
                size_display,
                self._get_priority_label(job.priority)
            )
        
        self.console.print(table)
        self.console.print()
    
    def _show_job_details_panel(self, job: QueueJob):
        """
        Exibe painel com detalhes completos de um job.
        
        Args:
            job: Job para exibir detalhes
        """
        content = Text()
        
        # Cabeçalho
        content.append("═" * 55 + "\n", style="bold yellow")
        content.append("  DETALHES DO JOB\n", style="bold yellow")
        content.append("═" * 55 + "\n\n", style="bold yellow")
        
        # Informações básicas
        content.append("ID do Job: ", style="cyan")
        content.append(f"{job.id}\n", style="white")
        
        content.append("Status: ", style="cyan")
        content.append(f"{self._get_status_label(job.status)}\n")
        
        content.append("Prioridade: ", style="cyan")
        content.append(f"{self._get_priority_label(job.priority)}\n\n")
        
        # Arquivos
        content.append("─" * 55 + "\n", style="dim")
        content.append("  ARQUIVOS\n", style="bold")
        content.append("─" * 55 + "\n\n", style="dim")
        
        content.append("Input: ", style="cyan")
        content.append(f"{job.input_path}\n", style="white")
        
        content.append("Output: ", style="cyan")
        content.append(f"{job.output_path}\n", style="white")
        
        content.append("Perfil: ", style="cyan")
        content.append(f"{job.profile_name}\n", style="white")
        
        # Detalhes do perfil
        if job.profile:
            codec = job.profile.get('codec', 'N/A')
            resolution = job.profile.get('resolution', 'N/A')
            bitrate = job.profile.get('bitrate', 'N/A')
            
            content.append(f"  Codec: {codec} | Resolução: {resolution} | Bitrate: {bitrate}\n", style="dim")
        
        content.append("\n")
        
        # Progresso e tempo
        content.append("─" * 55 + "\n", style="dim")
        content.append("  PROGRESSO E TEMPO\n", style="bold")
        content.append("─" * 55 + "\n\n", style="dim")
        
        content.append("Progresso: ", style="cyan")
        content.append(f"{self._format_percentage(job.progress)}\n")
        
        # Calcular tempo
        elapsed, eta, speed = self._calculate_eta_and_speed(job)
        
        content.append("Tempo Decorrido: ", style="cyan")
        content.append(f"{elapsed}\n", style="white")
        
        content.append("ETA Estimado: ", style="cyan")
        content.append(f"{eta}\n", style="magenta")
        
        content.append("Velocidade: ", style="cyan")
        content.append(f"{speed}\n", style="cyan")
        
        content.append("\n")
        
        # Tamanhos
        content.append("─" * 55 + "\n", style="dim")
        content.append("  TAMANHOS\n", style="bold")
        content.append("─" * 55 + "\n\n", style="dim")
        
        input_size_fmt = self._format_file_size(job.input_size)
        output_size_fmt = self._format_file_size(job.output_size)
        
        content.append("Tamanho Original: ", style="cyan")
        content.append(f"{input_size_fmt}\n", style="white")
        
        content.append("Tamanho Codificado: ", style="cyan")
        content.append(f"{output_size_fmt}\n", style="green")
        
        if job.compression_ratio > 0:
            ratio_pct = job.compression_ratio * 100
            content.append(f"Compressão: ", style="cyan")
            content.append(f"{ratio_pct:.1f}% do original\n", style="yellow")
        
        content.append("\n")
        
        # Timestamps
        content.append("─" * 55 + "\n", style="dim")
        content.append("  TIMESTAMPS\n", style="bold")
        content.append("─" * 55 + "\n\n", style="dim")
        
        content.append("Criado em: ", style="cyan")
        try:
            dt = datetime.fromisoformat(job.created_at)
            content.append(f"{dt.strftime('%d/%m/%Y %H:%M:%S')}\n", style="white")
        except Exception:
            content.append(f"{job.created_at}\n", style="white")
        
        if job.started_at:
            content.append("Iniciado em: ", style="cyan")
            try:
                dt = datetime.fromisoformat(job.started_at)
                content.append(f"{dt.strftime('%d/%m/%Y %H:%M:%S')}\n", style="white")
            except Exception:
                content.append(f"{job.started_at}\n", style="white")
        
        if job.completed_at:
            content.append("Concluído em: ", style="cyan")
            try:
                dt = datetime.fromisoformat(job.completed_at)
                content.append(f"{dt.strftime('%d/%m/%Y %H:%M:%S')}\n", style="white")
            except Exception:
                content.append(f"{job.completed_at}\n", style="white")
        
        content.append("\n")
        
        # Uso de recursos (se disponível)
        if job.resource_usage and job.resource_usage.gpu_usage > 0:
            content.append("─" * 55 + "\n", style="dim")
            content.append("  USO DE RECURSOS\n", style="bold")
            content.append("─" * 55 + "\n\n", style="dim")
            
            ru = job.resource_usage
            content.append(f"GPU: {ru.gpu_usage:.1f}%  ", style="cyan")
            content.append(f"VRAM: {ru.vram_usage:.1f}GB  ", style="magenta")
            content.append(f"CPU: {ru.cpu_usage:.1f}%  ", style="yellow")
            content.append(f"RAM: {ru.memory_usage:.1f}GB\n", style="green")
            
            content.append("\n")
        
        # Erro (se houver)
        if job.error_message:
            content.append("─" * 55 + "\n", style="dim red")
            content.append("  ERRO\n", style="bold red")
            content.append("─" * 55 + "\n\n", style="dim")
            
            content.append(f"{job.error_message}\n", style="red")
            content.append("\n")
        
        # Rodapé
        content.append("═" * 55 + "\n", style="bold yellow")
        
        self.console.print(Panel(content, border_style="yellow", title=f"[bold]Job {job.id[:8]}[/bold]"))
    
    def _show_statistics_panel(self):
        """Exibe painel com estatísticas da fila."""
        stats = self.queue_mgr.get_statistics()
        
        content = Text()
        
        # Título
        content.append("═" * 40 + "\n", style="bold magenta")
        content.append("  ESTATÍSTICAS DA FILA\n", style="bold magenta")
        content.append("═" * 40 + "\n\n", style="bold magenta")
        
        # Resumo
        content.append("Total de Jobs: ", style="cyan")
        content.append(f"{stats['total']}\n", style="bold white")
        
        content.append("Jobs Ativos: ", style="cyan")
        content.append(f"{stats['active']}/{stats['max_concurrent']}\n", style="bold green")
        
        status_label = "[yellow]PAUSADA[/yellow]" if stats['paused'] else "[green]ATIVA[/green]"
        content.append("Status da Fila: ", style="cyan")
        content.append(f"{status_label}\n\n")
        
        # Por status
        content.append("─" * 40 + "\n", style="dim")
        content.append("  POR STATUS\n", style="bold")
        content.append("─" * 40 + "\n\n", style="dim")
        
        by_status = stats['by_status']
        content.append(f"  Executando:  ", style="white")
        content.append(f"{by_status.get('running', 0)}\n", style="bold green")
        
        content.append(f"  Na Fila:     ", style="white")
        content.append(f"{by_status.get('queued', 0) + by_status.get('pending', 0)}\n", style="bold cyan")
        
        content.append(f"  Pausados:    ", style="white")
        content.append(f"{by_status.get('paused', 0)}\n", style="bold yellow")
        
        content.append(f"  Completos:   ", style="white")
        content.append(f"{by_status.get('completed', 0)}\n", style="bold green")
        
        content.append(f"  Falhados:    ", style="white")
        content.append(f"{by_status.get('failed', 0)}\n", style="bold red")
        
        content.append(f"  Cancelados:  ", style="white")
        content.append(f"{by_status.get('cancelled', 0)}\n\n", style="dim red")
        
        # Por prioridade
        content.append("─" * 40 + "\n", style="dim")
        content.append("  POR PRIORIDADE\n", style="bold")
        content.append("─" * 40 + "\n\n", style="dim")
        
        by_priority = stats['by_priority']
        content.append(f"  Critical:  ", style="white")
        content.append(f"{by_priority.get('critical', 0)}\n", style="bold red")
        
        content.append(f"  High:      ", style="white")
        content.append(f"{by_priority.get('high', 0)}\n", style="bold yellow")
        
        content.append(f"  Normal:    ", style="white")
        content.append(f"{by_priority.get('normal', 0)}\n", style="bold green")
        
        content.append(f"  Low:       ", style="white")
        content.append(f"{by_priority.get('low', 0)}\n\n", style="dim")
        
        # Taxa de sucesso
        content.append("─" * 40 + "\n", style="dim")
        content.append("  DESEMPENHO\n", style="bold")
        content.append("─" * 40 + "\n\n", style="dim")
        
        content.append(f"  Taxa de Sucesso: ", style="white")
        content.append(f"{stats['success_rate']:.1f}%\n", style="green")
        
        content.append(f"  Input Total:     ", style="white")
        content.append(f"{stats['total_input_size_gb']:.2f} GB\n", style="cyan")
        
        content.append(f"  Output Total:    ", style="white")
        content.append(f"{stats['total_output_size_gb']:.2f} GB\n", style="green")
        
        content.append("\n")
        content.append("═" * 40 + "\n", style="bold magenta")
        
        self.console.print(Panel(content, border_style="magenta", title="[bold]Estatísticas[/bold]"))
    
    # =========================================================================
    # MENUS DE GERENCIAMENTO
    # =========================================================================
    
    def _manage_individual_job_submenu(self):
        """Submenu para gerenciar job individual."""
        all_jobs = self.queue_mgr.list_queue()
        
        if not all_jobs:
            self.menu.print_info("Nenhum job encontrado")
            return
        
        # Filtrar jobs gerenciáveis (não completados)
        manageable = [
            j for j in all_jobs
            if j.status not in [JobStatus.COMPLETED.value, JobStatus.CANCELLED.value]
        ]
        
        if not manageable:
            self.menu.print_info("Nenhum job ativo para gerenciar")
            return
        
        self.menu.clear()
        self.menu.print_header("Gerenciar Job Individual")
        
        # Tabela de jobs disponíveis
        table = Table(title="Jobs Disponíveis", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Job ID", style="dim", width=10)
        table.add_column("Input", style="cyan")
        table.add_column("Status", style="white", width=15)
        table.add_column("Progresso", style="green", width=25)
        
        for i, job in enumerate(manageable, 1):
            table.add_row(
                str(i),
                job.id[:8],
                Path(job.input_path).name[:40],
                self._get_status_label(job.status),
                self._format_percentage(job.progress)
            )
        
        self.console.print(table)
        self.console.print()
        
        choice = self.menu.ask_int(
            "Número do job para gerenciar (0 para cancelar)",
            default=0
        )
        
        if choice == 0:
            return
        
        if 1 <= choice <= len(manageable):
            selected_job = manageable[choice - 1]
            self._show_job_management_options(selected_job)
        else:
            self.menu.print_error("Opção inválida")
            self.console.input("\nPressione Enter para continuar...")
    
    def _show_job_management_options(self, job: QueueJob):
        """Mostra opções de gerenciamento para um job específico."""
        self.menu.clear()
        self.menu.print_header(f"Gerenciar Job: {job.id[:8]}")
        
        # Exibir detalhes do job
        self._show_job_details_panel(job)
        
        # Opções de gerenciamento
        options = [
            {"description": "Cancelar job", "shortcut": "1"},
        ]
        
        if job.status == JobStatus.RUNNING.value:
            options.append({"description": "Pausar job", "shortcut": "2"})
        elif job.status == JobStatus.PAUSED.value:
            options.append({"description": "Retomar job", "shortcut": "2"})
        
        if job.status in [JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
            options.append({"description": "Retentar job", "shortcut": "3"})
        
        if job.status in [JobStatus.QUEUED.value, JobStatus.PENDING.value]:
            options.append({"description": "Alterar prioridade", "shortcut": "3"})
            options.append({"description": "Reordenar na fila", "shortcut": "4"})
        
        options.append({"description": "Voltar", "shortcut": str(len(options) + 1)})
        
        choice = self.menu.show_menu("Opções de Gerenciamento", options)
        
        if choice == 0:  # Cancelar
            self._cancel_job_confirmation(job.id)
        elif choice == 1:  # Pausar/Retomar
            if job.status == JobStatus.RUNNING.value:
                self._pause_job(job.id)
            elif job.status == JobStatus.PAUSED.value:
                self._resume_job(job.id)
        elif choice == 2:  # Retentar ou Alterar prioridade
            if job.status in [JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
                self._retry_job(job.id)
            elif job.status in [JobStatus.QUEUED.value, JobStatus.PENDING.value]:
                self._change_priority_submenu(job.id)
        elif choice == 3:  # Reordenar
            if job.status in [JobStatus.QUEUED.value, JobStatus.PENDING.value]:
                self._reorder_job_submenu(job.id)
    
    def _cancel_job_confirmation(self, job_id: str):
        """Confirmação para cancelar job."""
        job = self.queue_mgr.get_job(job_id)
        if not job:
            self.menu.print_error("Job não encontrado")
            return
        
        self.console.print()
        self.console.print("[bold red]⚠ ATENÇÃO: Cancelar este job?[/bold red]")
        self.console.print("[yellow]Esta operação não pode ser desfeita.[/yellow]")
        self.console.print()
        
        if self.menu.ask_confirm("Confirmar cancelamento?"):
            if self.queue_mgr.cancel_job(job_id):
                self.menu.print_success(f"Job {job_id[:8]} cancelado com sucesso")
            else:
                self.menu.print_error("Erro ao cancelar job")
        
        self.console.input("\nPressione Enter para continuar...")
    
    def _pause_job(self, job_id: str):
        """Pausa um job em execução."""
        if self.queue_mgr.pause_job(job_id):
            self.menu.print_success(f"Job {job_id[:8]} pausado com sucesso")
        else:
            self.menu.print_error("Erro ao pausar job")
        
        self.console.input("\nPressione Enter para continuar...")
    
    def _resume_job(self, job_id: str):
        """Retoma um job pausado."""
        if self.queue_mgr.resume_job(job_id):
            self.menu.print_success(f"Job {job_id[:8]} retomado com sucesso")
        else:
            self.menu.print_error("Erro ao retomar job - verifique se há slots disponíveis")
        
        self.console.input("\nPressione Enter para continuar...")
    
    def _retry_job(self, job_id: str):
        """Retenta um job falhado ou cancelado."""
        new_job_id = self.queue_mgr.retry_job(job_id)
        if new_job_id:
            self.menu.print_success(f"Job retentado com novo ID: {new_job_id[:8]}")
        else:
            self.menu.print_error("Não foi possível retentar este job")
        
        self.console.input("\nPressione Enter para continuar...")
    
    def _change_priority_submenu(self, job_id: str):
        """Submenu para alterar prioridade do job."""
        self.menu.clear()
        self.menu.print_header("Alterar Prioridade")
        
        job = self.queue_mgr.get_job(job_id)
        if not job:
            self.menu.print_error("Job não encontrado")
            return
        
        self.console.print(f"Job: {job.id[:8]} - {job.profile_name}")
        self.console.print(f"Prioridade atual: {self._get_priority_label(job.priority)}")
        self.console.print()
        
        options = [
            {"description": "LOW (Baixa)", "shortcut": "1"},
            {"description": "NORMAL (Normal)", "shortcut": "2"},
            {"description": "HIGH (Alta)", "shortcut": "3"},
            {"description": "CRITICAL (Crítica)", "shortcut": "4"}
        ]
        
        choice = self.menu.show_menu("Selecione a prioridade", options)
        
        if 0 <= choice <= 3:
            priority = QueuePriority(choice + 1)
            if self.queue_mgr.set_job_priority(job_id, priority):
                self.menu.print_success(f"Prioridade alterada para {priority.name}")
            else:
                self.menu.print_error("Erro ao alterar prioridade")
        
        self.console.input("\nPressione Enter para continuar...")
    
    def _reorder_job_submenu(self, job_id: str):
        """Submenu para reordenar job na fila."""
        self.menu.clear()
        self.menu.print_header("Reordenar Job na Fila")
        
        job = self.queue_mgr.get_job(job_id)
        if not job:
            self.menu.print_error("Job não encontrado")
            return
        
        # Mostrar posição atual
        queue = self.queue_mgr.list_queue()
        current_pos = next((i for i, j in enumerate(queue) if j.id == job_id), -1) + 1
        
        self.console.print(f"Job: {job.id[:8]} - {job.profile_name}")
        self.console.print(f"Posição atual: {current_pos}")
        self.console.print()
        
        new_pos = self.menu.ask_int(
            "Nova posição na fila (0 para cancelar)",
            default=0
        )
        
        if new_pos > 0:
            if self.queue_mgr.reorder_job(job_id, new_pos - 1):
                self.menu.print_success(f"Job movido para posição {new_pos}")
            else:
                self.menu.print_error("Erro ao reordenar job")
        
        self.console.input("\nPressione Enter para continuar...")
    
    # =========================================================================
    # MENU PRINCIPAL
    # =========================================================================
    
    def show_submenu(self):
        """Exibe submenu principal de gerenciamento de fila."""
        while True:
            self.menu.clear()
            self.menu.print_header("Gerenciador de Fila")
            
            # Obter jobs
            all_jobs = self.queue_mgr.list_queue()
            is_paused = self.queue_mgr.is_queue_paused()
            
            # Separar por status
            running = [j for j in all_jobs if j.status == JobStatus.RUNNING.value]
            pending = [j for j in all_jobs if j.status in [JobStatus.QUEUED.value, JobStatus.PENDING.value]]
            
            # Exibir resumo
            if running:
                self.console.print(f"[bold green]Jobs em execução: {len(running)}[/bold green]")
                for job in running[:3]:
                    self.console.print(f"  • {job.id[:8]}: {self._format_percentage(job.progress)}")
                if len(running) > 3:
                    self.console.print(f"  [dim]... e mais {len(running) - 3} jobs[/dim]")
                self.console.print()
            elif pending:
                self.console.print(f"[bold cyan]Jobs na fila: {len(pending)}[/bold cyan]")
                self.console.print()
            
            # Exibir tabela se houver jobs
            if all_jobs:
                self._show_queue_table(all_jobs)
                
                options = [
                    {"description": "Ver estatísticas", "shortcut": "1"},
                    {"description": "Pausar fila" if not is_paused else "Retomar fila", "shortcut": "2"},
                    {"description": "Limpar fila completa", "shortcut": "3"},
                    {"description": "Remover job específico", "shortcut": "4"},
                    {"description": "Gerenciar job individual", "shortcut": "5"},
                    {"description": "Processar fila agora", "shortcut": "6"},
                    {"description": "Voltar", "shortcut": "7"}
                ]
            else:
                self.menu.print_info("Fila vazia")
                options = [
                    {"description": "Voltar", "shortcut": "1"}
                ]
            
            choice = self.menu.show_menu("Menu", options)
            
            if choice == 0:  # Estatísticas
                self._show_statistics_panel()
                self.console.input("\nPressione Enter para continuar...")
            elif choice == 1:  # Pausar/Retomar fila
                if is_paused:
                    self.queue_mgr.resume_queue()
                    self.menu.print_success("Fila retomada")
                else:
                    self.queue_mgr.pause_queue()
                    self.menu.print_warning("Fila pausada")
                self.console.input("\nPressione Enter para continuar...")
            elif choice == 2:  # Limpar fila
                if self.menu.ask_confirm("Tem certeza que deseja limpar toda a fila?"):
                    count = self.queue_mgr.clear_queue()
                    self.menu.print_success(f"{count} job(s) removidos da fila")
                self.console.input("\nPressione Enter para continuar...")
            elif choice == 3:  # Remover job
                self._remove_job_submenu()
            elif choice == 4:  # Gerenciar job individual
                self._manage_individual_job_submenu()
            elif choice == 5:  # Processar fila
                self._process_queue_with_monitor()
            elif choice == 6:  # Voltar
                break
    
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
        table.add_column("Status", style="white", width=15)
        
        for i, job in enumerate(queue, 1):
            table.add_row(
                str(i),
                job.id[:8],
                Path(job.input_path).name[:40],
                job.profile_name[:20],
                self._get_status_label(job.status)
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
            
            if self.menu.ask_confirm(f"Confirmar remoção do job {job_to_remove.id[:8]}?"):
                if self.queue_mgr.remove_job(job_to_remove.id):
                    self.menu.print_success("Job removido da fila")
                else:
                    self.menu.print_error("Erro ao remover job")
        
        self.console.input("\nPressione Enter para continuar...")
    
    def _process_queue_with_monitor(self):
        """Processa fila com monitor em tempo real."""
        # Esta função será implementada na Fase 7
        self.menu.print_info("Processamento com monitor será implementado na próxima fase")
        self.console.input("\nPressione Enter para continuar...")


def show_queue_submenu_v2(console: Console, queue_mgr: UnifiedQueueManager):
    """Função helper para exibir submenu de fila v2."""
    ui = QueueMenuUIV2(console, queue_mgr)
    ui.show_submenu()
