# Phase 10: Multi-Profile Conversion Support

## Visão Geral

Esta fase implementa suporte para **múltipla conversão em uma única configuração**, permitindo que o usuário selecione vários perfis de codificação de uma vez e crie automaticamente múltiplos jobs na fila - um job para cada combinação de arquivo de entrada + perfil selecionado.

## Problema Atual

Atualmente, o sistema requer que o usuário:
1. Selecione um arquivo ou pasta para conversão
2. Escolha **um único perfil** para todos os arquivos
3. Adicione os jobs à fila com esse perfil único

Para usar diferentes perfis, o usuário precisa repetir todo o processo manualmente para cada perfil desejado.

## Solução Proposta

Adicionar uma interface que permite:
1. Selecionar arquivos/pasta para conversão
2. **Selecionar múltiplos perfis** de uma vez
3. Automaticamente criar jobs para cada combinação arquivo × perfil
4. Visualizar resumo completo antes de confirmar
5. Adicionar todos os jobs à fila de uma vez

## Arquitetura do Sistema

### Componentes Existentes

```
┌─────────────────────────────────────────────────────────────┐
│                     UI Layer (menu.py)                       │
│  - show_pre_conversion_summary()                             │
│  - show_advanced_profile_editor()                            │
│  - show_profiles_table()                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Manager Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ ProfileManager  │  │   JobManager    │  │ QueueManager │ │
│  │                 │  │                 │  │              │ │
│  │ - list_profiles │  │ - create_job    │  │ - add_to_    │ │
│  │ - get_profile   │  │ - update_job    │  │   queue      │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Core Layer                                 │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  EncoderEngine  │  │  FFmpegWrapper  │                   │
│  │                 │  │                 │                   │
│  │ - add_job       │  │ - run_encoding  │                   │
│  │ - execute_job   │  │ - build_command │                   │
│  └─────────────────┘  └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Novos Componentes

```
┌─────────────────────────────────────────────────────────────┐
│              MultiProfileConversionManager                   │
│  (NOVO - src/managers/multi_profile_conversion_manager.py)  │
│                                                              │
│  - create_jobs_for_multiple_profiles(                        │
│      input_files: List[str],                                 │
│      profile_ids: List[str],                                 │
│      output_folder: str                                      │
│    ) -> List[Dict]                                           │
│                                                              │
│  - generate_conversion_plan(                                 │
│      input_files: List[str],                                 │
│      profiles: List[Dict]                                    │
│    ) -> ConversionPlan                                       │
│                                                              │
│  - validate_profiles_compatibility(                          │
│      profile_ids: List[str]                                  │
│    ) -> tuple[bool, str]                                     │
└─────────────────────────────────────────────────────────────┘
```

## Fluxo de Dados

### Fluxo Atual (Single Profile)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Selecionar  │────▶│  Escolher    │────▶│  Criar Jobs  │
│   Arquivos   │     │   Perfil     │     │  (1 perfil)  │
└──────────────┘     └──────────────┘     └──────────────┘
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │  Adicionar   │
                                         │    à Fila    │
                                         └──────────────┘
```

### Novo Fluxo (Multi-Profile)

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Selecionar  │────▶│  Selecionar      │────▶│  Gerar Plano │
│   Arquivos   │     │  Múltiplos       │     │  de Conversão│
│              │     │   Perfis         │     │  (Preview)   │
└──────────────┘     └──────────────────┘     └──────────────┘
                                                │
                                                ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Processar   │◀────│  Confirmar   │◀────│  Resumo      │
│    Fila      │     │   Conversão  │     │  Completo    │
└──────────────┘     └──────────────┘     └──────────────┘
```

## Estrutura de Dados

### ConversionPlan

```python
@dataclass
class ConversionPlan:
    """Plano de conversão multi-perfil."""
    input_files: List[str]           # Arquivos de entrada
    profiles: List[Dict[str, Any]]   # Perfis selecionados
    total_jobs: int                  # Total de jobs (arquivos × perfis)
    jobs: List[PlannedJob]           # Jobs planejados
    estimated_total_size: int        # Tamanho estimado de saída
    created_at: str                  # Data de criação
    
@dataclass
class PlannedJob:
    """Job planejado para conversão."""
    input_path: str
    output_path: str
    profile_id: str
    profile_name: str
    estimated_output_size: int
    priority: QueuePriority
```

## API Pública

### MultiProfileConversionManager

```python
class MultiProfileConversionManager:
    def __init__(
        self,
        profile_manager: ProfileManager,
        job_manager: JobManager,
        queue_manager: QueueManager
    ):
        """Inicializa o gerenciador de conversão multi-perfil."""
        
    def create_jobs_for_multiple_profiles(
        self,
        input_files: List[str],
        profile_ids: List[str],
        output_folder: str,
        preserve_structure: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Cria jobs para múltiplos perfis.
        
        Args:
            input_files: Lista de arquivos de entrada
            profile_ids: Lista de IDs de perfis
            output_folder: Pasta de saída
            preserve_structure: Preservar estrutura de diretórios
            
        Returns:
            Lista de jobs criados
        """
        
    def generate_conversion_plan(
        self,
        input_files: List[str],
        profile_ids: List[str],
        output_folder: str
    ) -> ConversionPlan:
        """
        Gera plano de conversão sem criar jobs.
        
        Args:
            input_files: Lista de arquivos de entrada
            profile_ids: Lista de IDs de perfis
            output_folder: Pasta de saída
            
        Returns:
            Objeto ConversionPlan
        """
        
    def validate_profiles_compatibility(
        self,
        profile_ids: List[str]
    ) -> tuple[bool, str]:
        """
        Valida se perfis são compatíveis entre si.
        
        Args:
            profile_ids: Lista de IDs de perfis
            
        Returns:
            Tuple (é_compatível, mensagem_erro)
        """
```

## Integração com UI

### Nova Interface no Menu

```python
def show_multi_profile_selection(
    self,
    profiles: List[Dict[str, Any]],
    title: str = "Selecione os Perfis"
) -> List[str]:
    """
    Exibe interface para seleção múltipla de perfis.
    
    Returns:
        Lista de IDs de perfis selecionados
    """

def show_conversion_plan_preview(
    self,
    plan: ConversionPlan
) -> int:
    """
    Exibe preview do plano de conversão.
    
    Returns:
        Índice da ação escolhida:
        0 - Confirmar e adicionar à fila
        1 - Editar perfis
        2 - Editar arquivos
        3 - Cancelar
    """
```

## Casos de Uso

### Caso de Uso 1: Filmes com Múltiplas Qualidades

**Cenário:** Usuário quer converter filmes para diferentes dispositivos:
- Perfil 1: Alta qualidade (4K HEVC) para TV
- Perfil 2: Qualidade média (1080p HEVC) para tablet
- Perfil 3: Baixa qualidade (720p H264) para celular

**Fluxo:**
1. Usuário seleciona pasta com filmes
2. Seleciona os 3 perfis desejados
3. Visualiza preview: "3 arquivos × 3 perfis = 9 jobs"
4. Confirma conversão
5. Sistema cria 9 jobs automaticamente na fila

### Caso de Uso 2: Série com Perfis Diferentes

**Cenário:** Usuário quer converter uma série com diferentes configurações:
- Episódios 1-5: Perfil "NVIDIA Series 1080p HEVC"
- Episódios 6-10: Perfil "NVIDIA Series 4K HEVC"

**Fluxo:**
1. Usuário seleciona episódios 1-5
2. Seleciona perfil "Series 1080p"
3. Adiciona à fila
4. Seleciona episódios 6-10
5. Seleciona perfil "Series 4K"
6. Adiciona à fila

*Nota: Este caso já é suportado parcialmente. A melhoria permite fazer tudo em uma única operação.*

### Caso de Uso 3: Teste de Qualidade

**Cenário:** Usuário quer testar qual perfil produz melhor resultado:
- Mesmo arquivo com 5 perfis diferentes
- Comparar qualidade/tamanho final

**Fluxo:**
1. Usuário seleciona 1 arquivo de teste
2. Seleciona 5 perfis para comparação
3. Visualiza preview: "1 arquivo × 5 perfis = 5 jobs"
4. Confirma conversão
5. Sistema cria 5 jobs com o mesmo input, outputs diferentes

## Regras de Negócio

1. **Validação de Perfis:**
   - Perfis devem existir no ProfileManager
   - Perfis incompatíveis (ex: mesmo codec com configurações conflitantes) devem gerar aviso

2. **Nomenclatura de Output:**
   - Para múltiplos perfis, o output deve incluir identificador do perfil
   - Exemplo: `filme_4k_hevc.mkv`, `filme_1080p_hevc.mkv`

3. **Estrutura de Diretórios:**
   - Opção de preservar estrutura original
   - Opção de agrupar por perfil ou por arquivo original

4. **Prioridade na Fila:**
   - Jobs do mesmo grupo podem ter prioridade agrupada
   - Opção de processar todos os jobs de um arquivo antes do próximo

## Considerações de Performance

1. **Geração de Jobs em Lote:**
   - Criar todos os jobs de uma vez é mais eficiente que um por um
   - Usar transações para persistência

2. **Preview sem Criação:**
   - Gerar plano sem criar jobs permite preview rápido
   - Jobs só são criados após confirmação

3. **Memória:**
   - Para muitos arquivos × muitos perfis, o plano pode ser grande
   - Implementar paginação no preview se necessário

## Critérios de Aceite

- [ ] Usuário pode selecionar múltiplos perfis de uma vez
- [ ] Sistema gera preview preciso do total de jobs
- [ ] Jobs são criados com nomenclatura clara e organizada
- [ ] Interface é intuitiva e não sobrecarrega o usuário
- [ ] Fila gerencia jobs múltiplos corretamente
- [ ] Progresso é exibido de forma agrupada e individual
