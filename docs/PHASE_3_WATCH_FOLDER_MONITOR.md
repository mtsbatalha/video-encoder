# Fase 3: WatchFolderMonitor

## Visão Geral

Esta fase implementa o sistema de monitoramento de diretórios (`WatchFolderMonitor`) para detecção e processamento automático de arquivos de vídeo. O sistema permite monitorar pastas específicas, detectar novos arquivos de vídeo e adicioná-los automaticamente à fila de encoding.

## Implementação

### Classe WatchFolderMonitor

A classe `WatchFolderMonitor` implementa as seguintes funcionalidades:

- **Monitoramento contínuo**: Utiliza polling para verificar periodicamente a presença de novos arquivos
- **Detecção de arquivos completos**: Implementa debounce para garantir que arquivos estejam completamente copiados antes do processamento
- **Validações**: Verifica extensão, tamanho mínimo e se output já existe
- **Integração com fila**: Adiciona automaticamente arquivos válidos à fila de encoding
- **Controle de início/parada**: Métodos para iniciar e parar o monitoramento individualmente
- **Logging**: Registra todas as atividades do monitoramento

### Funcionalidades Implementadas

#### 1. Polling de Arquivos
- Verificação periódica de novos arquivos na pasta monitorada
- Configuração de intervalo de verificação (padrão: 10 segundos)

#### 2. Sistema de Debounce
- Verificação de estabilidade do tamanho do arquivo
- Aguarda tempo configurável (padrão: 5 segundos) para confirmar que arquivo está completo
- Verificação de bloqueio de arquivo (em uso por outro processo)

#### 3. Validações de Processamento
- Verificação de extensão suportada (configurável)
- Verificação de tamanho mínimo (padrão: 10MB)
- Opção para pular arquivos cujo output já existe
- Validação de existência do profile de encoding

#### 4. Integração com Sistema de Filas
- Criação de jobs no JobManager
- Adição à fila do QueueManager com prioridade configurável
- Geração automática de caminhos de saída baseados no profile

#### 5. Controle de Monitoramento
- Métodos `start()` e `stop()` para controle individual
- Thread separada para cada monitor
- Mecanismo de stop seguro com Event

## Arquitetura

### Dependências
- `ConfigManager`: Para obter configurações de monitoramento
- `QueueManager`: Para adicionar jobs à fila
- `JobManager`: Para criar registros de jobs
- `ProfileManager`: Para obter configurações de encoding
- `FileUtils`: Para operações de arquivo e verificação de estado

### Estrutura de Configuração

O monitor aceita as seguintes opções de configuração:

```json
{
  "path": "caminho/para/pasta/monitorada",
  "profile_id": "id_do_perfil_de_encoding",
  "interval": 10,
  "min_size": 10485760,
  "skip_existing_output": true,
  "extensions": [".mp4", ".mkv", ".avi"],
  "debounce_time": 5,
  "enabled": true,
  "priority": "normal",
  "output_path": "caminho/para/saida"
}
```

## Classes e Métodos

### WatchFolderMonitor

- `__init__(config, queue_manager, job_manager, profile_manager)`: Inicializa o monitor com configurações
- `start()`: Inicia o monitoramento da pasta
- `stop()`: Para o monitoramento da pasta
- `_check_for_new_files()`: Verifica por novos arquivos
- `_is_file_complete(path)`: Verifica se arquivo está completo (com debounce)
- `_should_process_file(path)`: Validações para determinar se arquivo deve ser processado
- `_enqueue_file(path)`: Adiciona arquivo à fila de encoding
- `_get_output_path(input_path)`: Gera caminho de saída baseado no profile

## Integração

O sistema se integra com:
- Sistema de filas para processamento assíncrono
- Gerenciador de jobs para rastreamento
- Gerenciador de perfis para configurações de encoding
- Sistema de logging para auditoria

## Melhorias Futuras

- Suporte a múltiplos perfis por pasta
- Filtragem avançada por metadados
- Suporte a eventos do sistema de arquivos (além de polling)
- Estatísticas de monitoramento
- Notificações de eventos