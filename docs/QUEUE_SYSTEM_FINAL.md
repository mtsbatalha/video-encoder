# Sistema de Fila Unificado - Guia Final

## Resumo da Reconstrução

O sistema de fila foi completamente reconstruído do zero para resolver problemas de sincronização e falta de funcionalidades.

### Problema Original

- **Dois gerenciadores desincronizados**: `QueueManager` + `JobManager` operavam separadamente
- Falta de detalhes dos jobs (progresso, ETA, velocidade, uso de recursos)
- Impossibilidade de pausar, cancelar ou gerenciar jobs individuais
- UI mostrando dados inconsistentes ("Jobs em execução: 6" mas "Fila vazia")

### Solução Implementada

**UnifiedQueueManager** - Gerenciador único que substitui ambos os antigos:

- 📁 **Arquivo**: [`src/managers/unified_queue_manager.py`](../src/managers/unified_queue_manager.py)
- 🗄️ **Persistência**: `jobs/queue.json` (formato JSON unificado)
- 🔄 **Thread-safe**: Usa `threading.RLock()` para sincronização
- 📊 **Estatísticas completas**: Progresso, ETA, velocidade, uso de GPU/CPU/VRAM/RAM
- 🎯 **Prioridades**: LOW, NORMAL, HIGH, CRITICAL
- 🎮 **Controle total**: Pausar, retomar, cancelar jobs individuais ou em lote

## Arquitetura do Novo Sistema

### Classes Principais

#### 1. **JobStatus** (Enum)
```python
PENDING    # Job criado, aguardando na fila
QUEUED     # Job na fila, aguardando execução
RUNNING    # Job em execução
PAUSED     # Job pausado pelo usuário
COMPLETED  # Job completado com sucesso
FAILED     # Job falhou com erro
CANCELLED  # Job cancelado pelo usuário
```

#### 2. **QueuePriority** (Enum)
```python
LOW = 1        # Baixa prioridade
NORMAL = 2     # Prioridade normal (padrão)
HIGH = 3       # Alta prioridade
CRITICAL = 4   # Prioridade crítica (executa primeiro)
```

#### 3. **QueueJob** (Dataclass)
Job completo com todos os detalhes:
- IDs, paths, perfil de encoding
- Status, progresso (0-100%), prioridade
- Timestamps (criação, início, pausa, conclusão)
- Tempo decorrido, ETA estimado
- Velocidade de encoding (%/min)
- Tamanhos de entrada/saída, taxa de compressão
- Uso de recursos (GPU, VRAM, CPU, RAM)
- PID do processo FFmpeg
- Callbacks personalizados

#### 4. **UnifiedQueueManager**
Gerenciador único com métodos completos:

**Gerenciamento de Jobs:**
- `add_job()` - Adicionar job à fila
- `remove_job()` - Remover job
- `pause_job()` - Pausar job
- `resume_job()` - Retomar job
- `cancel_job()` - Cancelar job
- `retry_job()` - Tentar novamente job falhado

**Gerenciamento de Fila:**
- `list_queue()` - Listar jobs (com filtros e ordenação)
- `reorder_job()` - Reordenar posição na fila
- `set_job_priority()` - Alterar prioridade
- `clear_queue()` - Limpar fila completa
- `pause_queue()` / `resume_queue()` - Pausar/retomar processamento

**Controle de Execução:**
- `can_start_new_job()` - Verificar se pode iniciar novo job
- `register_active_job()` - Registrar job ativo
- `unregister_active_job()` - Desregistrar job ativo
- `get_max_concurrent_jobs()` - Limite de jobs simultâneos
- `get_active_jobs_count()` - Contagem de jobs ativos

**Monitoramento:**
- `get_job_details()` - Detalhes completos de um job
- `get_statistics()` - Estatísticas da fila
- `update_progress()` - Atualizar progresso
- `update_job_status()` - Atualizar status

**Persistência:**
- `save()` / `load()` - Salvar/carregar de arquivo
- `export_to_json()` / `import_from_json()` - Import/export
- `cleanup_history()` - Limpar jobs antigos

**Callbacks:**
- `register_status_callback()` - Callback para mudanças de status
- `register_progress_callback()` - Callback para progresso

## Nova Interface (UI v2)

### QueueMenuUIV2

Interface moderna usando Rich library:

- **Tabela detalhada** com todos os jobs
- **Painel de estatísticas** da fila
- **Gerenciamento individual** de jobs:
  - Ver detalhes completos
  - Pausar/retomar
  - Cancelar
  - Alterar prioridade
  - Retry (tentar novamente)
- **Gerenciamento em lote**:
  - Pausar/retomar fila inteira
  - Limpar fila completa
  - Filtrar por status
  - Ordenar por prioridade/data

### Exemplo de Exibição

```
╭────────────────────────────────────────────────────────────────╮
│                    FILA DE ENCODING                            │
╰────────────────────────────────────────────────────────────────╯

┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ ID       ┃ Input          ┃ Status ┃ Progresso┃ Velocidade┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ af4b55dc │ video1.mp4     │ RUNNING│ 45.2%    │ 2.3%/min │
│ 1007744c │ video2.mp4     │ QUEUED │ 0.0%     │ --       │
│ cb1b3a30 │ video3.mp4     │ QUEUED │ 0.0%     │ --       │
└──────────┴────────────────┴────────┴──────────┴──────────┘

📊 Jobs Ativos: 1/2
📋 Total na Fila: 3
⏱️  ETA: ~45min
```

## Integração com o Sistema

### CLI Principal

Em [`src/cli.py`](../src/cli.py), o UnifiedQueueManager substitui AMBOS os gerenciadores antigos:

```python
# ANTES (bugado):
job_mgr = JobManager()
queue_mgr = QueueManager()

# AGORA (correto):
unified_queue_mgr = UnifiedQueueManager()
job_mgr = unified_queue_mgr  # Mesma instância
queue_mgr = unified_queue_mgr  # Mesma instância
```

### Métodos de Compatibilidade

Para manter compatibilidade com código existente, o UnifiedQueueManager implementa:

```python
# Compatibilidade com JobManager
get_running_jobs() -> List[Dict]  # Jobs em execução
get_pending_jobs() -> List[Dict]  # Jobs pendentes
list_jobs() -> List[Dict]          # Todos os jobs

# Compatibilidade com QueueManager  
list_queue() -> List[QueueJob]     # Fila completa
is_paused() -> bool                 # Status da fila
```

## Migração de Dados

### Utilitário de Migração

O arquivo [`src/utils/queue_migration.py`](../src/utils/queue_migration.py) migra dados automaticamente:

- Lê jobs do antigo `jobs.json` (JobManager)
- Lê fila do antigo `queue.json` (QueueManager)
- Converte para o novo formato unificado
- Salva em `jobs/queue.json` (UnifiedQueueManager)

### Executar Migração

```bash
python src/utils/queue_migration.py
```

## Como Usar

### 1. Iniciar Aplicação

```bash
# Windows/Mac
python src/cli.py --interactive

# Linux (use python3)
python3 src/cli.py --interactive
```

### 2. Acessar Menu de Fila

No menu principal, escolha "Ver fila de jobs"

### 3. Adicionar Jobs

Use as opções do menu para:
- Converter arquivo único
- Converter pasta
- Configurar pasta recorrente
- Watch folder (monitoramento contínuo)

### 4. Gerenciar Fila

No submenu de fila:
- Ver detalhes da fila
- Pausar/retomar processamento
- Gerenciar jobs individuais
- Alterar prioridades
- Limpar fila

### 5. Monitorar Progresso

O sistema exibe em tempo real:
- Progresso de cada job (%)
- Velocidade de encoding (%/min)
- Tempo decorrido (HH:MM:SS)
- ETA estimado (HH:MM:SS)
- Uso de recursos (GPU, VRAM, CPU, RAM)

## Recursos Principais

### ✅ Gestão Completa de Arquivos

- ✓ Adicionar múltiplos jobs simultaneamente
- ✓ Controle de limite de jobs concorrentes (baseado em hardware)
- ✓ Detecção automática de GPU/CPU disponível
- ✓ Persistência automática (salva a cada mudança)

### ✅ Controle de Execução

- ✓ **Pausar** job individual ou fila inteira
- ✓ **Retomar** job pausado
- ✓ **Cancelar** job em andamento
- ✓ **Retry** job falhado
- ✓ **Limpar** fila completa

### ✅ Priorização

- ✓ 4 níveis de prioridade (LOW, NORMAL, HIGH, CRITICAL)
- ✓ Alterar prioridade de job existente
- ✓ Reordenar posição na fila manualmente
- ✓ Ordenação automática por prioridade

### ✅ Detalhes Completos

Para cada job:
- ID único (UUID)
- Arquivos de entrada/saída
- Perfil de encoding usado
- Status atual
- Progresso (0-100%)
- Tempo decorrido
- ETA estimado
- Velocidade de encoding
- Tamanhos (entrada/saída)
- Taxa de compressão
- Uso de recursos (GPU, VRAM, CPU, RAM)
- PID do processo FFmpeg
- Timestamp de cada evento (criação, início, pausa, conclusão)

### ✅ Estatísticas da Fila

- Total de jobs
- Jobs ativos vs limite
- Distribuição por status (running, queued, completed, failed)
- Distribuição por prioridade
- Taxa de sucesso (%)
- Tamanhos totais processados

## Testes

### Scripts de Teste Incluídos

1. **`tests/test_unified_queue_manager.py`**
   - Testes unitários completos
   - 25+ casos de teste
   - Cobertura de todos os métodos

2. **`tests/test_queue_ui_demo.py`**
   - Demo da nova UI
   - Simula fila com jobs de exemplo

3. **`test_unified_queue_display.py`**
   - Diagnóstico de exibição
   - Valida métodos de compatibilidade

4. **`debug_queue_ui.py`**
   - Diagnóstico completo
   - Compara antigo vs novo sistema

### Executar Testes

```bash
# Testes unitários
python -m pytest tests/test_unified_queue_manager.py -v

# Demo da UI
python tests/test_queue_ui_demo.py

# Diagnóstico
python test_unified_queue_display.py
```

## Documentação Adicional

- [`docs/QUEUE_SYSTEM_SPEC.md`](QUEUE_SYSTEM_SPEC.md) - Especificação técnica completa
- [`docs/QUEUE_SYSTEM_TECH_STACK.md`](QUEUE_SYSTEM_TECH_STACK.md) - Stack tecnológico
- [`docs/QUEUE_IMPLEMENTATION_PLAN.md`](QUEUE_IMPLEMENTATION_PLAN.md) - Plano de implementação
- [`docs/PHASE_QUEUE_SYSTEM.md`](PHASE_QUEUE_SYSTEM.md) - Resumo da implementação

## Arquivos do Sistema

### Criados/Modificados

**Novos Arquivos:**
- `src/managers/unified_queue_manager.py` (core do novo sistema)
- `src/ui/queue_menu_v2.py` (nova interface)
- `src/utils/queue_migration.py` (migração de dados)
- `tests/test_unified_queue_manager.py` (testes unitários)
- Documentação completa (4 arquivos em docs/)

**Modificados:**
- `src/cli.py` - Integração do UnifiedQueueManager
- `src/ui/queue_menu.py` - Chama nova UI v2
- `src/managers/__init__.py` - Exporta novas classes

### Estrutura de Persistência

```
jobs/
├── queue.json    # Novo formato unificado (UnifiedQueueManager)
└── jobs.json     # Antigo formato (JobManager) - será descontinuado
```

## Próximos Passos

1. ✅ Sistema limpo e pronto para uso
2. Adicionar jobs reais de conversão
3. Testar gerenciamento (pausar, cancelar, priorizar)
4. Monitorar uso de recursos durante encoding
5. (Opcional) Remover completamente JobManager/QueueManager antigos

## Suporte

Para problemas ou dúvidas:
1. Verifique logs em modo debug
2. Execute scripts de diagnóstico
3. Consulte documentação técnica
4. Verifique issues conhecidos (se houver)

---

**Sistema de Fila Unificado - Versão 2.0.0**  
Reconstruído do zero para máxima funcionalidade e confiabilidade.
