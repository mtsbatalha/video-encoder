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
    
    def show_hardware_detection_panel(self, hw_info: Dict[str, Any]):
        """Exibe painel de detecção de hardware."""
        content = Text()
        
        content.append("[HW] Detecção de Hardware\n\n", style="bold magenta")
        
        if hw_info.get('gpus'):
            for gpu in hw_info['gpus']:
                content.append(f"• {gpu['name']}\n", style="bold green")
                content.append(f"  Categoria: {gpu['category']}\n", style="dim")
                content.append(f"  VRAM: {gpu['vram_gb']}GB\n", style="dim")
                content.append(f"  Codecs: {', '.join(gpu['codec_support'])}\n\n", style="cyan")
        else:
            content.append("Nenhuma GPU dedicada detectada\n", style="yellow")
        
        content.append(f"\nCPU Disponível: {'Sim' if hw_info.get('cpu_available') else 'Não'}\n", style="blue")
        
        content.append(f"\nResumo:\n", style="bold magenta")
        nvidia_color = "green" if hw_info.get('nvidia_detected') else "red"
        content.append(f"  NVIDIA GPU: ", style="white")
        content.append(f"{'Detectada' if hw_info.get('nvidia_detected') else 'Não detectada'}\n", style=nvidia_color)
        
        amd_color = "green" if hw_info.get('amd_gpu_detected') else "dim"
        content.append(f"  AMD GPU: ", style="white")
        content.append(f"{'Detectada' if hw_info.get('amd_gpu_detected') else 'Não detectada'}\n", style=amd_color)
        
        intel_color = "green" if hw_info.get('intel_igpu_detected') else "dim"
        content.append(f"  Intel iGPU: ", style="white")
        content.append(f"{'Detectada' if hw_info.get('intel_igpu_detected') else 'Não detectada'}\n", style=intel_color)
        
        self.console.print(Panel(content, border_style="magenta", title="Detecção de Hardware"))
    
    def show_hardware_categories_menu(self) -> int:
        """Exibe menu de categorias de hardware e retorna escolha."""
        self.print_header("Perfis por Hardware")
        self.console.print()
        
        table = Table(show_header=False, box=None)
        table.add_column("#", style="bold green", width=4)
        table.add_column("Categoria", style="white")
        table.add_column("Codecs", style="cyan")
        
        categories = [
            ("NVIDIA GPU", "hevc_nvenc, h264_nvenc, av1_nvenc"),
            ("AMD GPU", "hevc_amf, h264_amf"),
            ("Intel iGPU", "hevc_qsv, h264_qsv"),
            ("AMD iGPU", "hevc_amf, h264_amf"),
            ("CPU Qualidade", "libx265, libx264"),
            ("CPU Rápido", "libx265, libx264")
        ]
        
        for i, (cat, codecs) in enumerate(categories, 1):
            table.add_row(str(i), cat, codecs)
        
        self.console.print(table)
        self.console.print()
        
        max_option = len(categories)
        choice = IntPrompt.ask(
            "Escolha categoria de hardware",
            choices=[str(i) for i in range(1, max_option + 1)]
        )
        
        return choice - 1
    
    def show_directory_summary(self, directory: str, video_files: List[str]):
        """Exibe sumário visual da estrutura de diretórios e arquivos de vídeo."""
        from pathlib import Path
        from rich.tree import Tree
        from collections import defaultdict
        
        if not video_files:
            self.print_warning("Nenhum vídeo encontrado no diretório")
            return
        
        # Agrupar arquivos por diretório
        dir_structure: Dict[str, List[str]] = defaultdict(list)
        base_path = Path(directory)
        
        for video_file in video_files:
            video_path = Path(video_file)
            try:
                rel_path = video_path.relative_to(base_path)
                parent_dir = str(rel_path.parent)
                dir_structure[parent_dir].append({
                    'full_path': video_file,
                    'filename': video_path.name,
                    'rel_path': str(rel_path)
                })
            except ValueError:
                # Arquivo fora do diretório base
                dir_structure['.'].append({
                    'full_path': video_file,
                    'filename': video_path.name,
                    'rel_path': video_path.name
                })
        
        # Calcular estatísticas
        total_dirs = len([d for d in dir_structure.keys() if d != '.'])
        total_files = len(video_files)
        
        self.console.print()
        self.console.print(Panel(
            f"[bold cyan]📁 Diretórios:[/bold cyan] [white]{total_dirs}[/white]  |  "
            f"[bold green]🎬 Arquivos de vídeo:[/bold green] [white]{total_files}[/white]",
            border_style="cyan",
            title="📊 Sumário do Diretório"
        ))
        self.console.print()
        
        # Criar árvore de diretórios
        tree = Tree(f"📂 {directory}", style="bold magenta")
        
        # Ordenar diretórios (raiz primeiro, depois alfabeticamente)
        sorted_dirs = sorted(dir_structure.keys(), key=lambda x: '' if x == '.' else x)
        
        for dir_name in sorted_dirs:
            files = dir_structure[dir_name]
            
            if dir_name == '.':
                # Arquivos na raiz
                for file_info in files:
                    tree.add(f"🎬 {file_info['filename']}", style="green")
            else:
                # Subdiretórios
                dir_branch = tree.add(f"📁 {dir_name}", style="bold blue")
                for file_info in sorted(files, key=lambda x: x['filename']):
                    dir_branch.add(f"🎬 {file_info['filename']}", style="green")
        
        self.console.print(tree)
        self.console.print()
    
    def show_pre_conversion_summary(
        self,
        input_folder: str,
        output_folder: str,
        video_files: List[str],
        profile: Dict[str, Any]
    ):
        """Exibe sumário completo antes da conversão com opções de ação."""
        from pathlib import Path
        from rich.panel import Panel
        from rich.text import Text
        
        self.console.print()
        
        # Painel de informações da conversão
        info = Text()
        info.append("📁 Pasta de Entrada: ", style="cyan")
        info.append(f"{input_folder}\n", style="white")
        info.append("💾 Pasta de Saída: ", style="cyan")
        info.append(f"{output_folder}\n\n", style="white")
        info.append("🎬 Perfil Selecionado:\n", style="bold magenta")
        info.append(f"  Nome: ", style="cyan")
        info.append(f"{profile.get('name', 'Custom')}\n", style="white")
        info.append(f"  Codec: ", style="cyan")
        info.append(f"{profile.get('codec', 'hevc_nvenc')}\n", style="white")
        if profile.get('cq'):
            info.append(f"  CQ: ", style="cyan")
            info.append(f"{profile.get('cq')}\n", style="yellow")
        if profile.get('preset'):
            info.append(f"  Preset: ", style="cyan")
            info.append(f"{profile.get('preset')}\n", style="white")
        if profile.get('resolution'):
            info.append(f"  Resolução: ", style="cyan")
            info.append(f"{profile.get('resolution')}\n", style="blue")
        
        self.console.print(Panel(info, border_style="magenta", title="⚙️ Configurações da Conversão"))
        self.console.print()
        
        # Exibir sumário de diretórios
        self.show_directory_summary(input_folder, video_files)
        
        # Menu de opções
        self.console.print()
        self.console.print("[bold]O que deseja fazer?[/bold]\n")
        
        options = [
            {"description": "🚀 Iniciar conversão agora", "shortcut": "1"},
            {"description": "📋 Adicionar à fila", "shortcut": "2"},
            {"description": "⚙️ Configurações avançadas", "shortcut": "3"},
            {"description": "⏮ Voltar", "shortcut": "4"}
        ]
        
        choice = self.show_menu("Opções de Conversão", options)
        return choice
    
    def show_advanced_profile_editor(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Exibe editor de perfil para configurações avançadas antes da conversão."""
        self.console.print()
        self.print_header("⚙️ Configurações Avançadas", "Editar perfil antes da conversão")
        
        self.console.print("\n[bold cyan]Perfil atual:[/bold cyan]\n")
        
        # Exibir configurações atuais
        info = Text()
        info.append(f"Nome: ", style="cyan")
        info.append(f"{profile.get('name', 'Custom')}\n", style="white")
        info.append(f"Codec: ", style="cyan")
        info.append(f"{profile.get('codec', 'hevc_nvenc')}\n", style="white")
        info.append(f"CQ: ", style="cyan")
        info.append(f"{profile.get('cq', 'auto')}\n", style="yellow")
        info.append(f"Preset: ", style="cyan")
        info.append(f"{profile.get('preset', 'p5')}\n", style="white")
        info.append(f"Resolução: ", style="cyan")
        info.append(f"{profile.get('resolution', 'original')}\n", style="blue")
        info.append(f"Two-Pass: ", style="cyan")
        info.append(f"{'Sim' if profile.get('two_pass') else 'Não'}\n", style="green" if profile.get('two_pass') else "dim")
        info.append(f"HDR para SDR: ", style="cyan")
        info.append(f"{'Sim' if profile.get('hdr_to_sdr') else 'Não'}\n", style="green" if profile.get('hdr_to_sdr') else "dim")
        info.append(f"Deinterlace: ", style="cyan")
        info.append(f"{'Sim' if profile.get('deinterlace') else 'Não'}\n", style="green" if profile.get('deinterlace') else "dim")
        info.append(f"Bitrate: ", style="cyan")
        info.append(f"{profile.get('bitrate', '10M')}\n", style="yellow")
        
        self.console.print(Panel(info, border_style="cyan", title="Configurações Atuais"))
        
        # Menu de edição
        while True:
            self.console.print("\n[bold]O que deseja editar?[/bold]\n")
            
            edit_options = [
                {"description": f"Codec: [white]{profile.get('codec', 'hevc_nvenc')}[/white]", "shortcut": "1"},
                {"description": f"CQ: [yellow]{profile.get('cq', 'auto')}[/yellow]", "shortcut": "2"},
                {"description": f"Preset: [white]{profile.get('preset', 'p5')}[/white]", "shortcut": "3"},
                {"description": f"Resolução: [blue]{profile.get('resolution', 'original')}[/blue]", "shortcut": "4"},
                {"description": f"Two-Pass: [{'green' if profile.get('two_pass') else 'dim'}]{'Sim' if profile.get('two_pass') else 'Não'}[/{'green' if profile.get('two_pass') else 'dim'}]", "shortcut": "5"},
                {"description": f"HDR para SDR: [{'green' if profile.get('hdr_to_sdr') else 'dim'}]{'Sim' if profile.get('hdr_to_sdr') else 'Não'}[/{'green' if profile.get('hdr_to_sdr') else 'dim'}]", "shortcut": "6"},
                {"description": f"Deinterlace: [{'green' if profile.get('deinterlace') else 'dim'}]{'Sim' if profile.get('deinterlace') else 'Não'}[/{'green' if profile.get('deinterlace') else 'dim'}]", "shortcut": "7"},
                {"description": f"Bitrate: [yellow]{profile.get('bitrate', '10M')}[/yellow]", "shortcut": "8"},
                {"description": "✅ Concluir e voltar", "shortcut": "9"},
                {"description": "❌ Cancelar edições", "shortcut": "10"}
            ]
            
            choice = self.show_menu("Editar Configurações", edit_options)
            
            if choice == 0:  # Codec
                codec_options = ["hevc_nvenc", "h264_nvenc", "av1_nvenc", "hevc_qsv", "h264_qsv", "hevc_amf", "h264_amf", "libx265", "libx264"]
                codec_idx = self.show_options(codec_options, "Selecione o codec")
                profile['codec'] = codec_options[codec_idx]
            
            elif choice == 1:  # CQ
                new_cq = self.ask("Novo valor CQ (1-51, ou vazio para bitrate)", default=profile.get('cq', ''))
                if new_cq:
                    profile['cq'] = new_cq
                    profile['bitrate'] = None  # Limpa bitrate quando CQ é definido
                    self.print_success(f"CQ atualizado para: {new_cq} (bitrate desativado)")
                else:
                    profile['cq'] = None
                    bitrate = self.ask("Bitrate (ex: 10M, 5000K)", default=profile.get('bitrate', '10M'))
                    profile['bitrate'] = bitrate
                    self.print_success(f"Bitrate atualizado para: {bitrate} (CQ desativado)")
            
            elif choice == 2:  # Preset
                preset_options = ["p1", "p2", "p3", "p4", "p5", "p6", "p7"]
                preset_idx = self.show_options(preset_options, "Selecione o preset")
                profile['preset'] = preset_options[preset_idx]
            
            elif choice == 3:  # Resolução
                resolution_options = ["", "480", "720", "1080", "1440", "2160"]
                resolution_labels = ["Original", "480p", "720p", "1080p", "1440p (2K)", "2160p (4K)"]
                resolution_idx = self.show_options(resolution_labels, "Selecione a resolução")
                profile['resolution'] = resolution_options[resolution_idx] if resolution_idx > 0 else None
            
            elif choice == 4:  # Two-Pass
                profile['two_pass'] = not profile.get('two_pass', False)
                self.print_success(f"Two-Pass: {'Ativado' if profile['two_pass'] else 'Desativado'}")
            
            elif choice == 5:  # HDR para SDR
                profile['hdr_to_sdr'] = not profile.get('hdr_to_sdr', False)
                self.print_success(f"HDR para SDR: {'Ativado' if profile['hdr_to_sdr'] else 'Desativado'}")
            
            elif choice == 6:  # Deinterlace
                profile['deinterlace'] = not profile.get('deinterlace', False)
                self.print_success(f"Deinterlace: {'Ativado' if profile['deinterlace'] else 'Desativado'}")
            
            elif choice == 7:  # Bitrate
                bitrate = self.ask("Bitrate (ex: 10M, 5000K)", default=profile.get('bitrate', '10M'))
                profile['bitrate'] = bitrate
                profile['cq'] = None  # Limpa CQ quando bitrate é definido
                self.print_success(f"Bitrate atualizado para: {bitrate} (CQ desativado)")
            
            elif choice == 8:  # Concluir
                self.print_success("Configurações atualizadas!")
                return profile
            
            elif choice == 9:  # Cancelar
                self.print_warning("Edições canceladas")
                return profile
        
        return profile
