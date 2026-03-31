# Phase 4: RecurrentFolderUI - Resumo da Implementação

## Visão Geral

Esta fase implementou a interface de usuário para gerenciamento de pastas recorrentes, permitindo que os usuários configurem, gerenciem e monitorem pastas para codificação contínua de vídeos.

## Implementação

### Classe Criada

**[`RecurrentFolderUI`](src/ui/recurrent_folder_ui.py:14)** - Localizada em [`src/ui/recurrent_folder_ui.py`](src/ui/recurrent_folder_ui.py)

A classe fornece uma interface completa baseada em terminal usando a biblioteca Rich, seguindo os mesmos padrões de design estabelecidos em [`WatchFoldersUI`](src/ui/watch_folders_ui.py:12).

### Métodos Implementados

| Método | Descrição |
|--------|-----------|
| [`__init__()`](src/ui/recurrent_folder_ui.py:18) | Inicializa a UI com Console, ConfigManager, ProfileManager e cria instância do RecurrentFolderManager |
| [`show_submenu()`](src/ui/recurrent_folder_ui.py:38) | Alias para `run()` - ponto de entrada do menu |
| [`run()`](src/ui/recurrent_folder_ui.py:41) | Loop principal do menu com 8 opções |
| [`_get_profile_choices()`](src/ui/recurrent_folder_ui.py:78) | Retorna lista de perfis formatados para seleção |
| [`_validate_folder_paths()`](src/ui/recurrent_folder_ui.py:88) | Valida caminhos de entrada e saída |
| [`_validate_profile()`](src/ui/recurrent_folder_ui.py:110) | Valida se o perfil existe |
| [`_get_folder_by_index()`](src/ui/recurrent_folder_ui.py:116) | Obtém pasta por índice (1-based) |
| [`list_recurrent_folders()`](src/ui/recurrent_folder_ui.py:122) | Exibe tabela com todas as pastas configuradas |
| [`add_recurrent_folder()`](src/ui/recurrent_folder_ui.py:162) | Formulário completo para adicionar nova pasta |
| [`remove_recurrent_folder()`](src/ui/recurrent_folder_ui.py:281) | Remove pasta com confirmação |
| [`edit_recurrent_folder()`](src/ui/recurrent_folder_ui.py:338) | Edita pasta existente com validações |
| [`toggle_enable_folder()`](src/ui/recurrent_folder_ui.py:471) | Ativa/desativa pasta recorrente |
| [`start_stop_monitors()`](src/ui/recurrent_folder_ui.py:522) | Gerencia inicio/parada de monitores |
| [`view_history()`](src/ui/recurrent_folder_ui.py:568) | Visualiza histórico de processamento |

## Funcionalidades

### 1. Listagem de Pastas Recorrentes

Tabela com colunas:
- **#**: Índice da pasta
- **Nome**: Nome descritivo
- **Entrada**: Caminho de entrada
- **Saída**: Caminho de saída
- **Perfil**: ID do perfil de encoding
- **Status**: Status (Ativa/Desativada + existência da pasta)
- **Processados**: Total de arquivos processados

### 2. Adição de Nova Pasta Recorrente

Formulário com:
- **Nome descritivo**: Identificador amigável da pasta
- **Caminho de entrada**: Valida existência do diretório
- **Caminho de saída**: Valida/cria diretório de saída
- **Seleção de perfil**: Lista perfis disponíveis com codec
- **Opções configuráveis**:
  - `preserve_subdirectories`: Preservar estrutura de subdiretórios
  - `skip_existing_output`: Pular arquivos já existentes
  - `delete_source_after_encode`: Excluir origem após conversão
  - `copy_subtitles`: Copiar legendas

### 3. Edição de Pasta Existente

- Exibe valores atuais entre colchetes
- Permite manter valores pressionando Enter
- Revalida caminhos e perfil se alterados
- Atualiza opções individualmente

### 4. Remoção com Confirmação

- Exibe tabela com todas as pastas
- Mostra resumo dos dados antes de remover
- Requer confirmação explícita do usuário

### 5. Toggle Enable/Disable

- Lista pastas com status atual
- Alterna entre ativo/desativado
- Feedback visual imediato

### 6. Gerenciamento de Monitores

- Exibe status de todos os monitores
- Opção para iniciar todos os monitores de pastas ativas
- Opção para parar todos os monitores
- Notas informativas sobre operação em segundo plano

### 7. Visualização de Histórico

- Tabela com resumo por pasta:
  - Total processado
  - Data/hora da última execução
  - Status de atividade
- Detalhes completos ao selecionar pasta específica

## Validações Implementadas

### Validação de Caminhos ([`_validate_folder_paths()`](src/ui/recurrent_folder_ui.py:88))

```python
- Verifica se pasta de entrada existe
- Verifica se é um diretório
- Tenta criar pasta de saída se não existir
- Captura PermissionError e exceções genéricas
- Retorna tuple (valid, message)
```

### Validação de Perfil ([`_validate_profile()`](src/ui/recurrent_folder_ui.py:110))

```python
- Consulta ProfileManager.get_profile()
- Verifica se perfil existe
- Retorna tuple (valid, message)
```

## Integração com Outros Componentes

### Dependências

| Componente | Uso |
|------------|-----|
| [`ConfigManager`](src/managers/config_manager.py:8) | Persistência de configuração |
| [`RecurrentFolderManager`](src/managers/recurrent_folder_manager.py:11) | Operações CRUD de pastas |
| [`ProfileManager`](src/managers/profile_manager.py) | Validação e listagem de perfis |
| [`Menu`](src/ui/menu.py:9) | Utilitários de UI |
| [`Validators`](src/ui/validators.py:6) | Validações utilitárias |

### Estrutura de Dados

Cada pasta recorrente segue o schema:

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
    "skip_existing_output": true,
    "supported_extensions": [".mp4", ".mkv", ".avi", ...],
    "min_file_size_mb": 0
  }
}
```

## Menu Interativo

```
Gerenciador de Pastas Recorrentes
Monitoramento contínuo de diretórios

Menu
  [1] Listar pastas recorrentes
  [2] Adicionar nova pasta recorrente
  [3] Remover pasta recorrente
  [4] Editar pasta recorrente
  [5] Ativar/Desativar pasta
  [6] Iniciar/Parar monitores
  [7] Ver histórico de processamento
  [0] Voltar ao menu principal
```

## Arquivos Criados/Modificados

### Criados
| Arquivo | Descrição |
|---------|-----------|
| [`src/ui/recurrent_folder_ui.py`](src/ui/recurrent_folder_ui.py) | Classe RecurrentFolderUI completa |
| [`docs/PHASE_4_RECURRENT_FOLDER_UI.md`](docs/PHASE_4_RECURRENT_FOLDER_UI.md) | Este documento de resumo |

### Nenhuma modificação em arquivos existentes

A implementação foi feita de forma isolada, utilizando apenas as interfaces públicas dos componentes existentes.

## Critérios de Aceitação Atendidos

- [x] Classe RecurrentFolderUI totalmente funcional
- [x] Menu interativo com Rich
- [x] Validações de entrada (caminhos, perfil)
- [x] Integração com RecurrentFolderManager
- [x] Listagem em tabela com todas as informações
- [x] Formulário de adição completo
- [x] Edição de pasta existente
- [x] Remoção com confirmação
- [x] Toggle enable/disable
- [x] Start/stop de monitores
- [x] Visualização de histórico

## Próximos Passos (Fase 5)

A Fase 5 deverá modificar o menu principal em [`src/cli.py`](src/cli.py) para:
1. Separar opção de pasta em única/recorrente
2. Adicionar submenu para "Codificação de Pasta"
3. Adicionar opção "Gerenciar Conversões Recorrentes" no menu principal
4. Integrar com a `RecurrentFolderUI` criada nesta fase

## Notas de Implementação

- A classe segue o mesmo padrão de design que `WatchFoldersUI`
- Todas as operações são confirmadas pelo usuário antes de executar
- Validações ocorrem antes e durante o processo de submissão
- Mensagens de erro e sucesso são exibidas usando os métodos do `Menu`
- O histórico visualizado é baseado nos dados armazenados no `RecurrentFolderManager`
