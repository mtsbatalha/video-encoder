"""
Interface de usuário para conexões remotas.

Este módulo contém a classe RemoteConnectionUI que fornece interfaces
interativas para configuração e gerenciamento de conexões remotas.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, IntPrompt, Confirm
from typing import List, Dict, Any, Optional, Tuple

from .menu import Menu
from ..managers.config_manager import ConfigManager
from ..managers.remote_directory_manager import RemoteDirectoryManager
from ..utils.path_utils import PathUtils, RemoteProtocol


class RemoteConnectionUI:
    """Interface de usuário para conexões remotas."""
    
    def __init__(self, console: Console, config_manager: ConfigManager):
        """
        Inicializa a UI de conexões remotas.
        
        Args:
            console: Instância do Console Rich
            config_manager: Instância do ConfigManager
        """
        self.console = console
        self.config_manager = config_manager
        self.remote_manager = RemoteDirectoryManager(config_manager)
        self.menu = Menu(console)
    
    def ask_directory_type(self) -> str:
        """
        Pergunta se o diretório é local ou remoto.
        
        Returns:
            'local' ou 'remote'
        """
        self.console.print()
        self.console.print(Panel(
            "[bold]O diretório de entrada é:[/bold]\n\n"
            "[1] 📁 Local (neste computador)\n"
            "[2] 🌐 Remoto (servidor, share de rede, etc.)",
            title="📂 Tipo de Diretório",
            border_style="cyan"
        ))
        
        choice = IntPrompt.ask(
            "Escolha uma opção",
            choices=["1", "2"],
            default="1"
        )
        
        return "local" if choice == 1 else "remote"
    
    def ask_remote_protocol(self) -> RemoteProtocol:
        """
        Pergunta qual protocolo remoto usar.
        
        Returns:
            RemoteProtocol selecionado
        """
        self.console.print()
        self.console.print(Panel(
            "[bold]Selecione o protocolo:[/bold]\n\n"
            "[1] 🔐 SSHFS (Filesystem sobre SSH)\n"
            "[2] 📁 SMB/CIFS (Windows Share/Samba)\n"
            "[3] 📡 NFS (Network File System)\n"
            "[4] 💾 Montado (rclone, etc.)\n"
            "[5] 📡 UNC Path (Caminho de Rede Windows)\n"
            "[6] 💾 Usar conexão salva",
            title="🌐 Protocolo Remoto",
            border_style="magenta"
        ))
        
        choice = IntPrompt.ask(
            "Escolha uma opção",
            choices=["1", "2", "3", "4", "5", "6"],
            default="1"
        )
        
        protocols = {
            1: RemoteProtocol.SSHFS,
            2: RemoteProtocol.SMB,
            3: RemoteProtocol.NFS,
            4: RemoteProtocol.MOUNTED,
            5: RemoteProtocol.UNC
        }
        
        if choice == 6:
            return self._select_saved_connection()
        
        return protocols.get(choice, RemoteProtocol.SSHFS)
    
    def _select_saved_connection(self) -> RemoteProtocol:
        """
        Seleciona conexão salva.
        
        Returns:
            RemoteProtocol da conexão selecionada
        """
        connections = self.config_manager.get_saved_connections()
        
        if not connections:
            self.menu.print_warning("Nenhuma conexão salva encontrada")
            return RemoteProtocol.SSHFS
        
        # Exibir conexões salvas
        table = Table(title="Conexões Salvas", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Nome", style="cyan")
        table.add_column("Protocolo", style="green")
        table.add_column("Host", style="white")
        
        for i, conn in enumerate(connections, 1):
            table.add_row(
                str(i),
                conn.get('name', 'N/A'),
                conn.get('protocol', 'unknown'),
                conn.get('host', conn.get('mount_point', 'N/A'))
            )
        
        self.console.print(table)
        
        choice = IntPrompt.ask(
            "Selecione uma conexão",
            choices=[str(i) for i in range(1, len(connections) + 1)],
            default="1"
        )
        
        # Armazenar conexão selecionada para uso posterior
        self._selected_connection = connections[choice - 1]
        
        protocol_map = {
            'sshfs': RemoteProtocol.SSHFS,
            'smb': RemoteProtocol.SMB,
            'nfs': RemoteProtocol.NFS,
            'mounted': RemoteProtocol.MOUNTED,
            'unc': RemoteProtocol.UNC
        }
        
        return protocol_map.get(connections[choice - 1].get('protocol'), RemoteProtocol.SSHFS)
    
    def configure_sshfs(self) -> Tuple[str, Dict[str, Any]]:
        """
        Configura conexão SSHFS.
        
        Returns:
            Tuple com (path remoto, config de conexão)
        """
        self.console.print()
        self.menu.print_header("🔐 Configurar SSHFS", "Filesystem sobre SSH")
        
        host = Prompt.ask("Host/Endereço do servidor")
        port = Prompt.ask("Porta SSH", default="22")
        username = Prompt.ask("Usuário")
        
        self.console.print("\nTipo de autenticação:")
        auth_choice = IntPrompt.ask(
            "[1] Senha\n[2] Chave SSH",
            choices=["1", "2"],
            default="1"
        )
        
        connection_config = {
            'host': host,
            'port': int(port),
            'username': username,
            'protocol': 'sshfs'
        }
        
        if auth_choice == 1:
            password = Prompt.ask("Senha", password=True)
            connection_config['password'] = password
        else:
            key_path = Prompt.ask("Caminho da chave privada")
            connection_config['private_key_path'] = key_path
        
        default_path = Prompt.ask("Caminho padrão (opcional)", default="/")
        connection_config['default_path'] = default_path
        
        # Construir path remoto
        remote_path = f"ssh://{username}@{host}:{port}{default_path}"
        
        # Opção de salvar conexão
        if Confirm.ask("\nDeseja salvar esta conexão?", default=False):
            name = Prompt.ask("Nome para a conexão")
            connection_config['name'] = name
            self.config_manager.add_saved_connection(connection_config)
            self.menu.print_success("Conexão salva com sucesso!")
        
        return (remote_path, connection_config)
    
    def configure_smb(self) -> Tuple[str, Dict[str, Any]]:
        """
        Configura conexão SMB.
        
        Returns:
            Tuple com (path remoto, config de conexão)
        """
        self.console.print()
        self.menu.print_header("📁 Configurar SMB/CIFS", "Windows Share/Samba")
        
        host = Prompt.ask("Host/Servidor")
        share = Prompt.ask("Nome do Share")
        username = Prompt.ask("Usuário (opcional)", default="")
        password = Prompt.ask("Senha (opcional)", password=True, default="")
        path = Prompt.ask("Caminho dentro do share (opcional)", default="/")
        
        connection_config = {
            'host': host,
            'share': share,
            'protocol': 'smb'
        }
        
        if username:
            connection_config['username'] = username
        if password:
            connection_config['password'] = password
        
        # Construir path remoto
        remote_path = f"smb://{host}/{share}{path if path != '/' else ''}"
        
        # Opção de salvar conexão
        if Confirm.ask("\nDeseja salvar esta conexão?", default=False):
            name = Prompt.ask("Nome para a conexão")
            connection_config['name'] = name
            self.config_manager.add_saved_connection(connection_config)
            self.menu.print_success("Conexão salva com sucesso!")
        
        return (remote_path, connection_config)
    
    def configure_nfs(self) -> Tuple[str, Dict[str, Any]]:
        """
        Configura conexão NFS.
        
        Returns:
            Tuple com (path remoto, config de conexão)
        """
        self.console.print()
        self.menu.print_header("📡 Configurar NFS", "Network File System")
        
        host = Prompt.ask("Host/Servidor NFS")
        export = Prompt.ask("Export NFS (ex: /exports/videos)")
        path = Prompt.ask("Caminho dentro do export (opcional)", default="/")
        
        connection_config = {
            'host': host,
            'export': export,
            'protocol': 'nfs'
        }
        
        # Construir path remoto
        remote_path = f"nfs://{host}/{export}{path if path != '/' else ''}"
        
        # Opção de salvar conexão
        if Confirm.ask("\nDeseja salvar esta conexão?", default=False):
            name = Prompt.ask("Nome para a conexão")
            connection_config['name'] = name
            self.config_manager.add_saved_connection(connection_config)
            self.menu.print_success("Conexão salva com sucesso!")
        
        return (remote_path, connection_config)
    
    def configure_mounted(self) -> Tuple[str, Dict[str, Any]]:
        """
        Configura diretório montado.
        
        Returns:
            Tuple com (path remoto, config de conexão)
        """
        self.console.print()
        self.menu.print_header("💾 Configurar Diretório Montado", "rclone, etc.")
        
        mount_point = Prompt.ask("Ponto de mount (ex: X:, /mnt/gdrive)")
        path = Prompt.ask("Caminho dentro do mount (opcional)", default="/")
        mount_type = Prompt.ask("Tipo de mount", default="rclone")
        
        connection_config = {
            'mount_point': mount_point,
            'mount_type': mount_type,
            'protocol': 'mounted'
        }
        
        # Construir path remoto
        remote_path = f"mounted://{mount_point}{path if path != '/' else ''}"
        
        # Opção de salvar conexão
        if Confirm.ask("\nDeseja salvar esta conexão?", default=False):
            name = Prompt.ask("Nome para a conexão")
            connection_config['name'] = name
            self.config_manager.add_saved_connection(connection_config)
            self.menu.print_success("Conexão salva com sucesso!")
        
        return (remote_path, connection_config)
    
    def configure_unc(self) -> Tuple[str, Dict[str, Any]]:
        """
        Configura caminho UNC.
        
        Returns:
            Tuple com (path remoto, config de conexão)
        """
        self.console.print()
        self.menu.print_header("📡 Configurar UNC", "Caminho de Rede Windows")
        
        host = Prompt.ask("Host/Servidor")
        share = Prompt.ask("Share")
        path = Prompt.ask("Caminho dentro do share (opcional)", default="\\")
        
        connection_config = {
            'host': host,
            'share': share,
            'protocol': 'unc'
        }
        
        # Construir path remoto (formato UNC)
        remote_path = f"\\\\{host}\\{share}{path.replace('/', '\\') if path != '\\' else ''}"
        
        # Opção de salvar conexão
        if Confirm.ask("\nDeseja salvar esta conexão?", default=False):
            name = Prompt.ask("Nome para a conexão")
            connection_config['name'] = name
            self.config_manager.add_saved_connection(connection_config)
            self.menu.print_success("Conexão salva com sucesso!")
        
        return (remote_path, connection_config)
    
    def configure_remote_directory(self, protocol: RemoteProtocol) -> Tuple[str, Dict[str, Any]]:
        """
        Configura diretório remoto baseado no protocolo.
        
        Args:
            protocol: Protocolo remoto selecionado.
            
        Returns:
            Tuple com (path remoto, config de conexão)
        """
        config_methods = {
            RemoteProtocol.SSHFS: self.configure_sshfs,
            RemoteProtocol.SMB: self.configure_smb,
            RemoteProtocol.NFS: self.configure_nfs,
            RemoteProtocol.MOUNTED: self.configure_mounted,
            RemoteProtocol.UNC: self.configure_unc
        }
        
        config_method = config_methods.get(protocol)
        if config_method:
            return config_method()
        
        return ("", {})
    
    def test_remote_connection(self, remote_path: str, connection_config: Dict[str, Any]) -> bool:
        """
        Testa conexão remota.
        
        Args:
            remote_path: Caminho remoto.
            connection_config: Configuração de conexão.
            
        Returns:
            True se conexão bem-sucedida, False caso contrário.
        """
        self.console.print("\n[cyan]Testando conexão...[/cyan]")
        
        success, msg = self.remote_manager.test_connection(remote_path, connection_config)
        
        if success:
            self.menu.print_success(msg)
        else:
            self.menu.print_error(msg)
        
        return success
    
    def show_copy_progress(self, progress: Any) -> None:
        """
        Exibe progresso de cópia.
        
        Args:
            progress: Objeto CopyProgress.
        """
        from ..managers.remote_directory_manager import CopyProgress, CopyStatus
        
        if not isinstance(progress, CopyProgress):
            return
        
        # Limpar linha e mostrar progresso
        self.console.print(f"\n[cyan]📥 {progress.current_file}[/cyan]")
        
        # Barra de progresso por arquivo
        if progress.total_bytes > 0:
            file_percent = (progress.bytes_copied / progress.total_bytes) * 100
            bar_length = 30
            filled = int(bar_length * file_percent / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            self.console.print(f"[{bar}] {file_percent:.1f}%")
        
        # Informações gerais
        self.console.print(f"\nArquivos: {len(progress.files_completed)}/{progress.total_files}")
        
        if progress.elapsed_seconds > 0:
            self.console.print(f"Tempo decorrido: {progress.elapsed_seconds:.1f}s")
        
        if progress.estimated_remaining_seconds > 0:
            self.console.print(f"Tempo estimado: {progress.estimated_remaining_seconds:.1f}s")
        
        # Status
        status_colors = {
            CopyStatus.PENDING: "dim",
            CopyStatus.IN_PROGRESS: "cyan",
            CopyStatus.COMPLETED: "green",
            CopyStatus.FAILED: "red",
            CopyStatus.CANCELLED: "yellow"
        }
        
        status_color = status_colors.get(progress.status, "white")
        self.console.print(f"\nStatus: [{status_color}]{progress.status.value}[/{status_color}]")
