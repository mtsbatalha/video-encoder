# Fase 1: Estrutura de Dados e ConfigManager

## Visão Geral

Esta fase implementou a estrutura de dados para configurações recorrentes e estendeu o ConfigManager para suportar o gerenciamento de pastas recorrentes, conforme especificado no plano de implementação e na especificação técnica.

## Funcionalidades Implementadas

### 1. Estrutura de Dados para Pastas Recorrentes

Adicionada a estrutura de dados completa para representar pastas recorrentes com os seguintes campos:

- `id`: Identificador único (UUID v4)
- `name`: Nome descritivo da pasta
- `input_directory`: Caminho da pasta de entrada
- `output_directory`: Caminho da pasta de saída
- `profile_id`: ID do perfil de codificação
- `profile_name`: Nome do perfil de codificação
- `enabled`: Flag indicando se a pasta está habilitada
- `created_at`: Timestamp de criação
- `last_run`: Timestamp da última execução (pode ser nulo)
- `total_processed`: Contador total de arquivos processados
- `options`: Conjunto de opções de processamento

### 2. Extensão do ConfigManager

#### Campos Adicionados
- Campo `recurrent_folders` adicionado à configuração padrão

#### Métodos Implementados
- `get_recurrent_folders()`: Retorna a lista de pastas recorrentes
- `add_recurrent_folder(folder: Dict)`: Adiciona uma nova pasta recorrente com geração automática de ID e valores padrão
- `remove_recurrent_folder(index: int)`: Remove pasta recorrente por índice
- `update_recurrent_folder(folder_id: str, updates: Dict)`: Atualiza pasta recorrente pelo ID
- `_generate_uuid()`: Função utilitária privada para geração de UUIDs

### 3. Exemplo de Configuração

Atualizado o arquivo `config.example.json` com um exemplo completo de estrutura de pasta recorrente.

## Arquivos Modificados

1. `src/managers/config_manager.py`
   - Adicionadas importações necessárias (uuid, datetime)
   - Adicionado campo `recurrent_folders` ao DEFAULT_CONFIG
   - Implementados métodos para gerenciamento de pastas recorrentes
   - Implementada função utilitária para geração de UUIDs

2. `config.example.json`
   - Adicionado exemplo completo de estrutura de pastas recorrentes

## Estrutura de Opções

As opções de pasta recorrente incluem:
- `preserve_subdirectories`: Manter subdiretórios na saída
- `delete_source_after_encode`: Apagar fonte após codificação
- `copy_subtitles`: Copiar legendas
- `supported_extensions`: Lista de extensões suportadas
- `min_file_size_mb`: Tamanho mínimo de arquivo em MB
- `skip_existing_output`: Pular saída existente

## Considerações de Segurança e Validação

- IDs únicos são automaticamente gerados usando UUID v4
- Valores padrão são definidos automaticamente para campos obrigatórios
- O sistema mantém histórico de execuções e contagem de arquivos processados