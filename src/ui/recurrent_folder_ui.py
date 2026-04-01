from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.managers.config_manager import ConfigManager
from src.managers.recurrent_folder_manager import RecurrentFolderManager
from src.managers.profile_manager import ProfileManager
from src.managers.recurrent_history_manager import RecurrentHistoryManager
from src.services.recurrent_monitor_service import RecurrentMonitorService
from src.core.encoder_engine import EncoderEngine
from src.ui.menu import Menu
from src.ui.validators import Validators


class RecurrentFolderUI:
    """Interface de usuário para gerenciamento de pastas recorrentes."""

    def __init__(
        self,
        console: Console,
        config_manager: ConfigManager,
        profile_manager: Optional[ProfileManager] = None,
        history_manager: Optional[RecurrentHistoryManager] = None,
        queue_manager: Any = None,
        job_manager: Any = None,
    ):
        """
        Inicializa a interface de usuário para pastas recorrentes.

        Args:
            console: Instância do Console Rich
            config_manager: Instância do ConfigManager para persistência
            profile_manager: Instância opcional do ProfileManager para validação de perfis
            history_manager: Instância opcional do RecurrentHistoryManager para histórico
            queue_manager: Gerenciador de fila para processar jobs
            job_manager: Gerenciador de jobs
        """
        self.console = console
        self.config = config_manager
        self.profile_mgr = profile_manager or ProfileManager()
        self.folder_manager = RecurrentFolderManager(config_manager, self.profile_mgr)
        self.history_manager = history_manager or RecurrentHistoryManager()
        self.menu = Menu(console)
        self.queue_manager = queue_manager
        self.job_manager = job_manager
        self._monitor_service = None
        self._encoder = None

    def show_submenu(self):
        """Alias para run() - mostra submenu de gerenciamento."""
        self.run()

    def run(self):
        """Loop principal do submenu de gerenciamento de pastas recorrentes."""
        while True:
            self.menu.clear()
            self.menu.print_header(
                "Gerenciador de Pastas Recorrentes",
                "Monitoramento contínuo de diretórios",
            )

            options = [
                {"description": "Listar pastas recorrentes", "shortcut": "1"},
                {"description": "Adicionar nova pasta recorrente", "shortcut": "2"},
                {"description": "Remover pasta recorrente", "shortcut": "3"},
                {"description": "Editar pasta recorrente", "shortcut": "4"},
                {"description": "Ativar/Desativar pasta", "shortcut": "5"},
                {"description": "Iniciar/Parar monitores", "shortcut": "6"},
                {"description": "Ver histórico de processamento", "shortcut": "7"},
                {"description": "Voltar ao menu principal", "shortcut": "0"},
            ]

            choice = self.menu.show_menu("Menu", options)

            if choice == 0:
                self.list_recurrent_folders()
            elif choice == 1:
                self.add_recurrent_folder()
            elif choice == 2:
                self.remove_recurrent_folder()
            elif choice == 3:
                self.edit_recurrent_folder()
            elif choice == 4:
                self.toggle_enable_folder()
            elif choice == 5:
                self.start_stop_monitors()
            elif choice == 6:
                self.view_history()
            elif choice == 7:
                break

    def _get_profile_choices(self) -> List[Dict[str, str]]:
        """Retorna lista de perfis formatados para seleção."""
        profiles = self.profile_mgr.list_profiles()
        if not profiles:
            return []

        return [
            {"id": p["id"], "display": f"{p['name']} ({p['codec']})"} for p in profiles
        ]

    def _validate_folder_paths(self, entrada: str, saida: str) -> tuple:
        """Valida caminhos das pastas de entrada e saída."""
        entrada_path = Path(entrada)
        saida_path = Path(saida)

        # Valida pasta de entrada
        if not entrada_path.exists():
            return (False, f"Pasta de entrada não existe: {entrada}")

        if not entrada_path.is_dir():
            return (False, f"Caminho de entrada não é uma pasta: {entrada}")

        # Valida/cria pasta de saída
        try:
            saida_path.mkdir(parents=True, exist_ok=True)
            if not saida_path.exists():
                return (False, f"Não foi possível criar pasta de saída: {saida}")
        except PermissionError:
            return (False, f"Sem permissão para criar pasta de saída: {saida}")
        except Exception as e:
            return (False, f"Erro ao validar pasta de saída: {e}")

        return (True, "Caminhos válidos")

    def _validate_profile(self, profile_id: str) -> tuple:
        """Valida se o perfil existe."""
        profile = self.profile_mgr.get_profile(profile_id)
        if not profile:
            return (False, f"Perfil não encontrado: {profile_id}")
        return (True, "Perfil válido")

    def _get_folder_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Obtém pasta por índice (1-based)."""
        folders = self.folder_manager.list_folders()
        if 1 <= index <= len(folders):
            return folders[index - 1]
        return None

    def list_recurrent_folders(self):
        """Lista todas as pastas recorrentes configuradas."""
        self.menu.clear()
        self.menu.print_header("Pastas Recorrentes Configuradas")

        folders = self.folder_manager.list_folders()

        if not folders:
            self.menu.print_warning("Nenhuma pasta recorrente configurada")
            input("\nPressione Enter para continuar...")
            return

        table = Table(
            title="Pastas Recorrentes", show_header=True, header_style="bold magenta"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Nome", style="cyan")
        table.add_column("Entrada", style="white")
        table.add_column("Saída", style="white")
        table.add_column("Perfil", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Processados", style="blue")

        for i, folder in enumerate(folders, 1):
            input_path = Path(folder.get("input_directory", ""))
            input_exists = input_path.exists()
            status = (
                "[green]OK[/green]" if input_exists else "[red]Pasta não existe[/red]"
            )

            enabled = folder.get("enabled", False)
            enabled_status = (
                "[green]Ativa[/green]" if enabled else "[yellow]Desativada[/yellow]"
            )

            total_processed = folder.get("total_processed", 0)

            table.add_row(
                str(i),
                folder.get("name", "N/A"),
                folder.get("input_directory", "N/A"),
                folder.get("output_directory", "N/A"),
                folder.get("profile_id", "N/A"),
                f"{enabled_status} | {status}",
                str(total_processed),
            )

        self.menu.console.print(table)
        input("\nPressione Enter para continuar...")

    def add_recurrent_folder(self):
        """Adiciona nova pasta recorrente."""
        self.menu.clear()
        self.menu.print_header("Adicionar Nova Pasta Recorrente")

        profiles = self._get_profile_choices()
        if not profiles:
            self.menu.print_error("Nenhum perfil disponível. Crie um perfil primeiro.")
            input("\nPressione Enter para continuar...")
            return

        self.menu.print_info("Perfis disponíveis:")
        for i, p in enumerate(profiles, 1):
            self.menu.console.print(f"  [{i}] {p['display']}")
        self.menu.console.print()

        # Coleta nome descritivo
        nome = self.menu.ask("Nome descritivo")
        if not nome or not nome.strip():
            self.menu.print_error("Nome não pode ser vazio")
            input("\nPressione Enter para continuar...")
            return

        # Coleta caminho de entrada
        entrada = self.menu.ask("Caminho da pasta de entrada")
        if not entrada or not entrada.strip():
            self.menu.print_error("Caminho de entrada não pode ser vazio")
            input("\nPressione Enter para continuar...")
            return

        # Coleta caminho de saída
        saida = self.menu.ask("Caminho da pasta de saída")
        if not saida or not saida.strip():
            self.menu.print_error("Caminho de saída não pode ser vazio")
            input("\nPressione Enter para continuar...")
            return

        # Seleção de perfil
        profile_idx = self.menu.ask_int("Número do perfil", default=1)

        if profile_idx < 1 or profile_idx > len(profiles):
            self.menu.print_error("Número de perfil inválido")
            input("\nPressione Enter para continuar...")
            return

        profile_id = profiles[profile_idx - 1]["id"]

        # Valida caminhos
        valido, mensagem = self._validate_folder_paths(entrada, saida)
        if not valido:
            self.menu.print_warning(mensagem)
            continuar = self.menu.ask_confirm(
                "Deseja continuar mesmo assim?", default=False
            )
            if not continuar:
                input("\nPressione Enter para continuar...")
                return

        # Valida perfil
        valido, mensagem = self._validate_profile(profile_id)
        if not valido:
            self.menu.print_error(mensagem)
            input("\nPressione Enter para continuar...")
            return

        # Configurações de opções
        self.menu.console.print("\n[bold]Configurações de Opções:[/bold]")

        preserve_subdirs = self.menu.ask_confirm(
            "Preservar subdiretórios no output?", default=True
        )

        self.menu.console.print(
            "\n[cyan]Como lidar com arquivos já existentes no output?[/cyan]"
        )
        self.menu.console.print("  [1] Pular arquivo (não fazer nada)")
        self.menu.console.print(
            "  [2] Criar cópia numerada automaticamente (ex: arquivo_1.mkv)"
        )
        self.menu.console.print(
            "  [3] Substituir arquivo existente (PERIGO: perde o arquivo original)"
        )

        conflict_choice = self.menu.ask_int("Escolha uma opção", default=2)

        if conflict_choice == 1:
            skip_existing = True
            rename_existing = False
        elif conflict_choice == 2:
            skip_existing = False
            rename_existing = True
        else:  # choice == 3
            skip_existing = False
            rename_existing = False  # Vai substituir

        delete_source = self.menu.ask_confirm(
            "Excluir arquivo de origem após conversão?", default=False
        )

        copy_subtitles = self.menu.ask_confirm("Copiar legendas?", default=True)

        # Monta estrutura de dados
        folder_data = {
            "name": nome.strip(),
            "input_directory": entrada.strip(),
            "output_directory": saida.strip(),
            "profile_id": profile_id,
            "enabled": True,
            "options": {
                "preserve_subdirectories": preserve_subdirs,
                "skip_existing_output": skip_existing,
                "rename_existing_output": rename_existing,  # Nova opção: renomeia automaticamente
                "delete_source_after_encode": delete_source,
                "copy_subtitles": copy_subtitles,
                "supported_extensions": [
                    ".mp4",
                    ".mkv",
                    ".avi",
                    ".mov",
                    ".wmv",
                    ".flv",
                    ".webm",
                    ".m4v",
                    ".mpeg",
                    ".mpg",
                ],
                "min_file_size_mb": 0,
            },
        }

        # Exibe resumo
        self.menu.console.print()

        # Determina ação para arquivos existentes
        if skip_existing:
            existing_action = "Pular"
        elif rename_existing:
            existing_action = "Renomear automaticamente"
        else:
            existing_action = "Substituir"

        self.menu.console.print(
            Panel(
                f"[bold]Confirmação:[/bold]\n\n"
                f"Nome: {nome}\n"
                f"Entrada: {entrada}\n"
                f"Saída: {saida}\n"
                f"Perfil: {profile_id}\n"
                f"Preservar subdiretórios: {'Sim' if preserve_subdirs else 'Não'}\n"
                f"Ação para existentes: {existing_action}\n"
                f"Excluir origem: {'Sim' if delete_source else 'Não'}\n"
                f"Copiar legendas: {'Sim' if copy_subtitles else 'Não'}",
                border_style="cyan",
                title="Resumo",
            )
        )

        if not self.menu.ask_confirm("Adicionar pasta recorrente?", default=False):
            self.menu.print_warning("Operação cancelada")
            input("\nPressione Enter para continuar...")
            return

        try:
            folder_id = self.folder_manager.add_folder(folder_data)
            self.menu.print_success(
                f"Pasta recorrente adicionada com sucesso (ID: {folder_id[:8]}...)"
            )
        except ValueError as e:
            self.menu.print_error(str(e))
        except Exception as e:
            self.menu.print_error(f"Erro ao adicionar pasta recorrente: {e}")

        input("\nPressione Enter para continuar...")

    def remove_recurrent_folder(self):
        """Remove pasta recorrente por índice."""
        self.menu.clear()
        self.menu.print_header("Remover Pasta Recorrente")

        folders = self.folder_manager.list_folders()

        if not folders:
            self.menu.print_warning("Nenhuma pasta recorrente configurada")
            input("\nPressione Enter para continuar...")
            return

        table = Table(
            title="Pastas Recorrentes", show_header=True, header_style="bold magenta"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Nome", style="cyan")
        table.add_column("Entrada", style="white")
        table.add_column("Saída", style="white")
        table.add_column("Perfil", style="green")
        table.add_column("Status", style="yellow")

        for i, folder in enumerate(folders, 1):
            enabled_status = (
                "[green]Ativa[/green]"
                if folder.get("enabled", False)
                else "[yellow]Desativada[/yellow]"
            )
            table.add_row(
                str(i),
                folder.get("name", "N/A"),
                folder.get("input_directory", "N/A")[:30],
                folder.get("output_directory", "N/A")[:30],
                folder.get("profile_id", "N/A")[:15],
                enabled_status,
            )

        self.menu.console.print(table)

        idx = self.menu.ask_int("Número da pasta para remover", default=0)

        if idx < 1 or idx > len(folders):
            self.menu.print_error("Número inválido")
            input("\nPressione Enter para continuar...")
            return

        folder = folders[idx - 1]
        folder_name = folder.get("name", "Desconhecida")

        self.menu.console.print()
        self.menu.print_warning(f"Dados da pasta:")
        self.menu.console.print(f"  Nome: {folder_name}")
        self.menu.console.print(f"  Entrada: {folder.get('input_directory', 'N/A')}")
        self.menu.console.print(f"  Saída: {folder.get('output_directory', 'N/A')}")
        self.menu.console.print(
            f"  Total processado: {folder.get('total_processed', 0)}"
        )

        if not self.menu.ask_confirm(f"Remover pasta '{folder_name}'?", default=False):
            self.menu.print_warning("Operação cancelada")
            input("\nPressione Enter para continuar...")
            return

        if self.folder_manager.remove_folder(folder.get("id")):
            self.menu.print_success(f"Pasta '{folder_name}' removida com sucesso")
        else:
            self.menu.print_error("Erro ao remover pasta recorrente")

        input("\nPressione Enter para continuar...")

    def edit_recurrent_folder(self):
        """Edita pasta recorrente existente."""
        self.menu.clear()
        self.menu.print_header("Editar Pasta Recorrente")

        folders = self.folder_manager.list_folders()

        if not folders:
            self.menu.print_warning("Nenhuma pasta recorrente configurada")
            input("\nPressione Enter para continuar...")
            return

        table = Table(
            title="Pastas Recorrentes", show_header=True, header_style="bold magenta"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Nome", style="cyan")
        table.add_column("Entrada", style="white")
        table.add_column("Saída", style="white")
        table.add_column("Perfil", style="green")

        for i, folder in enumerate(folders, 1):
            table.add_row(
                str(i),
                folder.get("name", "N/A"),
                folder.get("input_directory", "N/A")[:30],
                folder.get("output_directory", "N/A")[:30],
                folder.get("profile_id", "N/A")[:15],
            )

        self.menu.console.print(table)

        idx = self.menu.ask_int("Número da pasta para editar", default=0)

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

        self.menu.console.print(
            "\n[bold]Valores atuais entre colchetes. Pressione Enter para manter.[/bold]\n"
        )

        # Nome
        nome_atual = folder.get("name", "")
        nome = self.menu.ask(f"Nome descritivo [{nome_atual}]", default="")
        if not nome:
            nome = nome_atual

        # Entrada
        entrada_atual = folder.get("input_directory", "")
        entrada = self.menu.ask(f"Pasta de entrada [{entrada_atual}]", default="")
        if not entrada:
            entrada = entrada_atual

        # Saída
        saida_atual = folder.get("output_directory", "")
        saida = self.menu.ask(f"Pasta de saída [{saida_atual}]", default="")
        if not saida:
            saida = saida_atual

        # Perfil
        self.menu.print_info("Perfis disponíveis:")
        for i, p in enumerate(profiles, 1):
            current_marker = (
                " (atual)" if p["id"] == folder.get("profile_id", "") else ""
            )
            self.menu.console.print(f"  [{i}] {p['display']}{current_marker}")

        profile_input = self.menu.ask("Número do perfil", default="")
        profile_id = folder.get("profile_id", "")

        if profile_input:
            try:
                profile_idx = int(profile_input)
                if 1 <= profile_idx <= len(profiles):
                    profile_id = profiles[profile_idx - 1]["id"]
                else:
                    self.menu.print_warning("Número inválido, mantendo perfil atual")
            except ValueError:
                self.menu.print_warning("Entrada inválida, mantendo perfil atual")

        # Valida caminhos se foram alterados
        if entrada != entrada_atual or saida != saida_atual:
            valido, mensagem = self._validate_folder_paths(entrada, saida)
            if not valido:
                self.menu.print_warning(mensagem)
                continuar = self.menu.ask_confirm(
                    "Deseja continuar mesmo assim?", default=False
                )
                if not continuar:
                    input("\nPressione Enter para continuar...")
                    return

        # Valida perfil se foi alterado
        if profile_id != folder.get("profile_id", ""):
            valido, mensagem = self._validate_profile(profile_id)
            if not valido:
                self.menu.print_error(mensagem)
                input("\nPressione Enter para continuar...")
                return

        # Opções
        self.menu.console.print("\n[bold]Opções (Enter para manter atuais):[/bold]")

        options = folder.get("options", {})

        preserve_subdirs = self.menu.ask_confirm(
            f"Preservar subdiretórios [{'Sim' if options.get('preserve_subdirectories', True) else 'Não'}]",
            default=options.get("preserve_subdirectories", True),
        )

        skip_existing = self.menu.ask_confirm(
            f"Pular existentes [{'Sim' if options.get('skip_existing_output', True) else 'Não'}]",
            default=options.get("skip_existing_output", True),
        )

        delete_source = self.menu.ask_confirm(
            f"Excluir origem [{'Sim' if options.get('delete_source_after_encode', False) else 'Não'}]",
            default=options.get("delete_source_after_encode", False),
        )

        copy_subtitles = self.menu.ask_confirm(
            f"Copiar legendas [{'Sim' if options.get('copy_subtitles', True) else 'Não'}]",
            default=options.get("copy_subtitles", True),
        )

        # Exibe resumo
        self.menu.console.print()
        self.menu.console.print(
            Panel(
                f"[bold]Alterações:[/bold]\n\n"
                f"Nome: {nome}\n"
                f"Entrada: {entrada}\n"
                f"Saída: {saida}\n"
                f"Perfil: {profile_id}\n"
                f"Preservar subdiretórios: {'Sim' if preserve_subdirs else 'Não'}\n"
                f"Pular existentes: {'Sim' if skip_existing else 'Não'}\n"
                f"Excluir origem: {'Sim' if delete_source else 'Não'}\n"
                f"Copiar legendas: {'Sim' if copy_subtitles else 'Não'}",
                border_style="cyan",
                title="Resumo",
            )
        )

        if not self.menu.ask_confirm("Salvar alterações?", default=False):
            self.menu.print_warning("Operação cancelada")
            input("\nPressione Enter para continuar...")
            return

        updates = {
            "name": nome.strip(),
            "input_directory": entrada.strip(),
            "output_directory": saida.strip(),
            "profile_id": profile_id,
            "options": {
                "preserve_subdirectories": preserve_subdirs,
                "skip_existing_output": skip_existing,
                "delete_source_after_encode": delete_source,
                "copy_subtitles": copy_subtitles,
                "supported_extensions": options.get(
                    "supported_extensions",
                    [
                        ".mp4",
                        ".mkv",
                        ".avi",
                        ".mov",
                        ".wmv",
                        ".flv",
                        ".webm",
                        ".m4v",
                        ".mpeg",
                        ".mpg",
                    ],
                ),
                "min_file_size_mb": options.get("min_file_size_mb", 0),
            },
        }

        try:
            if self.folder_manager.update_folder(folder.get("id"), updates):
                self.menu.print_success("Pasta recorrente atualizada com sucesso")
            else:
                self.menu.print_error("Erro ao atualizar pasta recorrente")
        except ValueError as e:
            self.menu.print_error(str(e))
        except Exception as e:
            self.menu.print_error(f"Erro ao atualizar pasta recorrente: {e}")

        input("\nPressione Enter para continuar...")

    def toggle_enable_folder(self):
        """Ativa ou desativa pasta recorrente."""
        self.menu.clear()
        self.menu.print_header("Ativar/Desativar Pasta Recorrente")

        folders = self.folder_manager.list_folders()

        if not folders:
            self.menu.print_warning("Nenhuma pasta recorrente configurada")
            input("\nPressione Enter para continuar...")
            return

        table = Table(
            title="Pastas Recorrentes", show_header=True, header_style="bold magenta"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Nome", style="cyan")
        table.add_column("Entrada", style="white")
        table.add_column("Status", style="yellow")

        for i, folder in enumerate(folders, 1):
            enabled = folder.get("enabled", False)
            status = (
                "[green]Ativa[/green]" if enabled else "[yellow]Desativada[/yellow]"
            )
            table.add_row(
                str(i),
                folder.get("name", "N/A"),
                folder.get("input_directory", "N/A")[:40],
                status,
            )

        self.menu.console.print(table)

        idx = self.menu.ask_int("Número da pasta", default=0)

        if idx < 1 or idx > len(folders):
            self.menu.print_error("Número inválido")
            input("\nPressione Enter para continuar...")
            return

        folder = folders[idx - 1]
        folder_id = folder.get("id")
        folder_name = folder.get("name", "Desconhecida")
        current_enabled = folder.get("enabled", False)

        new_status = not current_enabled
        action = "ativar" if new_status else "desativar"
        new_status_text = "Ativa" if new_status else "Desativada"

        if not self.menu.ask_confirm(
            f"Deseja {action} a pasta '{folder_name}'?", default=False
        ):
            self.menu.print_warning("Operação cancelada")
            input("\nPressione Enter para continuar...")
            return

        if new_status:
            success = self.folder_manager.enable_folder(folder_id)
        else:
            success = self.folder_manager.disable_folder(folder_id)

        if success:
            self.menu.print_success(
                f"Pasta '{folder_name}' {new_status_text.lower()} com sucesso"
            )
        else:
            self.menu.print_error(f"Erro ao {action} a pasta")

        input("\nPressione Enter para continuar...")

    def start_stop_monitors(self):
        """Inicia ou para monitores de pastas recorrentes."""
        self.menu.clear()
        self.menu.print_header("Gerenciar Monitores", "Iniciar/Parar monitoramento")

        folders = self.folder_manager.list_folders()

        if not folders:
            self.menu.print_warning("Nenhuma pasta recorrente configurada")
            input("\nPressione Enter para continuar...")
            return

        # Exibe status dos monitores
        table = Table(
            title="Status dos Monitores", show_header=True, header_style="bold magenta"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Nome", style="cyan")
        table.add_column("Entrada", style="white")
        table.add_column("Status", style="yellow")
        table.add_column("Monitor", style="green")

        is_running = (
            self._monitor_service is not None and self._monitor_service.is_running()
        )

        for i, folder in enumerate(folders, 1):
            enabled = folder.get("enabled", False)
            status = (
                "[green]Ativa[/green]" if enabled else "[yellow]Desativada[/yellow]"
            )
            if is_running and enabled:
                monitor_status = "[green]Rodando[/green]"
            elif enabled:
                monitor_status = "[yellow]Parado[/yellow]"
            else:
                monitor_status = "[dim]Desativado[/dim]"

            table.add_row(
                str(i),
                folder.get("name", "N/A"),
                folder.get("input_directory", "N/A")[:30],
                status,
                monitor_status,
            )

        self.menu.console.print(table)

        self.menu.console.print()
        self.menu.print_info("Opções:")
        if is_running:
            self.menu.console.print("  [1] Reiniciar monitores")
            self.menu.console.print("  [2] Parar todos os monitores")
        else:
            self.menu.console.print("  [1] Iniciar todos os monitores de pastas ativas")
            self.menu.console.print("  [2] Parar todos os monitores")
        self.menu.console.print("  [0] Voltar")

        choice = self.menu.ask("Escolha uma opção", default="0")

        if choice == "1":
            enabled_folders = self.folder_manager.get_enabled_folders()
            if not enabled_folders:
                self.menu.print_warning("Nenhuma pasta ativa para iniciar monitores")
                input("\nPressione Enter para continuar...")
                return

            if self._monitor_service is not None and self._monitor_service.is_running():
                self.menu.print_info("Parando serviço existente...")
                self._monitor_service.stop()

            if self._encoder is None and self.queue_manager is not None:
                self._encoder = EncoderEngine(
                    queue_manager=self.queue_manager,
                )

            self._monitor_service = RecurrentMonitorService(
                config_manager=self.config,
                queue_manager=self.queue_manager,
                job_manager=self.job_manager,
                profile_manager=self.profile_mgr,
                history_manager=self.history_manager,
                encoder=self._encoder,
            )

            self._monitor_service.start()

            self.menu.print_success(
                f"Monitores iniciados para {len(enabled_folders)} pasta(s) ativa(s)"
            )
            self.menu.console.print(
                "\n[dim]Nota: O serviço de monitoramento está rodando em segundo plano.[/dim]"
            )
            input("\nPressione Enter para continuar...")

        elif choice == "2":
            if self._monitor_service is not None and self._monitor_service.is_running():
                self.menu.print_info("Parando todos os monitores...")
                self._monitor_service.stop()
                self.menu.print_success("Monitores parados com sucesso")
            else:
                self.menu.print_warning("Nenhum monitor está rodando")
            input("\nPressione Enter para continuar...")
            return

    def view_history(self):
        """Visualiza histórico de processamento de pastas recorrentes."""
        self.menu.clear()
        self.menu.print_header("Histórico de Processamento")

        folders = self.folder_manager.list_folders()

        if not folders:
            self.menu.print_warning("Nenhuma pasta recorrente configurada")
            input("\nPressione Enter para continuar...")
            return

        # Exibe resumo do histórico por pasta usando o history manager
        table = Table(
            title="Resumo de Processamento por Pasta",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Nome", style="cyan")
        table.add_column("Total Processado", style="blue")
        table.add_column("Sucessos", style="green")
        table.add_column("Falhas", style="red")
        table.add_column("Duração Média", style="yellow")
        table.add_column("Último Processado", style="magenta")

        for i, folder in enumerate(folders, 1):
            folder_id = folder.get("id", "")
            folder_name = folder.get("name", "N/A")

            # Obter estatísticas do history manager
            stats = (
                self.history_manager.get_stats(folder_id)
                if folder_id
                else {
                    "total_processed": 0,
                    "success_count": 0,
                    "failed_count": 0,
                    "average_duration": 0,
                    "last_processed_at": None,
                }
            )

            # Formatar duração média
            avg_duration = stats.get("average_duration", 0)
            if avg_duration > 0:
                avg_duration_str = f"{avg_duration:.1f}s"
            else:
                avg_duration_str = "-"

            # Formatar última data de processamento
            last_processed = stats.get("last_processed_at")
            if last_processed:
                try:
                    from datetime import datetime

                    last_dt = datetime.fromisoformat(
                        last_processed.replace("Z", "+00:00")
                    )
                    last_processed_str = last_dt.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    last_processed_str = last_processed
            else:
                last_processed_str = "Nunca"

            table.add_row(
                str(i),
                folder_name,
                str(stats.get("total_processed", 0)),
                str(stats.get("success_count", 0)),
                str(stats.get("failed_count", 0)),
                avg_duration_str,
                last_processed_str,
            )

        self.menu.console.print(table)

        # Opção para ver histórico detalhado de uma pasta específica
        print("\nDeseja ver o histórico detalhado de uma pasta específica?")
        try:
            choice = Prompt.ask(
                "[bold cyan]Escolha uma pasta (1-{0}) ou 0 para voltar[/bold cyan]".format(
                    len(folders)
                ),
                default="0",
            )
            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(folders):
                selected_folder = folders[choice_idx]
                self._view_detailed_history(selected_folder)
        except (ValueError, KeyboardInterrupt):
            pass

    def _view_detailed_history(self, folder: Dict[str, Any]):
        """Visualiza histórico detalhado de uma pasta específica."""
        self.menu.clear()
        self.menu.print_header(f"Histórico Detalhado - {folder.get('name', 'N/A')}")

        folder_id = folder.get("id", "")
        if not folder_id:
            self.menu.print_error("ID da pasta não encontrado")
            input("\nPressione Enter para continuar...")
            return

        # Obter histórico detalhado
        history = self.history_manager.get_recent_entries(
            folder_id, limit=50
        )  # Últimos 50 registros

        if not history:
            self.menu.print_warning("Nenhum histórico encontrado para esta pasta")
            input("\nPressione Enter para continuar...")
            return

        # Exibir histórico detalhado
        table = Table(
            title=f"Registros Recentes - {folder.get('name', 'N/A')}",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Data/Hora", style="cyan", width=20)
        table.add_column("Status", style="green")
        table.add_column("Duração", style="yellow")
        table.add_column("Entrada", style="dim")
        table.add_column("Saída", style="dim")

        for entry in history:
            # Formatar data e hora
            completed_at = entry.get("completed_at", "")
            if completed_at:
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                    date_str = dt.strftime("%d/%m %H:%M:%S")
                except Exception:
                    date_str = completed_at
            else:
                date_str = "N/A"

            # Status com cor
            status = entry.get("status", "unknown")
            if status == "completed":
                status_display = "[green]✓[/green] Completado"
            elif status == "failed":
                status_display = "[red]✗[/red] Falhou"
            else:
                status_display = f"[yellow]?[/yellow] {status}"

            # Duração
            duration = entry.get("duration_seconds", 0)
            duration_str = f"{duration:.1f}s" if duration > 0 else "-"

            # Caminhos
            input_path = Path(entry.get("input_path", "")).name
            output_path = Path(entry.get("output_path", "")).name

            table.add_row(
                date_str, status_display, duration_str, input_path, output_path
            )

        self.menu.console.print(table)
        input("\nPressione Enter para continuar...")

        # Opção para ver detalhes de uma pasta específica
        self.menu.console.print()
        self.menu.print_info(
            "Digite o número da pasta para ver detalhes (0 para voltar)"
        )

        idx = self.menu.ask_int("Número da pasta", default=0)

        if idx < 1 or idx > len(folders):
            return

        folder = folders[idx - 1]

        self.menu.console.print()
        self.menu.console.print(
            Panel(
                f"[bold]Detalhes da Pasta:[/bold]\n\n"
                f"Nome: {folder.get('name', 'N/A')}\n"
                f"ID: {folder.get('id', 'N/A')}\n"
                f"Entrada: {folder.get('input_directory', 'N/A')}\n"
                f"Saída: {folder.get('output_directory', 'N/A')}\n"
                f"Perfil: {folder.get('profile_id', 'N/A')}\n"
                f"Total Processado: {folder.get('total_processed', 0)}\n"
                f"Última Execução: {folder.get('last_run', 'Nunca')}\n"
                f"Criada em: {folder.get('created_at', 'N/A')}",
                border_style="cyan",
                title="Informações Detalhadas",
            )
        )

        input("\nPressione Enter para continuar...")
