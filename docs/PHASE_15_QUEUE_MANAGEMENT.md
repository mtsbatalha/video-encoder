# PHASE_15_QUEUE_MANAGEMENT

## Visão Geral

Esta fase implementa melhorias significativas no sistema de fila de encoding, focando em três áreas principais:

1. **Limite de Jobs Simultâneos Baseado em Hardware**: Implementação de detecção automática de recursos de hardware para calcular o número ideal de jobs simultâneos
2. **Monitoramento Detalhado**: Adição de informações como tempo decorrido, ETA (tempo estimado de conclusão), velocidade de encoding e comparação de tamanhos
3. **Gerenciamento de Jobs Individuais**: Opções para cancelar, pausar, retomar e alterar prioridade de jobs individuais

## Arquivos Modificados

### 1. `src/managers/job_manager.py`

#### Novas Funcionalidades:
- Método `_calculate_max_concurrent_jobs()` para calcular limite baseado em hardware
- Propriedades `_max_concurrent_jobs` e `_active_jobs` para controle de concorrência
- Métodos `can_start_new_job()`, `register_active_job()`, `unregister_active_job()` para gerenciamento de jobs ativos
- Atualização do método `update_job_status()` para integrar controle de jobs ativos

#### Detalhes da Implementação:
- **GPU**: Estima ~6GB VRAM por job 4K NVENC, ~4GB por job AMF
- **CPU**: 1-2 cores por job
- O limite é determinado pelo recurso mais restritivo (GPU ou CPU)
- Integração com `HardwareDetector` para detecção automática

### 2. `src/ui/queue_menu.py`

#### Novas Funcionalidades:
- Cálculo de ETA e velocidade de encoding (`_calculate_eta_and_speed()`)
- Formatação de duração e tamanhos de arquivo (`_format_duration()`, `_format_file_size()`)
- Tabela expandida com colunas: Tempo, ETA, Velocidade, Tamanho
- Menu de gerenciamento individual de jobs (`_manage_individual_job()`)
- Opções de cancelar, pausar, retomar e visualizar logs de jobs

#### Interface Atualizada:
- Colunas adicionais na tabela de fila: Tempo decorrido, ETA, Velocidade, Tamanhos
- Nova opção no menu: "Gerenciar job individual"
- Submenu com detalhes completos do job e opções de ação

### 3. `config.example.json`

#### Atualização:
- Adicionado campo `"max_concurrent_jobs": null` para permitir configuração manual ou automática

## API e Interfaces

### JobManager
```python
def _calculate_max_concurrent_jobs(self) -> int:
    """Calcula o número máximo de jobs simultâneos baseado no hardware disponível."""

def get_max_concurrent_jobs(self) -> int:
    """Retorna o número máximo de jobs simultâneos permitidos."""

def can_start_new_job(self) -> bool:
    """Verifica se é possível iniciar um novo job."""

def register_active_job(self, job_id: str) -> bool:
    """Registra um job como ativo (em execução)."""

def unregister_active_job(self, job_id: str) -> None:
    """Remove um job da lista de ativos."""
```

### QueueMenuUI
```python
def _calculate_eta_and_speed(self, job_info: Dict[str, Any]) -> tuple:
    """Calcula ETA e velocidade de encoding para um job."""

def _format_duration(self, seconds: float) -> str:
    """Formata duração em segundos para HH:MM:SS."""

def _manage_individual_job(self):
    """Submenu para gerenciar job individual."""
```

## Benefícios Implementados

### 1. Otimização de Recursos
- Prevenção de sobrecarga de hardware através de limites inteligentes
- Detecção automática de hardware para configuração otimizada
- Balanceamento entre GPU e CPU para melhor desempenho

### 2. Monitoramento Aprimorado
- Visualização em tempo real de progresso, velocidade e ETA
- Comparação de tamanhos de entrada e saída
- Informações detalhadas sobre cada job

### 3. Controle Granular
- Capacidade de gerenciar jobs individuais sem afetar toda a fila
- Opções de pausa, retomada e cancelamento com confirmação
- Manutenção da integridade da fila durante operações

## Considerações de Desempenho

- O cálculo de ETA e velocidade é realizado apenas para jobs em execução
- O uso de locks garante thread safety nas operações de gerenciamento
- A detecção de hardware é realizada uma vez no início para evitar overhead

## Testes Recomendados

1. Testar limite de jobs com diferentes configurações de hardware
2. Verificar cálculos de ETA e velocidade com jobs reais
3. Validar funcionalidades de gerenciamento individual
4. Confirmar integração correta com o sistema de filas existente