# Fase 5: Modificações no Menu Principal

## Visão Geral

Esta fase implementou as modificações no menu principal para incluir as novas opções de codificação única e recorrente, conforme especificado no [`IMPLEMENTATION_PLAN.md`](../plans/IMPLEMENTATION_PLAN.md).

## Mudanças Implementadas

### 1. Novo Menu Principal

O menu principal foi atualizado com a seguinte estrutura:

```
Menu Principal
├── 1. Codificação de Pasta
│   ├── 1.1 Codificação Única (manual)
│   └── 1.2 Codificação Recorrente (automática)
├── 2. Codificar arquivo único
├── 3. Ver fila de jobs
├── 4. Gerenciar Perfis
├── 5. Ver estatísticas
├── 6. Gerenciar Conversões Recorrentes
└── 7. Sair
```

### 2. Submenu de Codificação de Pasta

Ao selecionar a opção "Codificação de Pasta", o usuário acessa um submenu com:
- **1.1 Codificação Única (manual)**: Executa a conversão manual de uma pasta específica
- **1.2 Codificação Recorrente (automática)**: Configura monitoramento contínuo de uma pasta
- **0. Voltar**: Retorna ao menu principal

### 3. Opção de Gerenciamento de Conversões Recorrentes

Nova opção dedicada no menu principal para gerenciar todas as conversões recorrentes configuradas, permitindo:
- Listar pastas recorrentes
- Adicionar/remover/editar pastas
- Ativar/desativar monitoramento
- Iniciar/parar monitores
- Ver histórico de processamento

## Arquivos Modificados

### [`src/cli.py`](../src/cli.py)

#### Imports Adicionados
- `from .ui.recurrent_folder_ui import RecurrentFolderUI`

#### Funções Criadas

1. **[`run_folder_conversion_submenu()`](../src/cli.py:848)**
   - Exibe submenu de codificação de pasta
   - Permite escolher entre codificação única ou recorrente
   - Encapsula a lógica de seleção do tipo de codificação

2. **[`run_single_folder_conversion()`](../src/cli.py:867)**
   - Executa codificação única de pasta
   - Chama a função existente `run_folder_conversion_cli()`
   - Mantém a funcionalidade original de conversão manual

3. **[`run_recurrent_folder_from_submenu()`](../src/cli.py:872)**
   - Executa codificação recorrente a partir do submenu
   - Instancia e executa `RecurrentFolderUI`
   - Reutiliza a infraestrutura existente da Fase 4

#### Função Modificada

- **[`run_interactive_mode()`](../src/cli.py:877)**
  - Atualizado para exibir novo menu com 7 opções
  - Opção 1: Chama `run_folder_conversion_submenu()`
  - Opção 6: Chama `run_recurrent_folder_from_submenu()` para gerenciamento direto
  - Numeração das opções subsequentes atualizada (2-5 → 2-5, 6 → gerenciamento recorrente)

## Dependências

- ✅ Fase 4 concluída (RecurrentFolderUI)
- ✅ Função `run_folder_conversion_cli()` existente para codificação única

## Fluxo de Uso

### Codificação Única de Pasta
1. Menu Principal → Opção 1 (Codificação de Pasta)
2. Submenu → Opção 1 (Codificação Única)
3. Selecionar pasta de entrada e saída
4. Configurar perfil ou usar existente
5. Iniciar conversão ou adicionar à fila

### Codificação Recorrente
1. Menu Principal → Opção 1 (Codificação de Pasta)
2. Submenu → Opção 2 (Codificação Recorrente)
3. Configurar pasta de entrada, saída e perfil
4. Monitoramento automático é iniciado

### Gerenciamento de Conversões Recorrentes
1. Menu Principal → Opção 6 (Gerenciar Conversões Recorrentes)
2. Acessar todas as funcionalidades de gerenciamento

## Resumo das Entregas

| Item | Status |
|------|--------|
| Menu principal atualizado com submenu de pasta | ✅ |
| Opção separada para gerenciamento de conversões recorrentes | ✅ |
| Funções de handler criadas | ✅ |
| Import da RecurrentFolderUI adicionado | ✅ |
| Documento de resumo gerado | ✅ |

## Próximos Passos

- Testar o fluxo completo do menu interativo
- Validar integração com as funcionalidades existentes
- Prosseguir para próxima fase do plano de implementação
