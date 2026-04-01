# Especificação Técnica: Suporte a Diretório Remoto

## Visão Geral

Esta especificação descreve a implementação de suporte a diretórios remotos para o video-encoder. Quando o usuário especificar um diretório de entrada, haverá uma opção para indicar se é um diretório local ou remoto. No caso de diretório remoto, os arquivos serão copiados para um diretório temporário local antes da conversão.

## 1. Requisitos Funcionais

### 1.1 Seleção do Tipo de Diretório
- **RF001**: O sistema deve perguntar ao usuário se o diretório de entrada é local ou remoto
- **RF002**: Para diretórios remotos, o sistema deve suportar os seguintes protocolos:
  - **SSHFS**: Filesystem sobre SSH (Linux/Windows)
  - **SMB/CIFS**: Compartilhamento Windows/Samba
  - **NFS**: Network File System (Linux/Unix)
  - **Rclone/Mounted**: Diretórios montados via rclone ou outros mount points
  - **UNC Path**: Caminho de rede Windows

### 1.2 Cópia para Diretório Temporário
- **RF003**: Arquivos remotos devem ser copiados para um diretório temporário local antes da conversão
- **RF004**: O diretório temporário deve ser criado automaticamente
- **RF005**: Após cópia bem-sucedida, a conversão deve iniciar automaticamente
- **RF006**: Opcionalmente, arquivos temporários podem ser removidos após a conversão

### 1.3 Configuração de Conexão Remota
- **RF007**: O sistema deve permitir salvar configurações de conexões remotas frequentes
- **RF008**: Suporte a autenticação por senha e chave SSH

## 2. Arquitetura do Sistema

### 2.1 Componentes Principais

```
┌─────────────────────────────────────────────────────────────────┐
│                         UI Layer                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Menu de Seleção: Local vs Remoto                       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RemoteDirectoryManager                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌────────────┐ │
│  │  SSHFS       │ │  SMB/CIFS    │ │  NFS     │ │  Mounted   │ │
│  │  Client      │ │  Client      │ │  Client  │ │  (rclone)  │ │
│  └──────────────┘ └──────────────┘ └──────────┘ └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TempDirectoryManager                         │
│  - Cria diretório temporário                                    │
│  - Gerencia cleanup                                             │
│  - Valida espaço em disco                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Conversion Flow (Existente)                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Fluxo de Processamento

```mermaid
flowchart TD
    A[Usuário especifica diretório] --> B{É diretório remoto?}
    B -->|Não| C[Usa diretório local diretamente]
    B -->|Sim| D[Identificar protocolo]
    
    D --> E{Protocolo}
    E -->|SSHFS| F[Montar via SSHFS]
    E -->|SMB/CIFS| G[Montar share SMB]
    E -->|NFS| H[Montar via NFS]
    E -->|Mounted|rclone| I[Acessar diretório montado]
    E -->|UNC| J[Acessar via UNC]
    
    F --> K[Copiar arquivos para temp]
    G --> K
    H --> K
    I --> K
    J --> K
    
    K --> L{Cópia bem sucedida?}
    L -->|Sim| M[Iniciar conversão]
    L -->|Não| N[Exibir erro e abortar]
    
    M --> O{Remover temp após conversão?}
    O -->|Sim| P[Remover diretório temporário]
    O -->|Não| Q[Manter arquivos temp]
    
    C --> R[Fluxo normal de conversão]
    P --> S[Concluir]
    Q --> S
    R --> S
```

## 3. Estrutura de Dados

### 3.1 Configuração de Conexão Remota

```json
{
  "remote_connections": {
    "saved_connections": [
      {
        "id": "uuid-v4",
        "name": "Servidor SSHFS",
        "protocol": "sshfs",
        "host": "192.168.1.100",
        "port": 22,
        "username": "usuario",
        "auth_type": "password",
        "password": null,
        "private_key_path": null,
        "mount_point": null,
        "default_path": "/home/usuario/videos",
        "created_at": "2026-04-01T00:00:00Z"
      },
      {
        "id": "uuid-v4",
        "name": "Servidor SMB",
        "protocol": "smb",
        "host": "//servidor/share",
        "port": 445,
        "username": "usuario",
        "auth_type": "password",
        "password": null,
        "mount_point": null,
        "default_path": "/videos",
        "created_at": "2026-04-01T00:00:00Z"
      },
      {
        "id": "uuid-v4",
        "name": "NFS Server",
        "protocol": "nfs",
        "host": "192.168.1.200",
        "port": 2049,
        "export_path": "/exports/videos",
        "mount_point": null,
        "default_path": "/",
        "created_at": "2026-04-01T00:00:00Z"
      },
      {
        "id": "uuid-v4",
        "name": "Google Drive via rclone",
        "protocol": "mounted",
        "mount_type": "rclone",
        "remote_name": "gdrive",
        "mount_point": "X:",
        "default_path": "/videos",
        "created_at": "2026-04-01T00:00:00Z"
      }
    ]
  }
}
```

### 3.2 Configuração de Diretório Temporário

```json
{
  "directories": {
    "temp_base": "C:\\temp\\video-encoder",
    "auto_cleanup": true,
    "min_disk_space_gb": 50
  }
}
```

## 4. Classes e Interfaces

### 4.1 RemoteDirectoryManager

```python
class RemoteDirectoryManager:
    """Gerenciador central para operações com diretórios remotos."""
    
    def __init__(self, config_manager: ConfigManager)
    
    def is_remote_path(self, path: str) -> bool:
        """Verifica se o caminho é remoto."""
    
    def get_protocol(self, path: str) -> Optional[str]:
        """Identifica o protocolo do caminho remoto."""
    
    def copy_to_temp(
        self, 
        remote_path: str, 
        temp_dir: str,
        extensions: List[str] = None,
        progress_callback: Callable = None
    ) -> Tuple[bool, List[str], str]:
        """
        Copia arquivos do diretório remoto para temporário local.
        
        Returns:
            Tuple com (sucesso, lista_de_arquivos_copiados, mensagem_erro)
        """
    
    def test_connection(self, connection_config: Dict) -> Tuple[bool, str]:
        """Testa conexão remota e retorna (sucesso, mensagem)."""
```

### 4.2 RemoteConnection Protocols

```python
class RemoteProtocol(ABC):
    """Interface base para protocolos remotos."""
    
    @abstractmethod
    def connect(self, config: Dict) -> bool:
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        pass
    
    @abstractmethod
    def list_files(self, path: str, extensions: List[str]) -> List[str]:
        pass
    
    @abstractmethod
    def copy_file(self, remote_path: str, local_path: str, callback: Callable) -> bool:
        pass
    
    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        pass


class SSHFSClient(RemoteProtocol):
    """Cliente SSHFS para filesystem sobre SSH."""
    
    def __init__(self)
    def connect(self, config: Dict) -> bool  # host, port, username, password/private_key
    def disconnect(self) -> None
    def list_files(self, path: str, extensions: List[str]) -> List[str]
    def copy_file(self, remote_path: str, local_path: str, callback: Callable) -> bool
    def test_connection(self) -> Tuple[bool, str]


class SMBClient(RemoteProtocol):
    """Cliente SMB para shares Windows/Samba."""
    
    def __init__(self)
    def connect(self, config: Dict) -> bool  # host, share, username, password
    def disconnect(self) -> None
    def list_files(self, path: str, extensions: List[str]) -> List[str]
    def copy_file(self, remote_path: str, local_path: str, callback: Callable) -> bool
    def test_connection(self) -> Tuple[bool, str]


class NFSClient(RemoteProtocol):
    """Cliente NFS para Network File System."""
    
    def __init__(self)
    def connect(self, config: Dict) -> bool  # host, export_path
    def disconnect(self) -> None
    def list_files(self, path: str, extensions: List[str]) -> List[str]
    def copy_file(self, remote_path: str, local_path: str, callback: Callable) -> bool
    def test_connection(self) -> Tuple[bool, str]


class MountedClient(RemoteProtocol):
    """Cliente para diretórios montados (rclone, etc.)."""
    
    def __init__(self)
    def connect(self, config: Dict) -> bool  # Verifica se mount point existe
    def disconnect(self) -> None
    def list_files(self, path: str, extensions: List[str]) -> List[str]
    def copy_file(self, remote_path: str, local_path: str, callback: Callable) -> bool
    def test_connection(self) -> Tuple[bool, str]  # Verifica se diretório montado está acessível


class UNCClient(RemoteProtocol):
    """Cliente para caminhos UNC Windows."""
    
    def __init__(self)
    def connect(self, config: Dict) -> bool
    def disconnect(self) -> None
    def list_files(self, path: str, extensions: List[str]) -> List[str]
    def copy_file(self, remote_path: str, local_path: str, callback: Callable) -> bool
    def test_connection(self) -> Tuple[bool, str]
```

### 4.3 TempDirectoryManager

```python
class TempDirectoryManager:
    """Gerenciador de diretórios temporários."""
    
    def __init__(self, base_temp_dir: Optional[str] = None)
    
    def create_temp_directory(self, prefix: str = "video_encoder_") -> str:
        """Cria diretório temporário e retorna caminho."""
    
    def get_available_space(self, path: str) -> int:
        """Retorna espaço disponível em bytes."""
    
    def check_disk_space(self, path: str, required_gb: int) -> bool:
        """Verifica se há espaço em disco suficiente."""
    
    def cleanup(self, temp_dir: str) -> bool:
        """Remove diretório temporário e seus conteúdos."""
    
    def cleanup_old_directories(self, max_age_hours: int = 24) -> int:
        """Remove diretórios temporários antigos."""
```

## 5. Interface do Usuário

### 5.1 Fluxo de Seleção

```
┌─────────────────────────────────────────────────────────────┐
│  Especificação do Diretório de Entrada                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  O diretório de entrada é:                                  │
│                                                             │
│  [1] 📁 Local (neste computador)                            │
│  [2] 🌐 Remoto (servidor, share de rede, etc.)              │
│                                                             │
│  Escolha uma opção: _                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Seleção de Protocolo Remoto

```
┌─────────────────────────────────────────────────────────────┐
│  Tipo de Conexão Remota                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Selecione o protocolo:                                     │
│                                                             │
│  [1] 🔐 SSHFS (Filesystem sobre SSH)                        │
│  [2] 📁 SMB/CIFS (Windows Share/Samba)                      │
│  [3] 📡 NFS (Network File System)                           │
│  [4] 💾 Montado (rclone, etc.)                              │
│  [5] 📡 UNC Path (Caminho de Rede Windows)                  │
│  [6] 💾 Usar conexão salva                                  │
│  [0] ⬅ Voltar                                               │
│                                                             │
│  Escolha uma opção: _                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Configuração de Conexão SSH/SFTP

```
┌─────────────────────────────────────────────────────────────┐
│  Configurar Conexão SSH/SFTP                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Host/Endereço: _                                           │
│  Porta [22]: _                                              │
│  Usuário: _                                                 │
│                                                             │
│  Tipo de Autenticação:                                      │
│  [1] Senha                                                  │
│  [2] Chave SSH                                              │
│                                                             │
│  Senha: _                                                   │
│  OU                                                         │
│  Caminho da Chave Privada: _                                │
│                                                             │
│  Caminho Padrão (opcional): _                               │
│                                                             │
│  [Testar Conexão]  [Salvar Conexão]  [Cancelar]             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.4 Progresso de Cópia

```
┌─────────────────────────────────────────────────────────────┐
│  Copiando Arquivos Remotos                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📥 arquivo_video.mp4                                       │
│  ████████████████████████░░░░░░ 65% - 1.2 GB / 2.0 GB       │
│                                                             │
│  Arquivos: 3/10                                             │
│  Tempo restante: ~15 minutos                                │
│  Diretório temporário: C:\temp\video_encoder_abc123         │
│                                                             │
│  [Cancelar]                                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 6. Dependências

### 6.1 Bibliotecas Python

| Biblioteca | Versão | Finalidade |
|------------|--------|------------|
| paramiko | >=3.0.0 | Cliente SSH/SFTP |
| smbprotocol | >=1.9.0 | Cliente SMB/CIFS |
| requests | >=2.28.0 | Cliente HTTP |
| pysmb | >=1.2.6 | Alternativa SMB |
| sshfs | >=2023.0.0 | Cliente SSHFS (opcional) |
| nfs3 | >=1.0.0 | Cliente NFS |

### 6.2 Instalação

```bash
pip install paramiko smbprotocol requests pysmb sshfs nfs3
```

### 6.3 Dependências de Sistema

| Sistema | Pacote | Finalidade |
|---------|--------|------------|
| Windows | WinFsp | Suporte a filesystems (SSHFS) |
| Linux | nfs-common | Suporte NFS |
| Linux | sshfs | Pacote sshfs |
| Todos | rclone | Mount de drives remotos (opcional) |

## 7. Tratamento de Erros

### 7.1 Erros de Conexão

| Erro | Ação |
|------|------|
| Timeout | Re-tentar 3 vezes com backoff exponencial |
| Autenticação falhou | Exibir mensagem clara e permitir nova tentativa |
| Host não encontrado | Exibir erro e abortar |
| Permissão negada | Exibir erro e abortar |

### 7.2 Erros de Cópia

| Erro | Ação |
|------|------|
| Espaço em disco insuficiente | Abortar e limpar temp |
| Arquivo corrompido | Re-tentar download |
| Conexão interrompida | Re-tentar do ponto de falha (resume) |

## 8. Critérios de Aceitação

- [ ] UI pergunta se diretório é local ou remoto
- [ ] Suporte a pelo menos SSH/SFTP e SMB/CIFS
- [ ] Cópia para diretório temporário funciona corretamente
- [ ] Conversão inicia após cópia bem-sucedida
- [ ] Opção de remover arquivos temporários após conversão
- [ ] Progresso de cópia é exibido ao usuário
- [ ] Tratamento de erros adequado
- [ ] Testes de integração passam

## 9. Considerações de Segurança

- Senhas nunca devem ser armazenadas em texto puro
- Chaves SSH devem ter permissões adequadas
- Validação de certificados SSL para HTTPS
- Sanitização de caminhos para evitar directory traversal

## 10. Considerações de Performance

- Usar múltiplas threads para downloads paralelos
- Implementar resume de downloads interrompidos
- Buffer otimizado para transferências grandes
- Limite configurável de conexões simultâneas
