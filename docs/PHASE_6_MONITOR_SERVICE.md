# Fase 6: Serviço de Monitoramento Recorrente

## Visão Geral

Esta fase implementa o serviço de monitoramento recorrente que gerencia todos os monitores de pasta ativos conforme especificado no plano de implementação. O serviço é responsável por iniciar, parar e monitorar todos os monitores de pasta configurados no sistema.

## Componentes Implementados

### RecurrentMonitorService

Classe principal que gerencia todos os monitores de pasta ativos. Ela coordena o funcionamento dos monitores individuais e fornece métodos para controle centralizado.

#### Métodos Implementados

1. **`__init__(config_manager, queue_manager, job_manager, profile_manager)`**
   - Inicializa o serviço com todas as dependências necessárias

2. **`start_all_monitors()`**
   - Lê as configurações e inicia todos os monitores de pasta configurados
   - Retorna um dicionário com os monitores iniciados

3. **`stop_all_monitors()`**
   - Para todos os monitores ativos
   - Limpa a lista interna de monitores

4. **`start_monitor(folder_id)`**
   - Inicia um monitor específico pelo ID da pasta
   - Retorna True se o monitor foi iniciado com sucesso

5. **`stop_monitor(folder_id)`**
   - Para um monitor específico pelo ID da pasta
   - Retorna True se o monitor foi parado com sucesso

6. **`get_status()`**
   - Retorna o status de todos os monitores ativos
   - Fornece informações sobre o estado de cada monitor

7. **`graceful_shutdown()`**
   - Realiza o desligamento gracioso de todos os monitores
   - Garante que todos os recursos sejam liberados corretamente

## Integração com Outros Componentes

O serviço se integra com:

- **ConfigManager**: Para obter as configurações das pastas recorrentes
- **QueueManager**: Para adicionar arquivos à fila de processamento
- **JobManager**: Para gerenciar os trabalhos de codificação
- **ProfileManager**: Para obter os perfis de codificação
- **WatchFolderMonitor**: Para monitorar as pastas individualmente

## Funcionalidades

- Gerenciamento centralizado de múltiplos monitores de pasta
- Controle individual e em grupo dos monitores
- Status detalhado de todos os monitores ativos
- Desligamento gracioso para evitar perda de dados
- Tratamento adequado de erros e logging

## Arquitetura

O serviço segue uma abordagem orientada a objetos com responsabilidades bem definidas:

- Cada monitor é uma instância independente de `WatchFolderMonitor`
- O serviço mantém uma referência a todos os monitores ativos
- As operações podem ser aplicadas a todos os monitores ou a um específico

## Considerações de Segurança e Estabilidade

- Verificação de configurações válidas antes de iniciar monitores
- Tratamento de exceções para evitar falhas em cascata
- Logging detalhado para facilitar a depuração
- Uso de ThreadPoolExecutor para gerenciar threads de forma segura

## Testes e Validação

O serviço foi projetado para ser facilmente testável, com dependências injetáveis e métodos bem definidos que podem ser testados individualmente.

## Próximos Passos

Com este serviço implementado, o sistema agora pode:

- Gerenciar múltiplos monitores de pasta simultaneamente
- Controlar o ciclo de vida dos monitores de forma centralizada
- Fornecer informações sobre o status dos monitores
- Garantir um desligamento seguro do sistema