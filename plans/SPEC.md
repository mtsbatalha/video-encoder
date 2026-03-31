# Especificação Técnica: Codificação de Pasta Única vs Recorrente

## Visão Geral

Esta especificação descreve a implementação de duas modalidades de codificação de pasta no menu principal:

1. **Codificação Única (One-Time)**: Funcionalidade existente que processa uma pasta uma única vez
2. **Codificação Recorrente (Recurrent)**: Nova funcionalidade que monitora continuamente um diretório de entrada e processa automaticamente novos conteúdos

## 1. Arquitetura do Sistema

### 1.1 Fluxo Atual (Codificação Única)

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Menu Principal │────▶│  run_folder_     │────▶│  FileUtils.     │
│  (Opção 1)      │     │  conversion_cli  │     │  find_video_files│
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Process Queue  │◀────│  Queue Manager   │◀────│  Job Manager    │
│  CLI            │     │  (add_to_queue)  │     │  (create_job)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### 1.2 Novo Fluxo (Codificação Recorrente)

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Menu Principal │────▶│  run_recurrent_  │────▶│  ConfigManager  │
│  (Opção 2)      │     │  folder_setup    │     │  (save_config)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Watch Folder   │◀────│  Monitor Service │◀────│  Recurrent Config│
│  Encoder        │     │  (file_watcher)  │     │  (loaded)       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## 2. Estrutura de Dados

### 2.1 Configuração de Pasta Recorrente

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
    "supported_extensions": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpeg", ".mpg"],
    "min_file_size_mb": 0,
    "skip_existing_output": true
  }
}
```

### 2.2 Configuração no ConfigManager

A configuração será armazenada no `config.json` sob a chave `directories.recurrent_folders`:

```json
{
  "directories": {
    "watch_folders": [...],
    "recurrent_folders": [
      {
        "id": "uuid-1",
        "name": "Filmes 4K",
        "input_directory": "D:/Downloads/Filmes",
        "output_directory": "E:/Media/Filmes_Encoded",
        "profile_id": "profile-123",
        "enabled": true,
        "options": { ... }
      }
    ]
  }
}
```

## 3. Componentes do Sistema

### 3.1 WatchFolderMonitor (Novo)

Classe responsável por monitorar diretórios em busca de novos arquivos.

**Responsabilidades:**
- Monitorar diretório de entrada usando `watchdog` ou polling
- Detectar novos arquivos de vídeo
- Verificar se arquivo já foi processado (skip_existing_output)
- Disparar encoding quando novo arquivo é detectado
- Gerenciar estado de cada arquivo (pending, processing, completed, failed)

**Métodos principais:**
```python
class WatchFolderMonitor:
    def __init__(self, config: Dict[str, Any])
    def start(self) -> None
    def stop(self) -> None
    def _on_file_created(self, event: FileCreatedEvent) -> None
    def _should_process_file(self, path: Path) -> bool
    def _enqueue_file(self, path: Path) -> None
```

### 3.2 RecurrentFolderManager (Novo)

Gerenciador central para operações de pastas recorrentes.

**Responsabilidades:**
- CRUD de configurações recorrentes
- Iniciar/parar monitores
- Listar status de todas as pastas recorrentes
- Exportar/importar configurações

**Métodos principais:**
```python
class RecurrentFolderManager:
    def __init__(self, config_manager: ConfigManager)
    def add_folder(self, folder: Dict[str, Any]) -> bool
    def remove_folder(self, folder_id: str) -> bool
    def update_folder(self, folder_id: str, updates: Dict[str, Any]) -> bool
    def list_folders(self) -> List[Dict[str, Any]]
    def get_folder(self, folder_id: str) -> Optional[Dict[str, Any]]
    def enable_folder(self, folder_id: str) -> bool
    def disable_folder(self, folder_id: str) -> bool
    def start_all_monitors(self) -> None
    def stop_all_monitors(self) -> None
```

### 3.3 Modificações no Menu Principal

O menu principal será modificado para oferecer duas opções distintas:

```
Menu Principal
├── 1. Codificação de Pasta
│   ├── 1.1. Codificação Única (manual)
│   └── 1.2. Codificação Recorrente (automática)
├── 2. Codificar arquivo único
├── 3. Ver fila de jobs
├── 4. Gerenciar Perfis
├── 5. Ver estatísticas
├── 6. Gerenciar Conversões Recorrentes  ← NOVO
└── 7. Sair
```

### 3.4 Menu de Gerenciamento de Conversões Recorrentes

```
Gerenciar Conversões Recorrentes
├── 1. Listar pastas recorrentes
├── 2. Adicionar nova pasta recorrente
├── 3. Remover pasta recorrente
├── 4. Editar pasta recorrente
├── 5. Ativar/Desativar pasta
├── 6. Iniciar todos monitores
├── 7. Parar todos monitores
├── 8. Ver histórico de processamento
└── 0. Voltar
```

## 4. API Endpoints (Estrutura Interna)

### 4.1 Operações do RecurrentFolderManager

| Operação | Método | Descrição |
|----------|--------|-----------|
| Listar | `list_folders()` | Retorna todas as pastas recorrentes |
| Adicionar | `add_folder(folder_data)` | Adiciona nova configuração |
| Remover | `remove_folder(folder_id)` | Remove configuração por ID |
| Atualizar | `update_folder(folder_id, updates)` | Atualiza configuração existente |
| Ativar | `enable_folder(folder_id)` | Marca pasta como enabled=true |
| Desativar | `disable_folder(folder_id)` | Marca pasta como enabled=false |
| Iniciar | `start_monitor(folder_id)` | Inicia monitor para pasta específica |
| Parar | `stop_monitor(folder_id)` | Para monitor para pasta específica |

## 5. Fluxo de Processamento Recorrente

```
1. Usuário configura pasta recorrente via menu
2. Configuração é salva no config.json
3. Usuário inicia monitores (opção no menu ou auto-start)
4. WatchFolderMonitor detecta novo arquivo
5. Verifica se arquivo deve ser processado:
   - Extensão suportada?
   - Tamanho mínimo atingido?
   - Arquivo já existe no output?
6. Se válido, cria job no QueueManager
7. EncoderEngine processa job
8. Atualiza estatísticas e histórico
9. (Opcional) Remove arquivo de entrada se configurado
```

## 6. Considerações de Implementação

### 6.1 Dependências

- `watchdog`: Biblioteca para monitoramento de filesystem
- Manter compatibilidade com `psutil` para monitoramento de recursos

### 6.2 Persistência de Estado

- Estado dos monitores deve ser persistido para recuperação após restart
- Histórico de processamento deve ser mantido (JSON ou SQLite leve)

### 6.3 Tratamento de Erros

- Re-tentativa automática para falhas temporárias
- Log detalhado de erros por arquivo
- Notificação opcional via webhook/email em caso de falha

### 6.4 Performance

- Polling interval configurável (default: 5 segundos)
- Limite de arquivos processados simultaneamente
- Debounce para arquivos sendo copiados (esperar arquivo estar completo)

## 7. Interface com Componentes Existentes

### 7.1 ConfigManager

```python
# Adicionar métodos para recurrent_folders
config.get_recurrent_folders() -> List[Dict]
config.add_recurrent_folder(folder: Dict) -> bool
config.remove_recurrent_folder(index: int) -> bool
config.set_recurrent_folders(folders: List[Dict]) -> bool
```

### 7.2 QueueManager

```python
# Reutilizar métodos existentes
queue_mgr.add_to_queue(job_id, input_path, output_path, profile)
queue_mgr.get_queue_length()
```

### 7.3 JobManager

```python
# Reutilizar métodos existentes
job_mgr.create_job(input_path, output_path, profile_id, profile_name)
job_mgr.update_job_status(job_id, status)
job_mgr.update_progress(job_id, progress)
```

## 8. Diagrama de Sequência

```
┌─────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│  User   │     │  RecurrentUI │     │RecurrentMgr   │     │WatchMonitor  │
└────┬────┘     └──────┬───────┘     └───────┬───────┘     └──────┬───────┘
     │                 │                     │                    │
     │ Add Folder      │                     │                    │
     │────────────────▶│                     │                    │
     │                 │ save_folder()       │                    │
     │                 │────────────────────▶│                    │
     │                 │                     │  save to config    │
     │                 │                     │───────────────────▶│
     │                 │                     │                    │
     │ Start Monitors  │                     │                    │
     │────────────────▶│                     │                    │
     │                 │ start_all()         │                    │
     │                 │────────────────────▶│                    │
     │                 │                     │ start()            │
     │                 │                     │───────────────────▶│
     │                 │                     │                    │
     │                 │                     │  File Detected     │
     │                 │                     │◀───────────────────│
     │                 │                     │                    │
     │                 │                     │ create_job()       │
     │                 │                     │───────────────────▶│
     │                 │                     │  queue_mgr.add()   │
     │                 │                     │───────────────────▶│
     │                 │                     │                    │
```

## 9. Critérios de Aceitação

- [ ] Menu principal exibe opções separadas para codificação única e recorrente
- [ ] Configurações recorrentes são salvas e persistidas
- [ ] Sistema detecta automaticamente novos arquivos no diretório de entrada
- [ ] Arquivos são processados com o perfil configurado
- [ ] Menu de gerenciamento permite CRUD completo de pastas recorrentes
- [ ] Monitores podem ser iniciados/parados individualmente ou em grupo
- [ ] Histórico de processamento é mantido e visualizável
- [ ] Sistema lida gracefulmente com erros e reinicializações
