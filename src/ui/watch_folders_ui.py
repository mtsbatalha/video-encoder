from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
from typing import List, Dict

from src.managers.config_manager import ConfigManager
from src.managers.profile_manager import ProfileManager
from src.ui.menu import Menu


class WatchFoldersUI:
    """Interface de usuário para gerenciamento de pastas watch."""
    
    def __init__(self, console: Console, config_manager: ConfigManager, profile_manager: ProfileManager):
        self.console = console
        self.config = config_manager
        self.profile_mgr = profile_manager
        self.menu = Menu(console)
    
    def show_submenu(self):
        """Alias para run() - mostra submenu de gerenciamento."""
        self.run()
    
    def run(self):
        """Loop principal do submenu."""
        while True:
            self.menu.clear()
            self.menu.print_header("Gerenciador de Pastas Watch")
            
            options = [
                {"description": "Listar pastas watch", "shortcut": "1"},
                {"description": "Adicionar nova pasta", "shortcut": "2"},
                {"description": "Remover pasta", "shortcut": "3"},
                {"description": "Editar pasta", "shortcut": "4"},
                {"description": "Testar configurações", "shortcut": "5"},
                {"description": "Voltar ao menu principal", "shortcut": "0"}
            ]
            
            choice = self.menu.show_menu("Menu", options)
            
            if choice == 0:
                self.list_watch_folders()
            elif choice == 1:
                self.add_watch_folder()
            elif choice == 2:
                self.remove_watch_folder()
            elif choice == 3:
                self.edit_watch_folder()
            elif choice == 4:
                self.test_watch_folders()
            elif choice == 5:
                break
    
    def _validate_folder_paths(self, entrada: str, saida: str) -> tuple:
        """Valida caminhos das pastas de entrada e saída."""
        entrada_path = Path(entrada)
        saida_path = Path(saida)
        
        if not entrada_path.exists():
            return (False, f"Pasta de entrada não existe: {entrada}")
        
        if not entrada_path.is_dir():
            return (False, f"Caminho de entrada não é uma pasta: {entrada}")
        
        try:
            saida_path.mkdir(parents=True, exist_ok=True)
            if not saida_path.exists():
                return (False, f"Não foi possível criar pasta de saída: {saida}")
        except PermissionError:
            return (False, f"Sem permissão para criar pasta de saída: {saida}")
        except Exception as e:
            return (False, f"Erro ao validar pasta de saída: {e}")
        
        return (True, "Caminhos válidos")
    
    def _get_profile_choices(self) -> List[Dict[str, str]]:
        """Retorna lista de perfis formatados para seleção."""
        profiles = self.profile_mgr.list_profiles()
        if not profiles:
            return []
        
        return [
            {"id": p["id"], "display": f"{p['name']} ({p['codec']})"}
            for p in profiles
        ]
    
    def list_watch_folders(self):
        """Lista todas as pastas watch configuradas."""
        self.menu.clear()
        self.menu.print_header("Pastas Watch Configuradas")
        
        folders = self.config.get_watch_folders()
        
        if not folders:
            self.menu.print_warning("Nenhuma pasta watch configurada")
            input("\nPressione Enter para continuar...")
            return
        
        table = Table(title="Pastas Watch", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Nome", style="cyan")
        table.add_column("Entrada", style="white")
        table.add_column("Saída", style="white")
        table.add_column("Perfil", style="green")
        table.add_column("Status", style="yellow")
        
        for i, folder in enumerate(folders, 1):
            entrada_path = Path(folder.get("entrada", ""))
            status = "[green]OK[/green]" if entrada_path.exists() else "[red]Pasta não existe[/red]"
            
            table.add_row(
                str(i),
                folder.get("nome", "N/A"),
                folder.get("entrada", "N/A"),
                folder.get("saida", "N/A"),
                folder.get("profile", "N/A"),
                status
            )
        
        self.menu.console.print(table)
        input("\nPressione Enter para continuar...")
    
    def add_watch_folder(self):
        """Adiciona nova pasta watch."""
        self.menu.clear()
        self.menu.print_header("Adicionar Nova Pasta Watch")
        
        profiles = self._get_profile_choices()
        if not profiles:
            self.menu.print_error("Nenhum perfil disponível. Crie um perfil primeiro.")
            input("\nPressione Enter para continuar...")
            return
        
        self.menu.print_info("Perfis disponíveis:")
        for i, p in enumerate(profiles, 1):
            self.menu.console.print(f"  [{i}] {p['display']}")
        self.menu.console.print()
        
        nome = self.menu.ask("Nome descritivo")
        if not nome or not nome.strip():
            self.menu.print_error("Nome não pode ser vazio")
            input("\nPressione Enter para continuar...")
            return
        
        entrada = self.menu.ask("Caminho da pasta de entrada")
        if not entrada or not entrada.strip():
            self.menu.print_error("Caminho de entrada não pode ser vazio")
            input("\nPressione Enter para continuar...")
            return
        
        saida = self.menu.ask("Caminho da pasta de saída")
        if not saida or not saida.strip():
            self.menu.print_error("Caminho de saída não pode ser vazio")
            input("\nPressione Enter para continuar...")
            return
        
        profile_idx = self.menu.ask_int(
            "Número do perfil",
            default=1
        )
        
        if profile_idx < 1 or profile_idx > len(profiles):
            self.menu.print_error("Número de perfil inválido")
            input("\nPressione Enter para continuar...")
            return
        
        profile_id = profiles[profile_idx - 1]["id"]
        
        valido, mensagem = self._validate_folder_paths(entrada, saida)
        if not valido:
            self.menu.print_warning(mensagem)
            continuar = self.menu.ask_confirm("Deseja continuar mesmo assim?", default=False)
            if not continuar:
                input("\nPressione Enter para continuar...")
                return
        
        self.menu.console.print()
        self.menu.console.print(Panel(
            f"[bold]Confirmação:[/bold]\n\n"
            f"Nome: {nome}\n"
            f"Entrada: {entrada}\n"
            f"Saída: {saida}\n"
            f"Perfil: {profile_id}",
            border_style="cyan",
            title="Resumo"
        ))
        
        if not self.menu.ask_confirm("Adicionar pasta?", default=False):
            self.menu.print_warning("Operação cancelada")
            input("\nPressione Enter para continuar...")
            return
        
        folder_data = {
            "nome": nome.strip(),
            "entrada": entrada.strip(),
            "saida": saida.strip(),
            "profile": profile_id,
            "enabled": True
        }
        
        if self.config.add_watch_folder(folder_data):
            self.menu.print_success("Pasta watch adicionada com sucesso")
        else:
            self.menu.print_error("Erro ao adicionar pasta watch")
        
        input("\nPressione Enter para continuar...")
    
    def remove_watch_folder(self):
        """Remove pasta watch por índice."""
        self.menu.clear()
        self.menu.print_header("Remover Pasta Watch")
        
        folders = self.config.get_watch_folders()
        
        if not folders:
            self.menu.print_warning("Nenhuma pasta watch configurada")
            input("\nPressione Enter para continuar...")
            return
        
        table = Table(title="Pastas Watch", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Nome", style="cyan")
        table.add_column("Entrada", style="white")
        table.add_column("Saída", style="white")
        table.add_column("Perfil", style="green")
        
        for i, folder in enumerate(folders, 1):
            table.add_row(
                str(i),
                folder.get("nome", "N/A"),
                folder.get("entrada", "N/A"),
                folder.get("saida", "N/A"),
                folder.get("profile", "N/A")
            )
        
        self.menu.console.print(table)
        
        idx = self.menu.ask_int(
            "Número da pasta para remover",
            default=0
        )
        
        if idx < 1 or idx > len(folders):
            self.menu.print_error("Número inválido")
            input("\nPressione Enter para continuar...")
            return
        
        folder_name = folders[idx - 1].get("nome", "Desconhecida")
        
        if not self.menu.ask_confirm(f"Remover pasta '{folder_name}'?", default=False):
            self.menu.print_warning("Operação cancelada")
            input("\nPressione Enter para continuar...")
            return
        
        if self.config.remove_watch_folder(idx - 1):
            self.menu.print_success(f"Pasta '{folder_name}' removida com sucesso")
        else:
            self.menu.print_error("Erro ao remover pasta watch")
        
        input("\nPressione Enter para continuar...")
    
    def edit_watch_folder(self):
        """Edita pasta watch existente."""
        self.menu.clear()
        self.menu.print_header("Editar Pasta Watch")
        
        folders = self.config.get_watch_folders()
        
        if not folders:
            self.menu.print_warning("Nenhuma pasta watch configurada")
            input("\nPressione Enter para continuar...")
            return
        
        table = Table(title="Pastas Watch", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Nome", style="cyan")
        table.add_column("Entrada", style="white")
        table.add_column("Saída", style="white")
        table.add_column("Perfil", style="green")
        
        for i, folder in enumerate(folders, 1):
            table.add_row(
                str(i),
                folder.get("nome", "N/A"),
                folder.get("entrada", "N/A"),
                folder.get("saida", "N/A"),
                folder.get("profile", "N/A")
            )
        
        self.menu.console.print(table)
        
        idx = self.menu.ask_int(
            "Número da pasta para editar",
            default=0
        )
        
        if idx < 1 or idx > len(folders):
            self.menu.print_error("Número inválido")
            input("\nPressione Enter para continuar...")
            return
        
        folder = folders[idx - 1]
        profiles = self._get_profile_choices()
        
        if not profiles:
            self.menu.print_error("Nenhum perfil disponível. Crie um perfil primeiro.")
            input("\nPressione Enter para continuar...")
            return
        
        self.menu.console.print("\n[bold]Valores atuais entre colchetes. Pressione Enter para manter.[/bold]\n")
        
        nome_atual = folder.get("nome", "")
        nome = self.menu.ask(f"Nome descritivo [{nome_atual}]", default="")
        if not nome:
            nome = nome_atual
        
        entrada_atual = folder.get("entrada", "")
        entrada = self.menu.ask(f"Pasta de entrada [{entrada_atual}]", default="")
        if not entrada:
            entrada = entrada_atual
        
        saida_atual = folder.get("saida", "")
        saida = self.menu.ask(f"Pasta de saída [{saida_atual}]", default="")
        if not saida:
            saida = saida_atual
        
        self.menu.print_info("Perfis disponíveis:")
        for i, p in enumerate(profiles, 1):
            current_marker = " (atual)" if p["id"] == folder.get("profile", "") else ""
            self.menu.console.print(f"  [{i}] {p['display']}{current_marker}")
        
        profile_input = self.menu.ask("Número do perfil", default="")
        if profile_input:
            try:
                profile_idx = int(profile_input)
                if 1 <= profile_idx <= len(profiles):
                    profile_id = profiles[profile_idx - 1]["id"]
                else:
                    profile_id = folder.get("profile", "")
                    self.menu.print_warning("Número inválido, mantendo perfil atual")
            except ValueError:
                profile_id = folder.get("profile", "")
                self.menu.print_warning("Entrada inválida, mantendo perfil atual")
        else:
            profile_id = folder.get("profile", "")
        
        valido, mensagem = self._validate_folder_paths(entrada, saida)
        if not valido:
            self.menu.print_warning(mensagem)
            continuar = self.menu.ask_confirm("Deseja continuar mesmo assim?", default=False)
            if not continuar:
                input("\nPressione Enter para continuar...")
                return
        
        self.menu.console.print()
        self.menu.console.print(Panel(
            f"[bold]Alterações:[/bold]\n\n"
            f"Nome: {nome}\n"
            f"Entrada: {entrada}\n"
            f"Saída: {saida}\n"
            f"Perfil: {profile_id}",
            border_style="cyan",
            title="Resumo"
        ))
        
        if not self.menu.ask_confirm("Salvar alterações?", default=False):
            self.menu.print_warning("Operação cancelada")
            input("\nPressione Enter para continuar...")
            return
        
        folder_data = {
            "nome": nome.strip(),
            "entrada": entrada.strip(),
            "saida": saida.strip(),
            "profile": profile_id,
            "enabled": folder.get("enabled", True)
        }
        
        folders[idx - 1] = folder_data
        self.config.set("directories.watch_folders", folders)
        
        if self.config.save():
            self.menu.print_success("Pasta watch atualizada com sucesso")
        else:
            self.menu.print_error("Erro ao atualizar pasta watch")
        
        input("\nPressione Enter para continuar...")
    
    def test_watch_folders(self):
        """Testa e valida todas as pastas watch configuradas."""
        self.menu.clear()
        self.menu.print_header("Testar Configurações das Pastas Watch")
        
        folders = self.config.get_watch_folders()
        
        if not folders:
            self.menu.print_warning("Nenhuma pasta watch configurada")
            input("\nPressione Enter para continuar...")
            return
        
        profiles = self.profile_mgr.list_profiles()
        profile_ids = {p["id"] for p in profiles}
        
        results = []
        
        for folder in folders:
            result = {
                "nome": folder.get("nome", "N/A"),
                "entrada_ok": False,
                "saida_ok": False,
                "perfil_ok": False,
                "mensagens": []
            }
            
            entrada_path = Path(folder.get("entrada", ""))
            if entrada_path.exists():
                result["entrada_ok"] = True
                result["mensagens"].append("Entrada: OK")
            else:
                result["mensagens"].append("[red]Entrada: Não existe[/red]")
            
            saida_path = Path(folder.get("saida", ""))
            try:
                saida_path.mkdir(parents=True, exist_ok=True)
                if saida_path.exists():
                    result["saida_ok"] = True
                    result["mensagens"].append("Saída: OK")
                else:
                    result["mensagens"].append("[red]Saída: Não foi possível criar[/red]")
            except PermissionError:
                result["mensagens"].append("[red]Saída: Sem permissão[/red]")
            except Exception as e:
                result["mensagens"].append(f"[red]Saída: Erro - {e}[/red]")
            
            profile_id = folder.get("profile", "")
            if profile_id in profile_ids:
                result["perfil_ok"] = True
                result["mensagens"].append(f"Perfil: OK ({profile_id})")
            else:
                result["mensagens"].append(f"[red]Perfil: '{profile_id}' não encontrado[/red]")
            
            results.append(result)
        
        table = Table(title="Resultado dos Testes", show_header=True, header_style="bold magenta")
        table.add_column("Nome", style="cyan")
        table.add_column("Entrada", style="green")
        table.add_column("Saída", style="green")
        table.add_column("Perfil", style="green")
        table.add_column("Status", style="yellow")
        
        for result in results:
            entrada_status = "[green]OK[/green]" if result["entrada_ok"] else "[red]FALHA[/red]"
            saida_status = "[green]OK[/green]" if result["saida_ok"] else "[red]FALHA[/red]"
            perfil_status = "[green]OK[/green]" if result["perfil_ok"] else "[red]FALHA[/red]"
            
            all_ok = result["entrada_ok"] and result["saida_ok"] and result["perfil_ok"]
            status = "[green]VÁLIDA[/green]" if all_ok else "[red]PROBLEMAS[/red]"
            
            table.add_row(
                result["nome"],
                entrada_status,
                saida_status,
                perfil_status,
                status
            )
        
        self.menu.console.print(table)
        
        self.menu.console.print("\n[bold]Detalhes:[/bold]")
        for result in results:
            self.menu.console.print(f"\n[cyan]{result['nome']}:[/cyan]")
            for msg in result["mensagens"]:
                self.menu.console.print(f"  {msg}")
        
        input("\nPressione Enter para continuar...")
