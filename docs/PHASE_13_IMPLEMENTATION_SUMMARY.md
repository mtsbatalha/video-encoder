# Phase 13: Suporte a Diretório Remoto - Resumo da Implementação

## Visão Geral

Esta fase implementa suporte a diretórios remotos para o video-encoder, permitindo que usuários especifiquem diretórios de entrada remotos (SSHFS, SMB, NFS, mounts rclone, UNC) que serão copiados para um diretório temporário local antes da conversão.

## Funcionalidades Avançadas Adicionadas

### CopyProgress - Rastreamento de Progresso Detalhado

```python
@dataclass
class CopyProgress:
    status: CopyStatus              # pending, in_progress, completed, failed, cancelled
    current_file: str               # Arquivo atual sendo copiado
    current_file_index: int         # Índice do arquivo atual
    total_files: int                # Total de arquivos
    bytes_copied: int               # Bytes copiados
    total_bytes: int                # Total de bytes
    files_completed: List[str]      # Arquivos já copiados
    files_failed: List[str]         # Arquivos que falharam
    error_message: str              # Mensagem de erro
    started_at: datetime            # Início da cópia
    completed_at: datetime          # Fim da cópia
    
    # Propriedades calculadas
    percent_complete: float         # Porcentagem completa
    elapsed_seconds: float          # Tempo decorrido
    estimated_remaining_seconds: float  # Tempo estimado restante
```

### CopyStatus - Enum de Status

```python
class CopyStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

## Novos Métodos no RemoteDirectoryManager

### Gerenciamento de Progresso e Cancelamento

| Método | Descrição |
|--------|-----------|
| `get_copy_progress()` | Retorna objeto CopyProgress com estado atual |
| `request_cancel()` | Solicita cancelamento da operação |
| `reset_cancel()` | Reseta solicitação de cancelamento |
| `copy_to_temp_with_progress()` | Copia arquivos com progresso detalhado e suporte a cancelamento |

### Informações e Utilitários

| Método | Descrição |
|--------|-----------|
| `get_directory_info()` | Obtém informações detalhadas sobre diretório remoto |
| `download_single_file()` | Baixa um único arquivo remoto |
| `get_saved_connection_by_name()` | Obtém conexão salva por nome |
| `list_saved_connections()` | Lista todas as conexões salvas |
| `add_saved_connection()` | Adiciona nova conexão salva |
| `remove_saved_connection()` | Remove conexão salva por ID |

## Exemplo de Uso com Progresso Detalhado

```python
from src.managers.remote_directory_manager import RemoteDirectoryManager, CopyProgress

# Inicializar
config = ConfigManager()
remote_mgr = RemoteDirectoryManager(config)

# Callback de progresso
def on_progress(progress: CopyProgress):
    print(f"Arquivo: {progress.current_file}")
    print(f"Progresso: {progress.percent_complete:.1f}%")
    print(f"Tempo decorrido: {progress.elapsed_seconds:.1f}s")
    print(f"Tempo estimado restante: {progress.estimated_remaining_seconds:.1f}s")

# Copiar com progresso detalhado
remote_path = "ssh://user@host/path"
connection_config = {'password': 'senha'}

success, files, temp_dir = remote_mgr.copy_to_temp_with_progress(
    files=['/remote/file1.mp4', '/remote/file2.mkv'],
    temp_dir=None,  # Criar novo diretório temporário
    progress_callback=on_progress
)

# Cancelar operação (se necessário)
# remote_mgr.request_cancel()

# Obter progresso atual
progress = remote_mgr.get_copy_progress()
if progress:
    print(f"Status: {progress.status.value}")
    print(f"Arquivos completados: {len(progress.files_completed)}")
    print(f"Arquivos falhados: {len(progress.files_failed)}")
```

## Exemplo: Obter Informações do Diretório

```python
# Obter informações sobre diretório remoto
info = remote_mgr.get_directory_info(
    remote_path="smb://server/share/videos",
    connection_config={'username': 'user', 'password': 'pass'}
)

print(f"Acessível: {info['accessible']}")
print(f"Número de arquivos: {info['file_count']}")
print(f"Arquivos de vídeo: {info['video_files']}")
```

## Exemplo: Download de Arquivo Único

```python
# Baixar arquivo único diretamente
success, msg = remote_mgr.download_single_file(
    remote_path="ssh://user@host/video.mp4",
    local_path="./downloads/video.mp4",
    connection_config={'password': 'senha'},
    progress_callback=lambda copied, total: print(f"{copied}/{total}")
)
```

## Exemplo: Gerenciar Conexões Salvas

```python
# Adicionar conexão salva
connection = {
    'name': 'Meu Servidor',
    'protocol': 'sshfs',
    'host': '192.168.1.100',
    'port': 22,
    'username': 'usuario',
    'password': 'senha123',
    'default_path': '/home/usuario/videos'
}
remote_mgr.add_saved_connection(connection)

# Listar conexões salvas
connections = remote_mgr.list_saved_connections()

# Obter conexão por nome
conn = remote_mgr.get_saved_connection_by_name('Meu Servidor')

# Remover conexão
remote_mgr.remove_saved_connection(conn['id'])
```

## Status da Implementação

| Fase | Status |
|------|--------|
| Fase 1: Estrutura de Configuração | ✅ Concluída |
| Fase 2: Clientes de Protocolo | ✅ Concluída |
| Fase 3: RemoteDirectoryManager | ✅ Concluída |
| Fase 4: Interface do Usuário | ✅ Concluída |
| Fase 5: Integração | ✅ Concluída |
| Fase 6: Testes | ⏳ Pendente |

## Arquivos Criados/Modificados

### Novos Arquivos

#### Utilitários Base
| Arquivo | Descrição |
|---------|-----------|
| [`src/utils/temp_directory_manager.py`](src/utils/temp_directory_manager.py) | Gerenciador de diretórios temporários |
| [`src/utils/remote/__init__.py`](src/utils/remote/__init__.py) | Pacote remote |
| [`src/utils/remote/remote_protocol.py`](src/utils/remote/remote_protocol.py) | Interface base para protocolos |
| [`src/utils/remote/sshfs_client.py`](src/utils/remote/sshfs_client.py) | Cliente SSHFS/SFTP |
| [`src/utils/remote/smb_client.py`](src/utils/remote/smb_client.py) | Cliente SMB/CIFS |
| [`src/utils/remote/nfs_client.py`](src/utils/remote/nfs_client.py) | Cliente NFS |
| [`src/utils/remote/mounted_client.py`](src/utils/remote/mounted_client.py) | Cliente para mounts (rclone) |
| [`src/utils/remote/unc_client.py`](src/utils/remote/unc_client.py) | Cliente UNC Windows |

#### Gerenciadores
| Arquivo | Descrição |
|---------|-----------|
| [`src/managers/remote_directory_manager.py`](src/managers/remote_directory_manager.py) | Gerenciador central de diretórios remotos |

### Arquivos Modificados

| Arquivo | Modificações |
|---------|-------------|
| [`src/managers/config_manager.py`](src/managers/config_manager.py) | Adicionado suporte a `remote_connections`, `temp_base`, `auto_cleanup`, `min_disk_space_gb` |
| [`src/utils/path_utils.py`](src/utils/path_utils.py) | Adicionado `RemoteProtocol` enum, métodos `is_remote_path()`, `get_protocol()`, `parse_remote_path()` |

## Funcionalidades Implementadas

### 1. ConfigManager Atualizado

**Novas configurações no `config.json`:**

```json
{
  "directories": {
    "temp_base": "C:\\temp\\video-encoder",
    "auto_cleanup": true,
    "min_disk_space_gb": 50
  },
  "remote_connections": {
    "saved_connections": [
      {
        "id": "uuid",
        "name": "Servidor SSH",
        "protocol": "sshfs",
        "host": "192.168.1.100",
        "port": 22,
        "username": "usuario",
        "auth_type": "password",
        "default_path": "/home/usuario/videos"
      }
    ]
  }
}
```

**Novos métodos:**
- `get_remote_connections()` - Retorna configurações de conexões remotas
- `get_saved_connections()` - Lista conexões salvas
- `add_saved_connection()` - Adiciona conexão salva
- `remove_saved_connection()` - Remove conexão salva
- `update_saved_connection()` - Atualiza conexão salva
- `get_temp_base()` - Retorna diretório temp base
- `get_auto_cleanup()` - Verifica se auto-cleanup está habilitado
- `get_min_disk_space_gb()` - Retorna espaço mínimo em disco

### 2. PathUtils Atualizado

**Novo Enum:**
```python
class RemoteProtocol(Enum):
    LOCAL = "local"
    SSHFS = "sshfs"
    SMB = "smb"
    NFS = "nfs"
    MOUNTED = "mounted"
    UNC = "unc"
```

**Novos métodos:**
- `is_remote_path(path)` - Verifica se caminho é remoto
- `get_protocol(path)` - Identifica o protocolo
- `parse_remote_path(path)` - Analisa caminho e extrai componentes

### 3. TempDirectoryManager

**Funcionalidades:**
- `create_temp_directory(prefix)` - Cria diretório temporário único
- `get_available_space(path)` - Retorna espaço disponível
- `check_disk_space(required_gb)` - Verifica espaço suficiente
- `cleanup(temp_dir)` - Remove diretório temporário
- `cleanup_old_directories(max_age_hours)` - Remove diretórios antigos
- `get_temp_directories()` - Lista diretórios temporários
- `validate_temp_directory(temp_dir)` - Valida diretório

### 4. Clientes de Protocolo

Todos os clientes implementam a interface `RemoteProtocol`:

```python
class RemoteProtocol(ABC):
    @abstractmethod
    def connect(self, config: Dict) -> bool: pass
    
    @abstractmethod
    def disconnect(self) -> None: pass
    
    @abstractmethod
    def list_files(path: str, extensions: List[str]) -> List[str]: pass
    
    @abstractmethod
    def copy_file(remote_path: str, local_path: str, callback: Callable) -> bool: pass
    
    @abstractmethod
    def test_connection() -> Tuple[bool, str]: pass
```

**SSHFSClient:**
- Usa paramiko para conexão SFTP
- Suporta autenticação por senha e chave SSH
- Listagem recursiva de arquivos
- Copy com callback de progresso

**SMBClient:**
- Usa smbprotocol para acesso a shares Windows/Samba
- Suporta autenticação Windows
- Listagem recursiva
- Copy com chunks de 1MB

**NFSClient:**
- Acessa exports NFS
- Funciona com NFS montado ou via nfs3
- Listagem recursiva
- Copy com callback de progresso

**MountedClient:**
- Para diretórios já montados (rclone, etc.)
- Verifica se mount point existe
- Usa operações nativas do sistema
- Copy eficiente

**UNCClient:**
- Para caminhos UNC Windows (\\server\share)
- Usa operações nativas do Windows
- Tratamento de erros Windows específico
- Copy com callback

### 5. RemoteDirectoryManager

**Funcionalidades principais:**

```python
# Verificar se é caminho remoto
manager.is_remote_path(path)

# Obter protocolo
manager.get_protocol(path)

# Conectar
manager.connect(path, connection_config)

# Listar arquivos
manager.list_files(path)

# Copiar para temp
manager.copy_to_temp(files, temp_dir, progress_callback)

# Copiar diretório inteiro para temp
manager.copy_directory_to_temp(remote_path, connection_config, progress_callback)

# Testar conexão
manager.test_connection(path, connection_config)

# Limpar temp
manager.cleanup_temp(temp_dir)
```

## Protocolos Suportados

| Protocolo | Formato do Path | Biblioteca |
|-----------|----------------|------------|
| SSHFS | `ssh://user@host:port/path` | paramiko |
| SMB | `smb://host/share/path` | smbprotocol |
| NFS | `nfs://host/export/path` | nfs3/os |
| Mounted | `mounted://mount_point/path` | os/pathlib |
| UNC | `\\host\share\path` | os/pathlib |

## Dependências

**Python:**
```
paramiko>=3.0.0
smbprotocol>=1.9.0
```

**Sistema:**
- Windows: WinFsp (para SSHFS)
- Linux: nfs-common, sshfs
- Opcional: rclone

## Funcionalidades Adicionais Implementadas

### CopyProgress - Rastreamento de Progresso Detalhado

A classe `CopyProgress` fornece informações detalhadas sobre o progresso da cópia:

- `status` - Status atual (pending, in_progress, completed, failed, cancelled)
- `current_file` - Arquivo atual sendo copiado
- `current_file_index` - Índice do arquivo atual
- `total_files` - Total de arquivos
- `bytes_copied` - Bytes copiados
- `files_completed` - Lista de arquivos completados
- `files_failed` - Lista de arquivos que falharam
- `percent_complete` - Porcentagem completa
- `elapsed_seconds` - Tempo decorrido
- `estimated_remaining_seconds` - Tempo estimado restante

### Cancelamento de Operações

```python
# Solicitar cancelamento
remote_mgr.request_cancel()

# Resetar cancelamento
remote_mgr.reset_cancel()
```

### Informações do Diretório Remoto

```python
# Obter informações sobre diretório remoto
info = remote_mgr.get_directory_info(
    remote_path="smb://server/share/videos",
    connection_config={'username': 'user', 'password': 'pass'}
)

print(f"Acessível: {info['accessible']}")
print(f"Número de arquivos: {info['file_count']}")
print(f"Arquivos de vídeo: {info['video_files']}")
```

## Fluxo de Uso no Menu Principal

1. **Selecionar Tipo de Diretório**
   - Local: Usa diretório diretamente
   - Remoto: Configura conexão e copia para temp

2. **Selecionar Protocolo Remoto**
   - SSHFS, SMB, NFS, Mounted, UNC
   - Ou usar conexão salva

3. **Configurar Conexão**
   - Host, porta, credenciais
   - Opção de salvar conexão

4. **Testar Conexão** (opcional)

5. **Copiar Arquivos**
   - Progresso exibido em tempo real
   - Suporte a cancelamento

6. **Processar Conversão**
   - Fluxo normal de conversão

7. **Cleanup Automático** (se habilitado)
   - Remove diretório temporário

## Status Final

| Componente | Status |
|------------|--------|
| ConfigManager | ✅ Implementado |
| TempDirectoryManager | ✅ Implementado |
| PathUtils | ✅ Implementado |
| SSHFSClient | ✅ Implementado |
| SMBClient | ✅ Implementado |
| NFSClient | ✅ Implementado |
| MountedClient | ✅ Implementado |
| UNCClient | ✅ Implementado |
| RemoteDirectoryManager | ✅ Implementado |
| RemoteConnectionUI | ✅ Implementado |
| Integração CLI | ✅ Implementado |
| Testes Unitários | ⏳ Pendente |

## Exemplo de Uso

```python
from src.managers.config_manager import ConfigManager
from src.managers.remote_directory_manager import RemoteDirectoryManager

# Inicializar
config = ConfigManager()
remote_mgr = RemoteDirectoryManager(config)

# Caminho remoto
remote_path = "ssh://user@192.168.1.100:22/home/user/videos"

# Configuração de conexão
connection_config = {
    'password': 'senha123',
    # ou 'private_key_path': '/path/to/key'
}

# Opção 1: Copiar diretório inteiro
success, temp_dir, files = remote_mgr.copy_directory_to_temp(
    remote_path, 
    connection_config,
    progress_callback=lambda f, c, t: print(f"{f}: {c}/{t}")
)

if success:
    print(f"Arquivos copiados para: {temp_dir}")
    print(f"Arquivos: {files}")
    
    # ... fazer conversão ...
    
    # Cleanup se habilitado
    if remote_mgr.should_auto_cleanup():
        remote_mgr.cleanup_temp(temp_dir)

# Opção 2: Conectar, listar, copiar manualmente
success, msg = remote_mgr.connect(remote_path, connection_config)
if success:
    files = remote_mgr.list_files()
    success, copied, temp_dir = remote_mgr.copy_to_temp(files)
    remote_mgr.disconnect()
```

## Status da Implementação

| Fase | Status |
|------|--------|
| Fase 1: Estrutura de Configuração | ✅ Concluída |
| Fase 2: Clientes de Protocolo | ✅ Concluída |
| Fase 3: RemoteDirectoryManager | ✅ Concluída |
| Fase 4: Interface do Usuário | ⏳ Pendente |
| Fase 5: Integração | ⏳ Pendente |
| Fase 6: Testes | ⏳ Pendente |
