# Queue System Tech Stack

## Tecnologias e Dependências

### Bibliotecas Principais

| Biblioteca | Versão | Uso |
|------------|--------|-----|
| Python | 3.10+ | Linguagem base |
| Rich | 13.x | Interface de terminal |
| psutil | 5.x | Monitoramento de sistema |
| pathlib | built-in | Manipulação de caminhos |
| json | built-in | Persistência de dados |
| threading | built-in | Concorrência |
| datetime | built-in | Manipulação de tempo |
| uuid | built-in | Geração de IDs únicos |
| dataclasses | built-in | Estruturas de dados |
| enum | built-in | Enums tipados |

### Sem Novas Dependências

O sistema será reconstruído usando apenas bibliotecas já disponíveis no projeto, sem necessidade de instalar novos pacotes.

## Estrutura de Arquivos

### Diretório de Jobs

```
jobs/
├── queue.json              # Arquivo principal da fila unificada
├── logs/                   # Logs individuais por job
│   ├── {job_id}.log
│   └── {job_id}.log
├── temp/                   # Arquivos temporários de encoding
│   └── {job_id}_temp
└── history/                # Histórico de jobs completados
    └── {YYYY-MM}.json
```

### Estrutura do `queue.json`

```json
{
  "version": "2.0",
  "schema_version": 1,
  "last_updated": "2026-04-01T15:45:00.000000",
  "queue_paused": false,
  "max_concurrent_jobs": 4,
  "jobs": {
    "550e8400-e29b-41d4-a716-446655440000": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "input_path": "C:/Videos/raw/video_001.mp4",
      "output_path": "C:/Videos/encoded/video_001_h264.mp4",
      "profile": {
        "id": "h264_1080p",
        "name": "H.264 1080p",
        "codec": "h264_nvenc",
        "resolution": "1920x1080",
        "bitrate": "8000K",
        "preset": "p5",
        "crf": 23
      },
      "profile_name": "H.264 1080p",
      "status": "running",
      "progress": 45.5,
      "priority": 2,
      "created_at": "2026-04-01T10:30:00.000000",
      "started_at": "2026-04-01T10:35:00.000000",
      "paused_at": null,
      "resumed_at": null,
      "completed_at": null,
      "elapsed_time": "00:15:30",
      "eta": "00:18:45",
      "speed": 2.9,
      "input_size": 2147483648,
      "output_size": 524288000,
      "compression_ratio": 0.244,
      "error_message": null,
      "retry_count": 0,
      "resource_usage": {
        "gpu_usage": 85.5,
        "vram_usage": 4.2,
        "cpu_usage": 25.0,
        "memory_usage": 1.5,
        "encoder_utilization": 92.0
      },
      "ffmpeg_pid": 12345,
      "log_file": "jobs/logs/550e8400-e29b-41d4-a716-446655440000.log"
    }
  },
  "queue_order": [
    "550e8400-e29b-41d4-a716-446655440000",
    "660e8400-e29b-41d4-a716-446655440001"
  ],
  "active_jobs": [
    "550e8400-e29b-41d4-a716-446655440000"
  ],
  "history": {
    "completed": [
      "440e8400-e29b-41d4-a716-446655439999"
    ],
    "failed": [],
    "cancelled": []
  }
}
```

## Enums e Tipos

### JobStatus

```python
class JobStatus(Enum):
    PENDING = "pending"       # Job criado, aguardando na fila
    QUEUED = "queued"         # Job na fila, aguardando execução
    RUNNING = "running"       # Job em execução
    PAUSED = "paused"         # Job pausado pelo usuário
    COMPLETED = "completed"   # Job completado com sucesso
    FAILED = "failed"         # Job falhou com erro
    CANCELLED = "cancelled"   # Job cancelado pelo usuário
```

### QueuePriority

```python
class QueuePriority(Enum):
    LOW = 1       # Baixa prioridade
    NORMAL = 2    # Prioridade normal (padrão)
    HIGH = 3      # Alta prioridade
    CRITICAL = 4  # Prioridade crítica (executa primeiro)
```

## Classes Principais

### UnifiedQueueManager

```python
class UnifiedQueueManager:
    """
    Gerenciador unificado de fila de encoding.
    
    Atributos:
        jobs_dir (Path): Diretório para armazenar dados dos jobs
        data_file (Path): Arquivo JSON de persistência
        _jobs (Dict): Dicionário de jobs por ID
        _queue_order (List): Lista ordenada de job IDs na fila
        _active_jobs (Set): Set de job IDs em execução
        _max_concurrent (int): Máximo de jobs simultâneos
        _paused (bool): Status de pausa da fila
        _lock (threading.Lock): Lock para thread safety
        _status_callbacks (Dict): Callbacks por job_id
        _progress_callbacks (Dict): Callbacks por job_id
    """
```

### QueueJob (dataclass)

```python
@dataclass
class QueueJob:
    """
    Representação de um job na fila.
    
    Atributos:
        id (str): UUID único do job
        input_path (str): Caminho do arquivo de entrada
        output_path (str): Caminho do arquivo de saída
        profile (dict): Configurações do perfil
        profile_name (str): Nome do perfil
        status (str): Status atual
        progress (float): Progresso (0-100)
        priority (int): Prioridade (1-4)
        created_at (str): Timestamp de criação
        started_at (Optional[str]): Timestamp de início
        paused_at (Optional[str]): Timestamp de pausa
        resumed_at (Optional[str]): Timestamp de retomada
        completed_at (Optional[str]): Timestamp de conclusão
        elapsed_time (str): Tempo decorrido formatado
        eta (str): ETA formatado
        speed (float): Velocidade (%/min)
        input_size (int): Tamanho de entrada (bytes)
        output_size (int): Tamanho de saída (bytes)
        compression_ratio (float): Razão de compressão
        error_message (Optional[str]): Mensagem de erro
        retry_count (int): Contador de tentativas
        resource_usage (dict): Uso de recursos
        ffmpeg_pid (Optional[int]): PID do FFmpeg
        log_file (str): Caminho do arquivo de log
    """
```

## Variáveis de Ambiente (Opcionais)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `QUEUE_JOBS_DIR` | `./jobs` | Diretório personalizado para jobs |
| `QUEUE_MAX_CONCURRENT` | `auto` | Máximo de jobs (auto ou número) |
| `QUEUE_PERSIST_INTERVAL` | `5` | Intervalo de auto-save (segundos) |

## Compatibilidade

### Arquivos Existentes

- `profiles/profiles.json` - Compatível
- `config.example.json` - Compatível
- `jobs/` directory - Compatível

### Migração

O sistema incluirá um método de migração automática que:
1. Detecta arquivos antigos do `QueueManager` e `JobManager`
2. Converte jobs antigos para o novo formato
3. Preserva histórico existente
4. Cria backup dos arquivos antigos

## Performance

### Otimizações

- **Lazy Loading**: Jobs são carregados sob demanda do arquivo JSON
- **Batch Save**: Múltiplas atualizações são agrupadas em uma única escrita
- **Memory Efficient**: Apenas jobs ativos são mantidos em memória completa
- **Thread Pool**: Callbacks são executados em thread pool separado

### Limites Recomendados

| Recurso | Limite | Descrição |
|---------|--------|-----------|
| Jobs na fila | 1000 | Máximo recomendado |
| Histórico | 30 dias | Auto-cleanup |
| Tamanho do log | 10 MB | Rotação de logs |
| Concurrent jobs | Hardware-based | Definido por detecção de hardware |
