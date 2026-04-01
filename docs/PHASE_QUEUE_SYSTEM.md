# PHASE_QUEUE_SYSTEM - Sistema Unificado de Gerenciamento de Fila

## Visão Geral

Esta fase implementa um sistema completamente novo e unificado para gerenciamento de fila de encoding, substituindo os antigos `QueueManager` e `JobManager` por um único `UnifiedQueueManager` mais robusto e funcional.

## Problemas Resolvidos

1. **Falta de sincronização**: O antigo sistema tinha dois gerenciadores separados que operavam de forma independente, causando inconsistências
2. **Gerenciamento de estado frágil**: Jobs podiam ficar em estados inconsistentes entre a fila e o gerenciador
3. **Controle limitado**: Funcionalidades de pausar, retomar e cancelar não eram totalmente integradas
4. **Falta de detalhes**: Jobs não exibiam informações completas sobre execução, recursos e histórico
5. **UI desatualizada**: A interface não refletia em tempo real o estado dos jobs

## Arquitetura do Novo Sistema

### Componentes Principais

#### 1. UnifiedQueueManager

Localização: [`src/managers/unified_queue_manager.py`](../src/managers/unified_queue_manager.py:1)

Classe principal que unifica todo o gerenciamento de fila:

- **Gerenciamento de Jobs**: Adicionar, remover, obter detalhes
- **Controle de Execução**: Pausar, retomar, cancelar, retentar
- **Gerenciamento de Fila**: Reordenar, prioridade, limpar
- **Persistência**: Salvar/carregar estado em JSON
- **Callbacks**: Atualizações em tempo real de progresso e status
- **Hardware Detection**: Limite automático baseado em GPU/CPU

#### 2. QueueJob (dataclass)

Estrutura de dados completa para cada job:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | str | UUID único |
| `input_path` | str | Caminho de entrada |
| `output_path` | str | Caminho de saída |
| `profile` | dict | Configurações do perfil |
| `profile_name` | str | Nome do perfil |
| `status` | str | Status atual |
| `progress` | float | Progresso (0-100) |
| `priority` | int | Prioridade (1-4) |
| `created_at` | str | Timestamp de criação |
| `started_at` | str | Timestamp de início |
| `completed_at` | str | Timestamp de conclusão |
| `elapsed_time` | str | Tempo decorrido (HH:MM:SS) |
| `eta` | str | ETA estimado (HH:MM:SS) |
| `speed` | float | Velocidade (%/min) |
| `input_size` | int | Tamanho de entrada (bytes) |
| `output_size` | int | Tamanho de saída (bytes) |
| `compression_ratio` | float | Razão de compressão |
| `error_message` | str | Mensagem de erro |
| `retry_count` | int | Contador de tentativas |
| `resource_usage` | ResourceUsage | Uso de recursos |
| `ffmpeg_pid` | int | PID do FFmpeg |
| `log_file` | str | Caminho do log |

#### 3. ResourceUsage (dataclass)

Monitoramento de recursos em tempo real:

- `gpu_usage`: Uso da GPU (%)
- `vram_usage`: Uso de VRAM (GB)
- `cpu_usage`: Uso da CPU (%)
- `memory_usage`: Uso de RAM (GB)
- `encoder_utilization`: Utilização do encoder (%)

#### 4. QueueMenuUIV2

Localização: [`src/ui/queue_menu_v2.py`](../src/ui/queue_menu_v2.py:1)

Nova interface de usuário com:

- Tabela detalhada com todas as informações
- Painel de detalhes do job
- Painel de estatísticas
- Barra de progresso visual
- Status e prioridade coloridos
- Menus de gerenciamento individual e em lote

## Funcionalidades Implementadas

### 1. Gestão Completa de Arquivos em Conversão

- Todos os jobs são rastreados com caminhos completos de entrada e saída
- Tamanhos de arquivo monitorados em tempo real
- Razão de compressão calculada automaticamente
- Logs individuais por job

### 2. Controle Total da Fila

**Pausar Fila:**
```python
queue_mgr.pause_queue()
```

**Retomar Fila:**
```python
queue_mgr.resume_queue()
```

**Limpar Fila:**
```python
# Limpar tudo
queue_mgr.clear_queue()

# Limpar apenas completados
queue_mgr.clear_queue(status_filter=JobStatus.COMPLETED)
```

### 3. Gerenciamento Individual de Jobs

**Cancelar Job:**
```python
queue_mgr.cancel_job(job_id)
```

**Pausar Job:**
```python
queue_mgr.pause_job(job_id)
```

**Retomar Job:**
```python
queue_mgr.resume_job(job_id)
```

**Retentar Job:**
```python
new_job_id = queue_mgr.retry_job(failed_job_id)
```

**Alterar Prioridade:**
```python
queue_mgr.set_job_priority(job_id, QueuePriority.HIGH)
```

**Reordenar na Fila:**
```python
queue_mgr.reorder_job(job_id, new_position=0)  # Move para primeiro
```

### 4. Detalhes Completos dos Jobs

Cada job exibe:

- **Informações Básicas**: ID, status, prioridade
- **Arquivos**: Input, output, perfil
- **Progresso**: Porcentagem com barra visual
- **Tempo**: Decorrido, ETA, velocidade
- **Tamanhos**: Original, codificado, compressão
- **Recursos**: GPU, CPU, VRAM, RAM, encoder
- **Timestamps**: Criação, início, conclusão
- **Erros**: Mensagens de falha (se houver)

## Exemplo de Uso

```python
from managers.unified_queue_manager import (
    UnifiedQueueManager,
    JobStatus,
    QueuePriority,
    ResourceUsage
)

# Criar gerenciador
queue_mgr = UnifiedQueueManager()

# Adicionar job
profile = {
    "id": "h264_1080p",
    "name": "H.264 1080p",
    "codec": "h264_nvenc",
    "resolution": "1920x1080",
    "bitrate": "8000K"
}

job = queue_mgr.add_job(
    input_path="/videos/input.mp4",
    output_path="/videos/output.mp4",
    profile=profile,
    priority=QueuePriority.HIGH
)

# Registrar como ativo (iniciar execução)
queue_mgr.register_active_job(job.id)

# Atualizar progresso
queue_mgr.update_progress(job.id, 45.5)

# Obter detalhes
details = queue_mgr.get_job_details(job.id)
print(f"Progresso: {details['progress']}%")
print(f"ETA: {details['eta']}")
print(f"Status: {details['status_display']}")

# Pausar job
queue_mgr.pause_job(job.id)

# Retomar job
queue_mgr.resume_job(job.id)

# Cancelar job
queue_mgr.cancel_job(job.id)

# Estatísticas
stats = queue_mgr.get_statistics()
print(f"Total: {stats['total']}")
print(f"Ativos: {stats['active']}")
```

## Estrutura do Arquivo de Persistência

```json
{
  "version": "2.0",
  "schema_version": 1,
  "last_updated": "2026-04-01T15:45:00.000000",
  "queue_paused": false,
  "max_concurrent_jobs": 4,
  "jobs": {
    "job_id": {
      "id": "job_id",
      "input_path": "...",
      "output_path": "...",
      "profile": {...},
      "status": "running",
      "progress": 45.5,
      ...
    }
  },
  "queue_order": ["job_id_1", "job_id_2"],
  "active_jobs": ["job_id_1"],
  "history": {
    "completed": [...],
    "failed": [...],
    "cancelled": [...]
  }
}
```

## Arquivos Criados/Modificados

### Criados
- [`src/managers/unified_queue_manager.py`](../src/managers/unified_queue_manager.py:1) - Core do sistema
- [`src/ui/queue_menu_v2.py`](../src/ui/queue_menu_v2.py:1) - Nova UI
- [`tests/test_unified_queue_manager.py`](../tests/test_unified_queue_manager.py:1) - Testes unitários
- [`tests/test_queue_ui_demo.py`](../tests/test_queue_ui_demo.py:1) - Demo da UI

### Modificados
- [`src/managers/__init__.py`](../src/managers/__init__.py:1) - Exportar novas classes

## API Reference

### UnifiedQueueManager

#### Métodos de Gerenciamento de Jobs
- `add_job(input_path, output_path, profile, priority)` → QueueJob
- `remove_job(job_id)` → bool
- `get_job(job_id)` → QueueJob
- `get_job_details(job_id)` → dict

#### Métodos de Controle de Execução
- `pause_job(job_id)` → bool
- `resume_job(job_id)` → bool
- `cancel_job(job_id)` → bool
- `retry_job(job_id)` → str (novo job_id)

#### Métodos de Gerenciamento de Fila
- `list_queue(status_filter, sort_by, ascending)` → List[QueueJob]
- `reorder_job(job_id, new_position)` → bool
- `set_job_priority(job_id, priority)` → bool
- `clear_queue(status_filter)` → int

#### Controle da Fila
- `pause_queue()` → bool
- `resume_queue()` → bool
- `is_queue_paused()` → bool

#### Hardware e Concorrência
- `can_start_new_job()` → bool
- `register_active_job(job_id)` → bool
- `unregister_active_job(job_id)` → None
- `get_max_concurrent_jobs()` → int
- `get_active_jobs_count()` → int

#### Estatísticas
- `get_statistics()` → dict
- `get_queue_length()` → int

#### Callbacks
- `register_status_callback(callback, job_id)` → None
- `register_progress_callback(callback, job_id)` → None

#### Persistência
- `save()` → bool
- `load()` → dict
- `export_to_json(filepath)` → bool
- `import_from_json(filepath)` → int
- `cleanup_history(older_than_days)` → int

## Testes

### Executar Testes Unitários
```bash
python tests/test_unified_queue_manager.py
```

### Executar Demo da UI
```bash
python tests/test_queue_ui_demo.py
```

## Próximos Passos (Fases Futuras)

1. **Migração e Compatibilidade**: Script para migrar dados dos antigos QueueManager e JobManager
2. **Integração com EncoderEngine**: Processamento automático da fila
3. **Monitor em Tempo Real**: Atualização ao vivo do progresso com Rich Live
4. **Documentação Completa**: Guia do usuário e API reference detalhada

## Benefícios

### Para o Usuário
- Controle total sobre todos os jobs
- Visibilidade completa do progresso
- Capacidade de gerenciar prioridades
- Informações detalhadas de cada conversão

### Para o Sistema
- Arquitetura unificada e consistente
- Thread safety garantida
- Persistência robusta
- Fácil extensão e manutenção
