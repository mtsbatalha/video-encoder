# Fase 2: RecurrentFolderManager

## Visão Geral

Esta fase implementou o gerenciador central para operações de pastas recorrentes, conforme especificado no plano de implementação e na especificação técnica. A classe `RecurrentFolderManager` fornece uma interface completa para gerenciar configurações de codificação automática de pastas.

## O que foi implementado

### 1. Classe RecurrentFolderManager

- Criada a classe `RecurrentFolderManager` em `src/managers/recurrent_folder_manager.py`
- Implementa todas as operações CRUD para pastas recorrentes
- Integra-se com `ConfigManager` para persistência de configurações
- Utiliza `ProfileManager` para validação de perfis de codificação

### 2. Operações CRUD Implementadas

#### Métodos de Gerenciamento
- `add_folder(folder_data: Dict) -> str`: Adiciona uma nova pasta recorrente e retorna seu ID
- `remove_folder(folder_id: str) -> bool`: Remove uma pasta recorrente existente
- `update_folder(folder_id: str, updates: Dict) -> bool`: Atualiza uma pasta recorrente existente
- `list_folders() -> List[Dict]`: Lista todas as pastas recorrentes configuradas
- `get_folder(folder_id: str) -> Optional[Dict]`: Obtém uma pasta específica por ID

#### Métodos de Controle
- `enable_folder(folder_id: str) -> bool`: Habilita uma pasta recorrente
- `disable_folder(folder_id: str) -> bool`: Desabilita uma pasta recorrente
- `get_enabled_folders() -> List[Dict]`: Retorna apenas pastas habilitadas

### 3. Validações Implementadas

- **Validação de caminhos**: Verifica se os diretórios de entrada e saída são válidos e existem
- **Validação de perfis**: Confirma que o perfil de codificação especificado existe
- **Campos obrigatórios**: Verifica presença de campos essenciais (nome, diretórios, perfil)
- **Validação de opções**: Verifica formato correto das opções adicionais

### 4. Persistência de Configurações

- As configurações são armazenadas no `ConfigManager` sob a chave `recurrent_folders`
- Cada pasta recorrente tem um ID único gerado automaticamente
- Campos de metadados incluem timestamps e contadores de processamento

## Estrutura de Dados

A classe suporta a estrutura de dados definida na especificação:

```json
{
  "id": "uuid-v4",
  "name": "Nome Descritivo",
  "input_directory": "C:/Path/To/Input",
  "output_directory": "C:/Path/To/Output",
  "profile_id": "profile-uuid",
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

## Integrações

- **ConfigManager**: Para persistência e recuperação de configurações
- **ProfileManager**: Para validação de perfis de codificação
- **path_utils**: Para validação de caminhos de diretórios

## Arquivos Criados/Modificados

- `src/managers/recurrent_folder_manager.py`: Implementação principal da classe
- `docs/PHASE_2_RECURRENT_FOLDER_MANAGER.md`: Documento de resumo desta fase

## Próximos Passos

Com esta fase concluída, os próximos passos envolvem:

1. Implementação do `WatchFolderMonitor` para monitorar diretórios
2. Integração com o sistema de filas para processamento automático
3. Implementação da interface de usuário para gerenciamento de pastas recorrentes