from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.text import Text
from typing import Optional, List, Dict, Any


class Menu:
    """Menu interativo com Rich."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def clear(self):
        """Limpa tela."""
        self.console.clear()
    
    def print_header(self, title: str, subtitle: str = ""):
        """Exibe cabeçalho."""
        header = Text()
        header.append(title, style="bold magenta")
        if subtitle:
            header.append(f"\n{subtitle}", style="dim")
        
        self.console.print(Panel(header, border_style="magenta"))
    
    def print_success(self, message: str):
        """Exibe mensagem de sucesso."""
        self.console.print(f"[green][OK][/green] {message}")
    
    def print_error(self, message: str):
        """Exibe mensagem de erro."""
        self.console.print(f"[red][X][/red] {message}")
    
    def print_warning(self, message: str):
        """Exibe mensagem de aviso."""
        self.console.print(f"[yellow][!][/yellow] {message}")
    
    def print_info(self, message: str):
        """Exibe informação."""
        self.console.print(f"[cyan][i][/cyan] {message}")
    
    def ask(self, question: str, default: Optional[str] = None) -> str:
        """Faz pergunta e retorna resposta."""
        return Prompt.ask(question, default=default) if default else Prompt.ask(question)
    
    def ask_int(self, question: str, default: Optional[int] = None) -> int:
        """Faz pergunta numérica."""
        return IntPrompt.ask(question, default=default) if default else IntPrompt.ask(question)
    
    def ask_confirm(self, question: str, default: bool = False) -> bool:
        """Faz pergunta de confirmação."""
        return Confirm.ask(question, default=default)
    
    def show_options(self, options: List[str], title: str = "Opções") -> int:
        """Exibe lista de opções e retorna índice escolhido."""
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Opção", style="white")
        
        for i, option in enumerate(options, 1):
            table.add_row(str(i), option)
        
        self.console.print(table)
        
        max_option = len(options)
        choice = IntPrompt.ask(
            "Escolha uma opção",
            choices=[str(i) for i in range(1, max_option + 1)],
            default=1
        )
        
        return choice - 1
    
    def show_menu(self, title: str, options: List[Dict[str, Any]]) -> int:
        """Exibe menu e retorna índice da opção escolhida."""
        self.print_header(title)
        self.console.print()
        
        table = Table(show_header=False, box=None)
        table.add_column("#", style="bold green", width=4)
        table.add_column("Descrição", style="white")
        
        for i, option in enumerate(options, 1):
            desc = option.get('description', '')
            shortcut = option.get('shortcut', '')
            if shortcut:
                desc = f"[{shortcut}] {desc}"
            table.add_row(str(i), desc)
        
        self.console.print(table)
        self.console.print()
        
        max_option = len(options)
        choice = IntPrompt.ask(
            "Escolha uma opção",
            choices=[str(i) for i in range(1, max_option + 1)]
        )
        
        return choice - 1
    
    def show_profiles_table(self, profiles: List[Dict[str, Any]]):
        """Exibe tabela de perfis."""
        if not profiles:
            self.print_warning("Nenhum perfil encontrado")
            return
        
        table = Table(title="Perfis de Encoding", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=8)
        table.add_column("Nome", style="cyan")
        table.add_column("Codec", style="green")
        table.add_column("CQ", style="yellow")
        table.add_column("Resolução", style="blue")
        table.add_column("Descrição", style="dim")
        
        for profile in profiles:
            table.add_row(
                profile.get('id', '')[:8],
                profile.get('name', ''),
                profile.get('codec', ''),
                profile.get('cq', '-') or '-',
                profile.get('resolution', '-') or '-',
                profile.get('description', '')
            )
        
        self.console.print(table)
    
    def show_jobs_table(self, jobs: List[Dict[str, Any]]):
        """Exibe tabela de jobs."""
        if not jobs:
            self.print_warning("Nenhum job encontrado")
            return
        
        table = Table(title="Jobs", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=8)
        table.add_column("Input", style="cyan")
        table.add_column("Perfil", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Progresso", style="blue")
        table.add_column("Erro", style="red")
        
        status_icons = {
            'pending': '[WAIT]',
            'running': '[RUN]',
            'completed': '[OK]',
            'failed': '[X]',
            'cancelled': '[STOP]',
            'paused': '[PAUSE]'
        }
        
        for job in jobs:
            status = job.get('status', 'unknown')
            icon = status_icons.get(status, '')
            status_text = f"{icon} {status}"
            
            progress = job.get('progress', 0)
            progress_bar = f"{progress:.1f}%"
            
            table.add_row(
                job.get('id', '')[:8],
                job.get('input_path', '')[:30],
                job.get('profile_name', ''),
                status_text,
                progress_bar,
                job.get('error_message', '')[:20] or '-'
            )
        
        self.console.print(table)
    
    def show_stats_panel(self, stats: Dict[str, Any]):
        """Exibe painel de estatísticas."""
        content = Text()
        
        content.append("[STATS] Estatísticas Gerais\n\n", style="bold magenta")
        content.append("Total de Encodes: ", style="cyan")
        content.append(f"{stats.get('total_encodes', 0)}\n", style="white")
        
        content.append("Sucesso: ", style="green")
        content.append(f"{stats.get('successful_encodes', 0)} ")
        content.append(f"({stats.get('success_rate', 0)}%)\n", style="white")
        
        content.append("Falhas: ", style="red")
        content.append(f"{stats.get('failed_encodes', 0)}\n\n", style="white")
        
        content.append("Duração Total: ", style="cyan")
        content.append(f"{stats.get('total_duration_hours', 0)} horas\n", style="white")
        
        content.append("Tamanho Input: ", style="cyan")
        content.append(f"{stats.get('total_input_size_gb', 0)} GB\n", style="white")
        
        content.append("Tamanho Output: ", style="cyan")
        content.append(f"{stats.get('total_output_size_gb', 0)} GB\n", style="white")
        
        content.append("Razão de Compressão: ", style="cyan")
        content.append(f"{stats.get('compression_ratio', 0):.2f}x\n", style="white")
        
        self.console.print(Panel(content, border_style="magenta", title="Estatísticas"))
    
    def show_hardware_panel(self, hw_stats: Dict[str, Any]):
        """Exibe painel de hardware."""
        content = Text()
        
        gpu_util = hw_stats.get('gpu_util', 0)
        gpu_temp = hw_stats.get('gpu_temperature', 0)
        gpu_mem = hw_stats.get('gpu_memory_used', 0)
        cpu_util = hw_stats.get('cpu_util', 0)
        
        content.append("[HW] Hardware\n\n", style="bold cyan")
        
        gpu_bar = '█' * int(gpu_util / 10) + '░' * (10 - int(gpu_util / 10))
        content.append("GPU: ", style="green")
        content.append(f"{gpu_bar} {gpu_util}%\n", style="white")
        
        temp_color = "red" if gpu_temp > 80 else "yellow" if gpu_temp > 60 else "green"
        content.append("Temp GPU: ", style="green")
        content.append(f"{gpu_temp}°C\n", style=temp_color)
        
        content.append("Memória GPU: ", style="green")
        content.append(f"{gpu_mem} MB\n", style="white")
        
        cpu_bar = '█' * int(cpu_util / 10) + '░' * (10 - int(cpu_util / 10))
        content.append("CPU: ", style="blue")
        content.append(f"{cpu_bar} {cpu_util}%\n", style="white")
        
        self.console.print(Panel(content, border_style="cyan", title="Hardware Monitor"))
