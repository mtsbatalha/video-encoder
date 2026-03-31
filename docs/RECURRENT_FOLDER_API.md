# API de Codificação Recorrente

Este documento descreve a API dos componentes de codificação recorrente para desenvolvedores.

---

## Visão Geral

O sistema de codificação recorrente é composto por quatro componentes principais:

1. **RecurrentFolderManager** - Gerenciamento CRUD de configurações
2. **WatchFolderMonitor** - Monitoramento de diretórios
3. **RecurrentMonitorService** - Orquestração de múltiplos monitores
4. **RecurrentHistoryManager** - Histórico e estatísticas

---

## RecurrentFolderManager

**Arquivo:** [`src/managers/recurrent_folder_manager.py`](../src/managers/recurrent_folder_manager.py)

Gerencia as configurações de pastas recorrentes, incluindo validação e persistência.

### Inicialização

```python
from src.managers.recurrent_folder_manager import RecurrentFolderManager
from src.managers.config_manager import ConfigManager
from src.managers.profile_manager import ProfileManager

config_mgr = ConfigManager()
profile_mgr = ProfileManager()
folder_mgr = RecurrentFolderManager(config_mgr, profile_mgr)
```

### Métodos

#### `add_folder(folder_data: Dict[str, Any]) -> str`

Adiciona uma nova pasta recorrente.

**Parâmetros:**
- `folder_data`: Dicionário com dados da pasta
  - `name` (str): Nome descritivo
  - `input_directory` (str): Caminho de entrada
  - `output_directory` (str): Caminho de saída
  - `profile_id` (str): ID do perfil
  - `enabled` (bool, opcional): Status inicial (padrão: True)
  - `options` (dict, opcional): Opções de configuração

**Retorna:** ID da pasta criada (str)

**Exceções:** `ValueError` se dados inválidos

**Exemplo:**
```python
folder_data = {
    "name": "Minha Pasta",
    "input_directory": "C:/Input",
    "output_directory": "D:/Output",
    "profile_id": "profile-uuid",
    "options": {
        "preserve_subdirectories": True,
        "skip_existing_output": True
    }
}
folder_id = folder_mgr.add_folder(folder_data)
```

---

#### `remove_folder(folder_id: str) -> bool`

Remove uma pasta recorrente.

**Parâmetros:**
- `folder_id`: ID da pasta a remover

**Retorna:** True se removido com sucesso

**Exemplo:**
```python
success = folder_mgr.remove_folder("folder-uuid")
```

---

#### `update_folder(folder_id: str, updates: Dict[str, Any]) -> bool`

Atualiza uma pasta existente.

**Parâmetros:**
- `folder_id`: ID da pasta
- `updates`: Dicionário com campos a atualizar

**Retorna:** True se atualizado com sucesso

**Exemplo:**
```python
folder_mgr.update_folder("folder-uuid", {
    "enabled": False,
    "name": "Novo Nome"
})
```

---

#### `list_folders() -> List[Dict[str, Any]]`

Lista todas as pastas recorrentes.

**Retorna:** Lista de dicionários com dados das pastas

**Exemplo:**
```python
folders = folder_mgr.list_folders()
for folder in folders:
    print(f"{folder['name']}: {folder['input_directory']}")
```

---

#### `get_folder(folder_id: str) -> Optional[Dict[str, Any]]`

Obtém uma pasta específica por ID.

**Parâmetros:**
- `folder_id`: ID da pasta

**Retorna:** Dicionário com dados da pasta ou None

**Exemplo:**
```python
folder = folder_mgr.get_folder("folder-uuid")
if folder:
    print(f"Perfil: {folder['profile_id']}")
```

---

#### `enable_folder(folder_id: str) -> bool`

Habilita uma pasta recorrente.

**Parâmetros:**
- `folder_id`: ID da pasta

**Retorna:** True se habilitado com sucesso

---

#### `disable_folder(folder_id: str) -> bool`

Desabilita uma pasta recorrente.

**Parâmetros:**
- `folder_id`: ID da pasta

**Retorna:** True se desabilitado com sucesso

---

#### `get_enabled_folders() -> List[Dict[str, Any]]`

Retorna apenas as pastas habilitadas.

**Retorna:** Lista de pastas habilitadas

---

#### `get_folder_status(folder_id: str) -> Optional[Dict[str, Any]]`

Obtém status detalhado de uma pasta.

**Parâmetros:**
- `folder_id`: ID da pasta

**Retorna:** Dicionário com informações de status

---

## WatchFolderMonitor

**Arquivo:** [`src/core/watch_folder_monitor.py`](../src/core/watch_folder_monitor.py)

Monitora um diretório específico e detecta novos arquivos para processamento.

### Inicialização

```python
from src.core.watch_folder_monitor import WatchFolderMonitor

config = {
    'path': 'C:/Input',
    'output_path': 'D:/Output',
    'profile_id': 'profile-uuid',
    'folder_id': 'folder-uuid',
    'interval': 10,  # segundos entre verificações
    'min_size': 10 * 1024 * 1024,  # 10MB
    'skip_existing_output': True,
    'extensions': ['.mp4', '.mkv', '.avi'],
    'debounce_time': 5,  # segundos
    'enabled': True,
    'priority': 'normal'
}

monitor = WatchFolderMonitor(
    config=config,
    queue_manager=queue_manager,
    job_manager=job_manager,
    profile_manager=profile_manager,
    history_manager=history_manager
)
```

### Métodos

#### `start() -> None`

Inicia o monitoramento da pasta.

**Exemplo:**
```python
monitor.start()
```

---

#### `stop() -> None`

Para o monitoramento da pasta.

**Exemplo:**
```python
monitor.stop()
```

---

#### `is_running() -> bool`

Verifica se o monitor está em execução.

**Retorna:** True se estiver rodando

---

### Configurações do Monitor

| Chave | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `path` | str | - | Caminho da pasta de entrada |
| `output_path` | str | - | Caminho da pasta de saída |
| `profile_id` | str | - | ID do perfil de codificação |
| `folder_id` | str | - | ID da pasta recorrente |
| `interval` | int | 10 | Intervalo entre verificações (segundos) |
| `min_size` | int | 10MB | Tamanho mínimo do arquivo (bytes) |
| `skip_existing_output` | bool | True | Pular arquivos já codificados |
| `extensions` | list | [.mp4, .mkv, ...] | Extensões suportadas |
| `debounce_time` | int | 5 | Tempo para verificar se arquivo está completo |
| `enabled` | bool | True | Monitor habilitado |
| `priority` | str | 'normal' | Prioridade do job (low/normal/high/critical) |

---

## RecurrentMonitorService

**Arquivo:** [`src/services/recurrent_monitor_service.py`](../src/services/recurrent_monitor_service.py)

Orquestra múltiplos monitores de pasta.

### Inicialização

```python
from src.services.recurrent_monitor_service import RecurrentMonitorService

service = RecurrentMonitorService(
    config_manager=config_manager,
    queue_manager=queue_manager,
    job_manager=job_manager,
    profile_manager=profile_manager,
    history_manager=history_manager
)
```

### Métodos

#### `start_all_monitors() -> Dict[str, WatchFolderMonitor]`

Inicia todos os monitores configurados.

**Retorna:** Dicionário com monitores iniciados (chave: folder_id)

**Exemplo:**
```python
monitors = service.start_all_monitors()
print(f"Monitores iniciados: {len(monitors)}")
```

---

#### `stop_all_monitors() -> None`

Para todos os monitores ativos.

**Exemplo:**
```python
service.stop_all_monitors()
```

---

#### `start_monitor(folder_id: str) -> bool`

Inicia um monitor específico.

**Parâmetros:**
- `folder_id`: ID da pasta

**Retorna:** True se iniciado com sucesso

---

#### `stop_monitor(folder_id: str) -> bool`

Para um monitor específico.

**Parâmetros:**
- `folder_id`: ID da pasta

**Retorna:** True se parado com sucesso

---

#### `get_status() -> Dict[str, Any]`

Retorna status de todos os monitores.

**Retorna:**
```python
{
    'total_monitors': 2,
    'active_monitors': {
        'folder-uuid-1': {
            'folder_id': 'folder-uuid-1',
            'is_running': True,
            'source_path': 'C:/Input1',
            'destination_path': 'D:/Output1',
            'last_event_time': '2026-03-31T00:00:00Z',
            'processed_files': 5,
            'errors_count': 0
        }
    },
    'monitor_count': 2
}
```

---

#### `graceful_shutdown() -> None`

Realiza desligamento gracioso de todos os monitores.

**Exemplo:**
```python
import atexit
atexit.register(service.graceful_shutdown)
```

---

## RecurrentHistoryManager

**Arquivo:** [`src/managers/recurrent_history_manager.py`](../src/managers/recurrent_history_manager.py)

Gerencia histórico e estatísticas de processamento.

### Inicialização

```python
from src.managers.recurrent_history_manager import RecurrentHistoryManager

history_mgr = RecurrentHistoryManager(history_file_path="history.json")
```

### Métodos

#### `add_entry(folder_id, input_path, output_path, status, started_at, completed_at, error_message=None) -> str`

Adiciona entrada de histórico.

**Parâmetros:**
- `folder_id` (str): ID da pasta recorrente
- `input_path` (str): Caminho do arquivo de entrada
- `output_path` (str): Caminho do arquivo de saída
- `status` (str): 'completed' ou 'failed'
- `started_at` (datetime): Início do processamento
- `completed_at` (datetime): Conclusão do processamento
- `error_message` (str, opcional): Mensagem de erro

**Retorna:** ID da entrada criada

**Exemplo:**
```python
from datetime import datetime

entry_id = history_mgr.add_entry(
    folder_id="folder-uuid",
    input_path="C:/Input/video.mkv",
    output_path="D:/Output/video.mp4",
    status="completed",
    started_at=datetime.now(),
    completed_at=datetime.now()
)
```

---

#### `get_history(folder_id: str) -> List[Dict[str, Any]]`

Retorna histórico de uma pasta.

**Parâmetros:**
- `folder_id`: ID da pasta

**Retorna:** Lista de entradas de histórico

---

#### `get_stats(folder_id: str) -> Dict[str, Any]`

Retorna estatísticas de uma pasta.

**Retorna:**
```python
{
    'total_processed': 10,
    'success_count': 9,
    'failed_count': 1,
    'total_duration': 3600.5,  # segundos
    'average_duration': 360.05,  # segundos
    'last_processed_at': '2026-03-31T00:00:00Z'
}
```

---

#### `get_recent_entries(folder_id: str, limit: int = 10) -> List[Dict[str, Any]]`

Retorna entradas recentes.

**Parâmetros:**
- `folder_id`: ID da pasta
- `limit`: Número máximo de entradas (padrão: 10)

**Retorna:** Lista ordenada por data (mais recentes primeiro)

---

#### `clear_history(folder_id: str) -> bool`

Limpa histórico de uma pasta.

**Parâmetros:**
- `folder_id`: ID da pasta

**Retorna:** True se limpo com sucesso

---

#### `get_all_stats() -> Dict[str, Dict[str, Any]]`

Retorna estatísticas de todas as pastas.

**Retorna:** Dicionário com estatísticas por pasta

---

#### `get_total_stats() -> Dict[str, Any]`

Retorna estatísticas gerais de todos os processamentos.

---

## Estrutura de Dados

### Configuração de Pasta Recorrente

```json
{
  "id": "uuid-v4",
  "name": "Nome Descritivo",
  "input_directory": "C:/Path/To/Input",
  "output_directory": "C:/Path/To/Output",
  "profile_id": "profile-uuid",
  "profile_name": "HEVC NVENC CQ20",
  "enabled": true,
  "created_at": "2026-03-31T00:00:00Z",
  "last_run": null,
  "total_processed": 0,
  "options": {
    "preserve_subdirectories": true,
    "delete_source_after_encode": false,
    "copy_subtitles": true,
    "supported_extensions": [".mp4", ".mkv", ".avi"],
    "min_file_size_mb": 0,
    "skip_existing_output": true
  }
}
```

### Entrada de Histórico

```json
{
  "id": "entry-uuid",
  "folder_id": "folder-uuid",
  "input_path": "C:/Input/video.mkv",
  "output_path": "D:/Output/video.mp4",
  "status": "completed",
  "started_at": "2026-03-31T00:00:00Z",
  "completed_at": "2026-03-31T00:10:00Z",
  "duration_seconds": 600.0,
  "error_message": null
}
```

---

## Exemplo de Uso Completo

```python
from src.managers.config_manager import ConfigManager
from src.managers.profile_manager import ProfileManager
from src.managers.recurrent_folder_manager import RecurrentFolderManager
from src.services.recurrent_monitor_service import RecurrentMonitorService
from src.managers.queue_manager import QueueManager
from src.managers.job_manager import JobManager
from src.managers.recurrent_history_manager import RecurrentHistoryManager

# Inicializar gerenciadores
config_mgr = ConfigManager()
profile_mgr = ProfileManager()
queue_mgr = QueueManager()
job_mgr = JobManager()
history_mgr = RecurrentHistoryManager()

# Criar gerenciador de pastas
folder_mgr = RecurrentFolderManager(config_mgr, profile_mgr)

# Adicionar pasta recorrente
folder_data = {
    "name": "Downloads",
    "input_directory": "C:/Downloads",
    "output_directory": "D:/Videos",
    "profile_id": "nvidia-1080p-hevc",
    "options": {
        "preserve_subdirectories": True,
        "skip_existing_output": True
    }
}
folder_id = folder_mgr.add_folder(folder_data)
print(f"Pasta adicionada: {folder_id}")

# Criar serviço de monitoramento
service = RecurrentMonitorService(
    config_manager=config_mgr,
    queue_manager=queue_mgr,
    job_manager=job_mgr,
    profile_manager=profile_mgr,
    history_manager=history_mgr
)

# Iniciar todos os monitores
monitors = service.start_all_monitors()
print(f"Monitores ativos: {len(monitors)}")

# Verificar status
status = service.get_status()
print(f"Status: {status}")

# Parar monitores quando necessário
service.stop_all_monitors()
```

---

## Thread Safety

- **RecurrentHistoryManager:** Usa `threading.RLock` para operações de leitura/escrita
- **WatchFolderMonitor:** Executa em thread separada
- **RecurrentMonitorService:** Gerencia múltiplas threads de monitores

---

## Tratamento de Erros

Todos os componentes lançam exceções Python padrão:

- `ValueError`: Dados inválidos
- `RuntimeError`: Erros de operação
- `FileNotFoundError`: Caminhos não encontrados
- `PermissionError`: Erros de permissão

**Exemplo:**
```python
try:
    folder_mgr.add_folder({"name": "Test"})  # Dados incompletos
except ValueError as e:
    print(f"Erro de validação: {e}")
```

---

## Integração com CLI

Para usar via linha de comando:

```bash
# Menu interativo
python vigia_nvenc.py --interactive

# Via código Python
from src.cli import VideoEncoderCLI
cli = VideoEncoderCLI()
cli.run_interactive_mode()
```
