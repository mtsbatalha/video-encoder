# Phase 10: Multi-Profile Conversion - Implementation Summary

## Visão Geral

Esta fase implementa o suporte para **conversão multi-perfil**, permitindo que o usuário selecione vários perfis de codificação de uma vez e crie automaticamente múltiplos jobs na fila - um job para cada combinação de arquivo de entrada × perfil selecionado.

## Arquivos Criados/Modificados

### Novos Arquivos

1. **[`src/managers/multi_profile_conversion_manager.py`](../src/managers/multi_profile_conversion_manager.py)**
   - Nova classe `MultiProfileConversionManager`
   - Dataclasses `ConversionPlan` e `PlannedJob`
   - Enum `NamingConvention`

### Arquivos Modificados

1. **[`src/managers/__init__.py`](../src/managers/__init__.py)**
   - Adicionadas exports para `MultiProfileConversionManager`, `ConversionPlan`, `PlannedJob`, `NamingConvention`

2. **[`src/utils/file_utils.py`](../src/utils/file_utils.py)**
   - Novo método `generate_output_filename_for_profile()`
   - Novo método `_get_profile_suffix()` (estático)
   - Novo método `estimate_output_size()`

3. **[`src/ui/menu.py`](../src/ui/menu.py)**
   - Novo método `show_multi_profile_selection()` - Interface de seleção múltipla com checkboxes
   - Novo método `show_conversion_plan_preview()` - Preview da matriz de conversão

4. **[`src/cli.py`](../src/cli.py)**
   - Modificada função `run_folder_conversion_cli()` para suportar modo multi-perfil
   - Adicionada opção "Selecionar múltiplos perfis" no menu

## Funcionalidades Implementadas

### 1. MultiProfileConversionManager

Gerencia a criação de jobs em lote para múltiplas combinações arquivo × perfil.

**Métodos principais:**

```python
generate_conversion_plan(
    input_files: List[str],
    profile_ids: List[str],
    output_folder: str,
    options: Dict[str, Any]
) -> ConversionPlan
```
Gera plano de conversão sem criar jobs (usado para preview).

```python
create_jobs_for_multiple_profiles(
    input_files: List[str],
    profile_ids: List[str],
    output_folder: str,
    options: Dict[str, Any]
) -> List[Dict[str, Any]]
```
Cria jobs para múltiplos perfis e adiciona à fila.

```python
validate_profiles_compatibility(
    profile_ids: List[str]
) -> Tuple[bool, str]
```
Valida se perfis são compatíveis entre si.

### 2. Interface de Seleção Múltipla

Nova UI no menu que permite selecionar/desmarcar perfis com feedback visual:

```
┌────────────────────────────────────────────────────────────┐
│               Selecione os Perfis                          │
│  (Digite o número para selecionar/desmarcar, Enter p/ conf)│
├────┬────────────────┬──────────────────────────────────────┤
│ #  │ Selecionado    │ Nome            │ Codec      │ CQ   │
├────┼────────────────┼─────────────────┼────────────┼──────┤
│ 1  │ [x] Selecionado│ NVIDIA 4K HEVC  │ hevc_nvenc │ 18   │
│ 2  │ [x] Selecionado│ NVIDIA 1080p    │ hevc_nvenc │ 20   │
│ 3  │ [ ]            │ NVIDIA 720p     │ h264_nvenc │ 22   │
└────┴────────────────┴──────────────────────────────────────┘

Perfis selecionados: 2
  • NVIDIA Filmes 4K HEVC
  • NVIDIA Filmes 1080p HEVC
```

### 3. Preview da Matriz de Conversão

Exibe resumo completo antes de confirmar:

```
┌────────────────────────────────────────────────────────────┐
│              ⚙️ Plano de Conversão                         │
├────────────────────────────────────────────────────────────┤
│ 📊 RESUMO DA CONVERSÃO                                     │
│ Arquivos de entrada: 3                                     │
│ Perfis selecionados: 2                                     │
│ Total de jobs: 6                                           │
│ Tamanho estimado de saída: 4.50 GB                         │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│              Matriz de Conversão                           │
├───────────────────┬───────────────┬────────────────────────┤
│ Arquivo           │ 4K HEVC       │ 1080p HEVC             │
├───────────────────┼───────────────┼────────────────────────┤
│ filme1.mkv        │ ✓             │ ✓                      │
│ filme2.mkv        │ ✓             │ ✓                      │
│ filme3.mkv        │ ✓             │ ✓                      │
└───────────────────┴───────────────┴────────────────────────┘
```

### 4. Nomenclatura de Arquivos

Os arquivos de output recebem sufixo baseado no perfil:

- **Padrão (profile_suffix):** `filme_4k_hevc.mkv`
- **Prefixo (profile_prefix):** `4k_hevc_filme.mkv`
- **Subpasta (subfolder):** `4k_hevc/filme.mkv`

O sufixo é gerado automaticamente baseado em:
- Codec (ex: `hevc`, `h264`)
- Resolução (ex: `1080`, `4k`)
- CQ (ex: `cq18`, `cq20`)

Exemplo: `hevc_1080_cq20`

## Fluxo de Uso

### Modo Multi-Perfil

1. Usuário seleciona pasta de entrada
2. Usuário seleciona pasta de saída
3. Usuário escolhe "Selecionar múltiplos perfis"
4. Usuário marca/desmarca perfis desejados
5. Sistema gera plano de conversão
6. Sistema exibe preview com:
   - Total de jobs
   - Matriz de conversão
   - Estimativa de tamanho
7. Usuário confirma ou edita
8. Sistema cria todos os jobs e adiciona à fila
9. Sistema pergunta se deseja processar imediatamente

### Modo Perfil Único (Existente)

O fluxo original permanece inalterado para quem deseja usar apenas um perfil.

## Exemplo de Uso

### Cenário: Converter filmes para múltiplos dispositivos

**Objetivo:** Criar versões 4K, 1080p e 720p de 5 filmes

**Passos:**
1. Executar: `python -m src.cli -i`
2. Selecionar "Codificar pasta de vídeos"
3. Informar pasta de entrada: `/media/filmes`
4. Informar pasta de saída: `/output/filmes`
5. Escolher: "Selecionar múltiplos perfis"
6. Selecionar perfis:
   - [x] NVIDIA Filmes 4K HEVC
   - [x] NVIDIA Filmes 1080p HEVC
   - [x] NVIDIA Filmes 720p H264
7. Visualizar preview: "5 arquivos × 3 perfis = 15 jobs"
8. Confirmar conversão
9. Opcional: Processar fila imediatamente

**Resultado:** 15 jobs criados automaticamente na fila

## Estruturas de Dados

### ConversionPlan

```python
@dataclass
class ConversionPlan:
    input_files: List[str]           # Arquivos de entrada
    profiles: List[Dict[str, Any]]   # Perfis selecionados
    total_jobs: int                  # Total de jobs (arquivos × perfis)
    jobs: List[PlannedJob]           # Jobs planejados
    estimated_total_size: int        # Tamanho estimado de saída (bytes)
    created_at: str                  # Data de criação
    options: Dict[str, Any]          # Opções configuradas
```

### PlannedJob

```python
@dataclass
class PlannedJob:
    input_path: str                  # Caminho de entrada
    output_path: str                 # Caminho de saída
    profile_id: str                  # ID do perfil
    profile_name: str                # Nome do perfil
    estimated_output_size: int       # Tamanho estimado (bytes)
    priority: QueuePriority          # Prioridade na fila
    group_id: Optional[str]          # ID do grupo (nome do arquivo)
    metadata: Dict[str, Any]         # Metadata adicional
```

## Opções de Configuração

O método `generate_conversion_plan` e `create_jobs_for_multiple_profiles` aceitam:

```python
options = {
    'preserve_structure': True,      # Preservar subdiretórios
    'naming_convention': 'profile_suffix'  # profile_suffix, profile_prefix, subfolder
}
```

## Critérios de Aceite Atendidos

- [x] Usuário pode selecionar múltiplos perfis de uma vez
- [x] Sistema gera preview preciso do total de jobs
- [x] Jobs são criados com nomenclatura clara e organizada
- [x] Interface é intuitiva e não sobrecarrega o usuário
- [x] Fila gerencia jobs múltiplos corretamente
- [x] Código segue padrões existentes do projeto
- [x] Type hints utilizados em todos os métodos
- [x] Docstrings completas em todos os métodos

## Próximos Passos (Opcional)

1. **Testes Unitários:** Criar testes em `tests/test_multi_profile_conversion.py`
2. **Opção de Linha de Comando:** Adicionar `--multi-profile` e `--profile-id` no CLI
3. **Agrupamento de Jobs:** Implementar processamento agrupado por arquivo original
4. **Prioridade por Grupo:** Permitir definir prioridade diferente por grupo de jobs

## Compatibilidade

- **Python:** 3.10+
- **Dependências:** Nenhuma nova dependência adicionada
- **Retrocompatibilidade:** Fluxo de perfil único permanece inalterado
