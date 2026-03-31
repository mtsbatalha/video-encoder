# Tech Stack: Multi-Profile Conversion

## Visão Geral

Este documento descreve as tecnologias, bibliotecas e estruturas técnicas necessárias para implementar o suporte à conversão multi-perfil no Video Encoder.

## Stack Existente (Reutilizado)

### Linguagem e Runtime
- **Python 3.10+** - Linguagem principal
- **Pathlib** - Manipulação de caminhos
- **Dataclasses** - Estruturas de dados
- **Typing** - Type hints

### Bibliotecas de UI
- **Rich** - Interface de terminal rica
  - `Console` - Output formatado
  - `Table` - Tabelas
  - `Panel` - Painéis
  - `Prompt` - Input do usuário

### Gerenciadores Existentes
- **ProfileManager** (`src/managers/profile_manager.py`)
  - `list_profiles()` - Listar perfis
  - `get_profile(profile_id)` - Obter perfil específico
  
- **JobManager** (`src/managers/job_manager.py`)
  - `create_job()` - Criar job
  - `update_job_status()` - Atualizar status
  
- **QueueManager** (`src/managers/queue_manager.py`)
  - `add_to_queue()` - Adicionar à fila
  - `list_queue()` - Listar fila

## Novos Componentes

### 1. MultiProfileConversionManager

**Arquivo:** `src/managers/multi_profile_conversion_manager.py`

**Responsabilidades:**
- Gerenciar criação de jobs múltiplos para combinações arquivo × perfil
- Gerar planos de conversão (preview)
- Validar compatibilidade de perfis
- Calcular estimativas de tamanho de output

**Dependências:**
```python
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .profile_manager import ProfileManager
from .job_manager import JobManager
from .queue_manager import QueueManager, QueuePriority
from ..utils.file_utils import FileUtils
```

**Estruturas de Dados:**
```python
@dataclass
class PlannedJob:
    """Job planejado para conversão."""
    input_path: str
    output_path: str
    profile_id: str
    profile_name: str
    estimated_output_size: int  # bytes
    priority: QueuePriority
    group_id: Optional[str] = None  # Para agrupar jobs relacionados

@dataclass
class ConversionPlan:
    """Plano de conversão multi-perfil."""
    input_files: List[str]
    profiles: List[Dict[str, Any]]
    total_jobs: int
    jobs: List[PlannedJob]
    estimated_total_size: int  # bytes
    created_at: str
    options: Dict[str, Any]
```

### 2. Extensões de UI

**Arquivo:** `src/ui/menu.py` (extensão)

**Novos Métodos:**
```python
def show_multi_profile_selection(
    self,
    profiles: List[Dict[str, Any]],
    title: str = "Selecione os Perfis"
) -> List[str]:
    """
    Exibe interface para seleção múltipla de perfis.
    Usa checkboxes simulados com [x] e [ ].
    """

def show_conversion_plan_preview(
    self,
    plan: ConversionPlan
) -> int:
    """
    Exibe preview do plano de conversão.
    Mostra matriz de conversão e estatísticas.
    """
```

### 3. Utilitários de Nomenclatura

**Arquivo:** `src/utils/file_utils.py` (extensão)

**Novas Funções:**
```python
def generate_output_filename_for_profile(
    input_path: str,
    profile: Dict[str, Any],
    output_folder: str,
    preserve_structure: bool = True
) -> str:
    """
    Gera nome de arquivo de output baseado no perfil.
    
    Exemplos:
    - filme_4k_hevc.mkv
    - filme_1080p_h264.mkv
    - serie/s01e01_4k_hevc.mkv
    """

def estimate_output_size(
    input_size: int,
    profile: Dict[str, Any],
    duration_seconds: float
) -> int:
    """
    Estima tamanho do output baseado no perfil.
    Usa CQ/bitrate do perfil para cálculo aproximado.
    """
```

## Estrutura de Arquivos

```
src/
├── managers/
│   ├── multi_profile_conversion_manager.py  (NOVO)
│   ├── profile_manager.py                   (EXISTENTE - estendido)
│   ├── job_manager.py                       (EXISTENTE - estendido)
│   └── queue_manager.py                     (EXISTENTE - estendido)
├── ui/
│   ├── menu.py                              (EXISTENTE - estendido)
│   └── multi_profile_ui.py                  (NOVO - opcional)
├── utils/
│   ├── file_utils.py                        (EXISTENTE - estendido)
│   └── path_utils.py                        (EXISTENTE)
└── core/
    ├── encoder_engine.py                    (EXISTENTE)
    └── ffmpeg_wrapper.py                    (EXISTENTE)
```

## Configurações e Environment Variables

### Configurações do Sistema (config.json)

```json
{
  "multi_profile": {
    "max_profiles_per_conversion": 10,
    "max_files_per_batch": 100,
    "default_priority": "NORMAL",
    "group_jobs_by_file": true,
    "naming_convention": "profile_suffix",
    "preserve_directory_structure": true
  }
}
```

### Opções de Nomenclatura

| Opção | Descrição | Exemplo |
|-------|-----------|---------|
| `profile_suffix` | Adiciona sufixo do perfil | `filme_4k_hevc.mkv` |
| `profile_prefix` | Adiciona prefixo do perfil | `4k_hevc_filme.mkv` |
| `subfolder` | Cria subpasta por perfil | `4k_hevc/filme.mkv` |

## Algoritmos

### 1. Geração de Jobs

```python
def create_jobs_for_multiple_profiles(
    input_files: List[str],
    profile_ids: List[str],
    output_folder: str
) -> List[Dict]:
    """
    Algoritmo:
    1. Para cada arquivo de entrada
    2.   Para cada perfil selecionado
    3.     Gerar caminho de output único
    4.     Criar job com metadata de grupo
    5.     Adicionar à fila
    6. Retornar lista de jobs criados
    """
    jobs_created = []
    
    for input_file in input_files:
        for profile_id in profile_ids:
            profile = profile_manager.get_profile(profile_id)
            output_path = generate_output_filename_for_profile(
                input_file, profile, output_folder
            )
            
            job_id = job_manager.create_job(
                input_path=input_file,
                output_path=output_path,
                profile_id=profile_id,
                profile_name=profile['name']
            )
            
            queue_manager.add_to_queue(
                job_id=job_id,
                input_path=input_file,
                output_path=output_path,
                profile=profile,
                priority=QueuePriority.NORMAL
            )
            
            jobs_created.append({
                'job_id': job_id,
                'input': input_file,
                'output': output_path,
                'profile': profile['name']
            })
    
    return jobs_created
```

### 2. Estimativa de Tamanho

```python
def estimate_output_size(input_size, profile, duration):
    """
    Calcula estimativa baseada em:
    - CQ (Constant Quality): fator de compressão estimado
    - Bitrate: cálculo direto (bitrate × duration)
    """
    if profile.get('bitrate'):
        # Parse bitrate (ex: "10M" → 10000000)
        bitrate = parse_bitrate(profile['bitrate'])
        return int(bitrate * duration / 8)  # bits → bytes
    elif profile.get('cq'):
        # Fator de compressão estimado baseado no CQ
        cq = int(profile['cq'])
        # CQ menor = maior qualidade = maior arquivo
        compression_factor = 0.1 + (cq / 51) * 0.4  # 0.1 a 0.5
        return int(input_size * compression_factor)
    else:
        # Fallback: estimativa conservadora
        return int(input_size * 0.3)
```

## Integração com Sistema Existente

### Fluxo de Integração

```
┌─────────────────────────────────────────────────────────────┐
│                    run_folder_conversion_cli()               │
│                         (cli.py)                             │
│                                                              │
│  1. Selecionar arquivos                                      │
│  2. [NOVO] Selecionar múltiplos perfis                       │
│  3. Gerar plano de conversão                                 │
│  4. Exibir preview                                           │
│  5. Confirmar                                                │
│  6. [EXISTENTE] Criar jobs e adicionar à fila                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              MultiProfileConversionManager                   │
│                                                              │
│  - Valida seleção                                            │
│  - Gera plano                                                │
│  - Cria jobs em lote                                         │
└─────────────────────────────────────────────────────────────┘
```

### Modificações no Código Existente

#### 1. `src/cli.py` - `run_folder_conversion_cli()`

**Adicionar após seleção de perfil:**
```python
# Perguntar se deseja adicionar mais perfis
additional_profiles = []
while menu.ask_confirm("Deseja adicionar outro perfil?", default=False):
    profile_idx = menu.show_options(
        [p['name'] for p in profiles],
        "Perfil adicional"
    )
    additional_profiles.append(profiles[profile_idx]['id'])

# Se houver perfis adicionais, usar multi-profile manager
if additional_profiles:
    all_profile_ids = [profile['id']] + additional_profiles
    plan = multi_profile_mgr.generate_conversion_plan(
        input_files=video_files,
        profile_ids=all_profile_ids,
        output_folder=output_folder
    )
    
    # Exibir preview
    action = menu.show_conversion_plan_preview(plan)
    
    if action == 0:  # Confirmar
        jobs = multi_profile_mgr.create_jobs_for_multiple_profiles(
            input_files=video_files,
            profile_ids=all_profile_ids,
            output_folder=output_folder
        )
        menu.print_success(f"{len(jobs)} jobs criados!")
```

#### 2. `src/ui/menu.py` - Novo método

```python
def show_multi_profile_selection(self, profiles, title="Perfis"):
    """Interface de seleção múltipla com checkboxes."""
    selected = set()
    
    while True:
        self.console.print(f"\n[bold]{title}[/bold]")
        self.console.print("[dim](Enter para confirmar, número para selecionar)[/dim]\n")
        
        table = Table()
        table.add_column("#", width=4)
        table.add_column("Selecionado", width=12)
        table.add_column("Nome", width=40)
        table.add_column("Codec", width=15)
        
        for i, profile in enumerate(profiles, 1):
            selected_mark = "[green][x] Selecionado[/green]" if profile['id'] in selected else "[dim][ ][/dim]"
            table.add_row(
                str(i),
                selected_mark,
                profile['name'],
                profile.get('codec', '')
            )
        
        self.console.print(table)
        
        choice = self.ask("Número do perfil (ou Enter para confirmar)", default="")
        
        if not choice:
            break
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(profiles):
                profile_id = profiles[idx]['id']
                if profile_id in selected:
                    selected.remove(profile_id)
                else:
                    selected.add(profile_id)
        except ValueError:
            pass
    
    return list(selected)
```

## Testes

### Testes Unitários

**Arquivo:** `tests/test_multi_profile_conversion.py`

```python
class TestMultiProfileConversionManager:
    
    def test_create_jobs_for_multiple_profiles(self):
        """Testa criação de jobs para múltiplos perfis."""
        input_files = ['video1.mp4', 'video2.mp4']
        profile_ids = ['profile_1', 'profile_2']
        
        jobs = manager.create_jobs_for_multiple_profiles(
            input_files=input_files,
            profile_ids=profile_ids,
            output_folder='/output'
        )
        
        assert len(jobs) == 4  # 2 arquivos × 2 perfis
        
    def test_generate_conversion_plan(self):
        """Testa geração de plano de conversão."""
        plan = manager.generate_conversion_plan(
            input_files=['video1.mp4'],
            profile_ids=['profile_1', 'profile_2'],
            output_folder='/output'
        )
        
        assert plan.total_jobs == 2
        assert len(plan.jobs) == 2
        
    def test_validate_profiles_compatibility(self):
        """Testa validação de compatibilidade."""
        is_valid, message = manager.validate_profiles_compatibility(
            profile_ids=['profile_1', 'profile_2']
        )
        
        assert is_valid == True
```

### Testes de Integração

```python
def test_full_multi_profile_workflow():
    """Testa fluxo completo de conversão multi-perfil."""
    # Setup
    input_files = create_test_videos(3)
    profile_ids = create_test_profiles(2)
    
    # Executar
    plan = manager.generate_conversion_plan(
        input_files=input_files,
        profile_ids=profile_ids,
        output_folder=temp_output_dir
    )
    
    jobs = manager.create_jobs_for_multiple_profiles(
        input_files=input_files,
        profile_ids=profile_ids,
        output_folder=temp_output_dir
    )
    
    # Validar
    assert len(jobs) == 6  # 3 × 2
    assert queue_manager.get_queue_length() == 6
```

## Considerações de Performance

1. **Criação em Lote de Jobs:**
   - Usar transações únicas para salvar todos os jobs
   - Evitar múltiplas operações de I/O

2. **Cache de Perfis:**
   - Carregar todos os perfis uma vez no início
   - Reutilizar em vez de buscar do disco repetidamente

3. **Estimativa de Tamanho:**
   - Usar cache para arquivos repetidos
   - Calcular apenas uma vez por arquivo único

## Segurança

1. **Validação de Caminhos:**
   - Sanitizar nomes de arquivo de output
   - Prevenir path traversal

2. **Limites de Recursos:**
   - Limitar máximo de perfis por conversão (configurável)
   - Limitar máximo de arquivos por batch

3. **Permissões:**
   - Verificar permissão de escrita no output
   - Validar acesso aos arquivos de entrada
