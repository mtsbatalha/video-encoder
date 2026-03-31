# Implementation Plan: Multi-Profile Conversion

## Visão Geral

Este plano descreve a implementação do suporte à conversão multi-perfil em 4 fases principais, com tarefas específicas e agentes especializados designados para cada etapa.

## Timeline de Implementação

```
┌─────────────────────────────────────────────────────────────┐
│  FASE 1          FASE 2          FASE 3          FASE 4     │
│  Core            Utils           UI              Integração  │
│  ─────           ─────           ─────           ──────────  │
│  • Manager       • file_utils    • menu.py       • cli.py    │
│  • Dataclasses   • path_utils    • multi_prof    • testes    │
│  • Validação     • naming        • preview       • docs      │
└─────────────────────────────────────────────────────────────┘
```

---

## FASE 1: Core Manager (Backend Specialist)

### Objetivo
Criar o `MultiProfileConversionManager` com toda a lógica de negócio.

### Tarefas

#### 1.1. Criar estrutura do manager
**Agente:** Backend Specialist  
**Arquivo:** `src/managers/multi_profile_conversion_manager.py`

```python
# Estrutura inicial
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .profile_manager import ProfileManager
from .job_manager import JobManager
from .queue_manager import QueueManager, QueuePriority


@dataclass
class PlannedJob:
    """Job planejado para conversão."""
    input_path: str
    output_path: str
    profile_id: str
    profile_name: str
    estimated_output_size: int
    priority: QueuePriority
    group_id: Optional[str] = None


@dataclass
class ConversionPlan:
    """Plano de conversão multi-perfil."""
    input_files: List[str]
    profiles: List[Dict[str, Any]]
    total_jobs: int
    jobs: List[PlannedJob]
    estimated_total_size: int
    created_at: str
    options: Dict[str, Any]


class MultiProfileConversionManager:
    def __init__(
        self,
        profile_manager: ProfileManager,
        job_manager: JobManager,
        queue_manager: QueueManager
    ):
        self.profile_mgr = profile_manager
        self.job_mgr = job_manager
        self.queue_mgr = queue_manager
```

#### 1.2. Implementar método `generate_conversion_plan()`
**Agente:** Backend Specialist

```python
def generate_conversion_plan(
    self,
    input_files: List[str],
    profile_ids: List[str],
    output_folder: str,
    options: Optional[Dict[str, Any]] = None
) -> ConversionPlan:
    """
    Gera plano de conversão sem criar jobs.
    
    Args:
        input_files: Lista de arquivos de entrada
        profile_ids: Lista de IDs de perfis
        output_folder: Pasta de saída
        options: Opções adicionais
        
    Returns:
        Objeto ConversionPlan
    """
    # 1. Carregar perfis
    profiles = []
    for profile_id in profile_ids:
        profile = self.profile_mgr.get_profile(profile_id)
        if profile:
            profiles.append(profile)
    
    # 2. Gerar jobs planejados
    planned_jobs = []
    total_size = 0
    
    for input_file in input_files:
        for profile in profiles:
            output_path = self._generate_output_path(
                input_file, profile, output_folder, options
            )
            estimated_size = self._estimate_output_size(input_file, profile)
            
            planned_jobs.append(PlannedJob(
                input_path=input_file,
                output_path=output_path,
                profile_id=profile['id'],
                profile_name=profile['name'],
                estimated_output_size=estimated_size,
                priority=QueuePriority.NORMAL,
                group_id=Path(input_file).stem
            ))
            
            total_size += estimated_size
    
    return ConversionPlan(
        input_files=input_files,
        profiles=profiles,
        total_jobs=len(planned_jobs),
        jobs=planned_jobs,
        estimated_total_size=total_size,
        created_at=datetime.now().isoformat(),
        options=options or {}
    )
```

#### 1.3. Implementar método `create_jobs_for_multiple_profiles()`
**Agente:** Backend Specialist

```python
def create_jobs_for_multiple_profiles(
    self,
    input_files: List[str],
    profile_ids: List[str],
    output_folder: str,
    options: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Cria jobs para múltiplos perfis.
    
    Returns:
        Lista de jobs criados
    """
    jobs_created = []
    
    for input_file in input_files:
        for profile_id in profile_ids:
            profile = self.profile_mgr.get_profile(profile_id)
            if not profile:
                continue
            
            output_path = self._generate_output_path(
                input_file, profile, output_folder, options
            )
            
            # Criar job
            job_id = self.job_mgr.create_job(
                input_path=input_file,
                output_path=output_path,
                profile_id=profile_id,
                profile_name=profile['name']
            )
            
            # Adicionar à fila
            self.queue_mgr.add_to_queue(
                job_id=job_id,
                input_path=input_file,
                output_path=output_path,
                profile=profile,
                priority=QueuePriority.NORMAL
            )
            
            jobs_created.append({
                'job_id': job_id,
                'input_path': input_file,
                'output_path': output_path,
                'profile_id': profile_id,
                'profile_name': profile['name']
            })
    
    return jobs_created
```

#### 1.4. Implementar método `validate_profiles_compatibility()`
**Agente:** Backend Specialist

```python
def validate_profiles_compatibility(
    self,
    profile_ids: List[str]
) -> tuple[bool, str]:
    """
    Valida se perfis são compatíveis entre si.
    
    Returns:
        Tuple (é_compatível, mensagem_erro)
    """
    if not profile_ids:
        return (False, "Nenhum perfil selecionado")
    
    profiles = []
    for profile_id in profile_ids:
        profile = self.profile_mgr.get_profile(profile_id)
        if not profile:
            return (False, f"Perfil não encontrado: {profile_id}")
        profiles.append(profile)
    
    # Verificar duplicatas
    profile_names = [p['name'] for p in profiles]
    if len(profile_names) != len(set(profile_names)):
        return (False, "Perfis duplicados selecionados")
    
    # Verificar conflitos (ex: mesmo codec com configurações muito diferentes)
    # Por enquanto,允许 qualquer combinação
    
    return (True, "Perfis compatíveis")
```

#### 1.5. Implementar métodos auxiliares
**Agente:** Backend Specialist

```python
def _generate_output_path(
    self,
    input_file: str,
    profile: Dict[str, Any],
    output_folder: str,
    options: Optional[Dict[str, Any]] = None
) -> str:
    """Gera caminho de output único para arquivo + perfil."""
    from pathlib import Path
    
    input_path = Path(input_file)
    profile_suffix = self._get_profile_suffix(profile)
    
    # Nome base: nome_do_arquivo + sufixo do perfil
    output_filename = f"{input_path.stem}_{profile_suffix}{input_path.suffix}"
    
    # Preservar estrutura de diretórios se opção estiver habilitada
    if options and options.get('preserve_structure', True):
        output_dir = Path(output_folder) / input_path.parent.relative_to(input_path.parent.anchor)
    else:
        output_dir = Path(output_folder)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir / output_filename)


def _get_profile_suffix(self, profile: Dict[str, Any]) -> str:
    """Gera sufixo único baseado no perfil."""
    codec = profile.get('codec', 'unknown')
    resolution = profile.get('resolution', 'auto')
    cq = profile.get('cq', '')
    
    parts = []
    if resolution:
        parts.append(resolution)
    parts.append(codec.replace('_nvenc', '').replace('_amf', '').replace('_qsv', ''))
    if cq:
        parts.append(f'cq{cq}')
    
    return '_'.join(parts)


def _estimate_output_size(self, input_file: str, profile: Dict[str, Any]) -> int:
    """Estima tamanho do output."""
    from pathlib import Path
    
    input_path = Path(input_file)
    if not input_path.exists():
        return 0
    
    input_size = input_path.stat().st_size
    
    if profile.get('bitrate'):
        # Calcular baseado no bitrate
        bitrate = self._parse_bitrate(profile['bitrate'])
        # Obter duração do vídeo (simplificado)
        duration = 3600  # Assume 1 hora como fallback
        return int(bitrate * duration / 8)
    elif profile.get('cq'):
        # Fator de compressão baseado no CQ
        cq = int(profile['cq'])
        compression_factor = 0.1 + (cq / 51) * 0.4
        return int(input_size * compression_factor)
    else:
        return int(input_size * 0.3)


def _parse_bitrate(self, bitrate_str: str) -> int:
    """Parse string de bitrate para bits/segundo."""
    bitrate_str = bitrate_str.upper()
    multiplier = 1
    
    if bitrate_str.endswith('M'):
        multiplier = 1_000_000
        bitrate_str = bitrate_str[:-1]
    elif bitrate_str.endswith('K'):
        multiplier = 1_000
        bitrate_str = bitrate_str[:-1]
    
    return int(float(bitrate_str) * multiplier)
```

---

## FASE 2: Utilitários (Backend Specialist)

### Objetivo
Estender utilitários existentes para suportar nomenclatura e estimativas.

### Tarefas

#### 2.1. Estender `file_utils.py` com funções de nomenclatura
**Agente:** Backend Specialist  
**Arquivo:** `src/utils/file_utils.py`

```python
@staticmethod
def generate_output_filename_for_profile(
    input_path: str,
    profile: Dict[str, Any],
    output_folder: str,
    preserve_structure: bool = True
) -> str:
    """
    Gera nome de arquivo de output baseado no perfil.
    
    Padrão: {nome_original}_{perfil}.{ext}
    Exemplo: filme_4k_hevc.mkv
    """
    from pathlib import Path
    
    input_file = Path(input_path)
    profile_suffix = FileUtils._get_profile_suffix(profile)
    
    output_name = f"{input_file.stem}_{profile_suffix}{input_file.suffix}"
    
    if preserve_structure:
        output_dir = Path(output_folder) / input_file.parent.name
    else:
        output_dir = Path(output_folder)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir / output_name)


@staticmethod
def _get_profile_suffix(profile: Dict[str, Any]) -> str:
    """Gera sufixo do perfil para nomenclatura."""
    codec = profile.get('codec', 'unknown')
    resolution = profile.get('resolution', '')
    cq = profile.get('cq', '')
    
    # Extrair nome curto do codec
    codec_short = codec.replace('_nvenc', '').replace('_amf', '').replace('_qsv', '')
    
    parts = []
    if resolution:
        parts.append(resolution)
    parts.append(codec_short)
    if cq:
        parts.append(f'cq{cq}')
    
    return '_'.join(parts)
```

#### 2.2. Estender `path_utils.py` se necessário
**Agente:** Backend Specialist

---

## FASE 3: Interface de Usuário (Frontend Specialist)

### Objetivo
Adicionar UI para seleção múltipla de perfis e preview do plano.

### Tarefas

#### 3.1. Adicionar método `show_multi_profile_selection()` no Menu
**Agente:** Frontend Specialist  
**Arquivo:** `src/ui/menu.py`

```python
def show_multi_profile_selection(
    self,
    profiles: List[Dict[str, Any]],
    title: str = "Selecione os Perfis"
) -> List[str]:
    """
    Exibe interface para seleção múltipla de perfis.
    Usa checkboxes simulados com [x] e [ ].
    
    Returns:
        Lista de IDs de perfis selecionados
    """
    selected = set()
    
    while True:
        self.console.print(f"\n[bold]{title}[/bold]")
        self.console.print("[dim](Digite o número para selecionar/desmarcar, Enter para confirmar)[/dim]\n")
        
        table = Table(title="Perfis Disponíveis", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Selecionado", style="white", width=14)
        table.add_column("Nome", style="cyan", width=40)
        table.add_column("Codec", style="green", width=15)
        table.add_column("CQ", style="yellow", width=8)
        
        for i, profile in enumerate(profiles, 1):
            selected_mark = "[green][x] Selecionado[/green]" if profile['id'] in selected else "[dim][ ][/dim]"
            table.add_row(
                str(i),
                selected_mark,
                profile.get('name', 'N/A')[:38],
                profile.get('codec', '')[:13],
                profile.get('cq', '-') or '-'
            )
        
        self.console.print(table)
        
        if selected:
            self.console.print(f"\n[green]Perfis selecionados: {len(selected)}[/green]")
        
        choice = self.ask("Número do perfil (ou Enter para confirmar)", default="")
        
        if not choice:
            if selected:
                break
            else:
                self.print_warning("Selecione pelo menos um perfil")
                continue
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(profiles):
                profile_id = profiles[idx]['id']
                if profile_id in selected:
                    selected.remove(profile_id)
                    self.print_info(f"Perfil desmarcado: {profiles[idx]['name']}")
                else:
                    selected.add(profile_id)
                    self.print_success(f"Perfil selecionado: {profiles[idx]['name']}")
            else:
                self.print_error("Número inválido")
        except ValueError:
            self.print_error("Entrada inválida")
    
    return list(selected)
```

#### 3.2. Adicionar método `show_conversion_plan_preview()` no Menu
**Agente:** Frontend Specialist  
**Arquivo:** `src/ui/menu.py`

```python
def show_conversion_plan_preview(
    self,
    plan: 'ConversionPlan'
) -> int:
    """
    Exibe preview do plano de conversão.
    
    Returns:
        Índice da ação escolhida:
        0 - Confirmar e adicionar à fila
        1 - Editar perfis
        2 - Cancelar
    """
    from rich.panel import Panel
    from rich.text import Text
    
    self.console.print()
    
    # Painel de resumo
    summary = Text()
    summary.append("📊 RESUMO DA CONVERSÃO\n\n", style="bold magenta")
    summary.append("Arquivos de entrada: ", style="cyan")
    summary.append(f"{len(plan.input_files)}\n", style="white")
    summary.append("Perfis selecionados: ", style="cyan")
    summary.append(f"{len(plan.profiles)}\n", style="white")
    summary.append("Total de jobs: ", style="bold yellow")
    summary.append(f"{plan.total_jobs}\n\n", style="bold yellow")
    
    # Calcular tamanho estimado
    total_gb = plan.estimated_total_size / (1024 ** 3)
    summary.append("Tamanho estimado de saída: ", style="cyan")
    summary.append(f"{total_gb:.2f} GB\n", style="green")
    
    self.console.print(Panel(summary, border_style="magenta", title="⚙️ Plano de Conversão"))
    self.console.print()
    
    # Tabela de matriz de conversão
    table = Table(title="Matriz de Conversão", show_header=True, header_style="bold cyan")
    table.add_column("Arquivo", style="white", width=40)
    
    for profile in plan.profiles:
        table.add_column(
            profile.get('name', 'N/A')[:20],
            style="green",
            width=22
        )
    
    # Agrupar jobs por arquivo de entrada
    from collections import defaultdict
    jobs_by_file = defaultdict(list)
    for job in plan.jobs:
        jobs_by_file[job.input_path].append(job)
    
    for input_file, jobs in jobs_by_file.items():
        row = [Path(input_file).name[:38]]
        for profile in plan.profiles:
            matching_jobs = [j for j in jobs if j.profile_id == profile['id']]
            if matching_jobs:
                row.append("[green]✓[/green]")
            else:
                row.append("[dim]-[/dim]")
        table.add_row(*row)
    
    self.console.print(table)
    self.console.print()
    
    # Menu de ações
    options = [
        {"description": "✅ Confirmar e adicionar jobs à fila", "shortcut": "1"},
        {"description": "✏️ Editar perfis", "shortcut": "2"},
        {"description": "❌ Cancelar", "shortcut": "3"}
    ]
    
    choice = self.show_menu("Ações", options)
    return choice
```

#### 3.3. (Opcional) Criar módulo `multi_profile_ui.py`
**Agente:** Frontend Specialist

---

## FASE 4: Integração e CLI (Backend Specialist)

### Objetivo
Integrar nova funcionalidade ao fluxo existente do CLI.

### Tarefas

#### 4.1. Modificar `run_folder_conversion_cli()` no `cli.py`
**Agente:** Backend Specialist  
**Arquivo:** `src/cli.py`

```python
def run_folder_conversion_cli(
    config: ConfigManager,
    profile_mgr: ProfileManager,
    job_mgr: JobManager,
    queue_mgr: QueueManager,
    stats_mgr: StatsManager
):
    """Fluxo de conversão de pasta com suporte multi-perfil."""
    from .managers.multi_profile_conversion_manager import MultiProfileConversionManager
    
    menu = Menu(console)
    
    # ... (código existente para selecionar pasta e output)
    
    # Seleção de perfis (MODIFICADO)
    profiles = profile_mgr.list_profiles()
    
    # Perguntar se deseja modo multi-perfil
    multi_profile_mode = menu.ask_confirm(
        "Deseja selecionar múltiplos perfis para conversão?",
        default=False
    )
    
    if multi_profile_mode:
        # Modo multi-perfil
        selected_profile_ids = menu.show_multi_profile_selection(profiles)
        
        if not selected_profile_ids:
            menu.print_error("Nenhum perfil selecionado")
            return
        
        # Gerar plano
        multi_mgr = MultiProfileConversionManager(
            profile_manager=profile_mgr,
            job_manager=job_mgr,
            queue_manager=queue_mgr
        )
        
        plan = multi_mgr.generate_conversion_plan(
            input_files=video_files,
            profile_ids=selected_profile_ids,
            output_folder=output_folder
        )
        
        # Exibir preview
        action = menu.show_conversion_plan_preview(plan)
        
        if action == 0:  # Confirmar
            jobs = multi_mgr.create_jobs_for_multiple_profiles(
                input_files=video_files,
                profile_ids=selected_profile_ids,
                output_folder=output_folder
            )
            menu.print_success(f"{len(jobs)} jobs criados e adicionados à fila!")
            console.print(f"[cyan]Fila total: {queue_mgr.get_queue_length()} jobs[/cyan]")
            
            # Perguntar se deseja processar agora
            if menu.ask_confirm("Deseja processar a fila agora?", default=True):
                process_queue_cli(config, job_mgr, queue_mgr, stats_mgr)
        
        elif action == 1:  # Editar perfis
            # Voltar para seleção de perfis
            run_folder_conversion_cli(config, profile_mgr, job_mgr, queue_mgr, stats_mgr)
        
        else:  # Cancelar
            menu.print_warning("Operação cancelada")
            return
    
    else:
        # Modo single-perfil (existente)
        # ... (código existente)
```

#### 4.2. Adicionar opção de linha de comando (opcional)
**Agente:** Backend Specialist  
**Arquivo:** `src/cli.py`

```python
# No create_parser()
parser.add_argument(
    '--multi-profile',
    action='store_true',
    help='Habilitar seleção de múltiplos perfis'
)
parser.add_argument(
    '--profile-id',
    action='append',
    help='ID do perfil (pode ser usado múltiplas vezes)'
)
```

---

## FASE 5: Testes e Documentação

### Tarefas

#### 5.1. Criar testes unitários
**Agente:** Security & QA Tester  
**Arquivo:** `tests/test_multi_profile_conversion.py`

#### 5.2. Atualizar documentação
**Agente:** Documentation Specialist  
**Arquivos:** 
- `README.md` - Adicionar seção sobre multi-profile
- `docs/PHASE_10_MULTI_PROFILE_CONVERSION.md` - Já criado

---

## Resumo das Tarefas por Agente

| Agente | Tarefas |
|--------|---------|
| **Backend Specialist** | FASE 1 (Core Manager), FASE 2 (Utils), FASE 4 (Integração CLI) |
| **Frontend Specialist** | FASE 3 (UI) |
| **Security & QA Tester** | FASE 5 (Testes) |
| **Documentation Specialist** | FASE 5 (Documentação) |

---

## Critérios de Aceite

- [ ] Usuário pode selecionar múltiplos perfis de uma vez
- [ ] Sistema gera preview preciso do total de jobs
- [ ] Jobs são criados com nomenclatura clara
- [ ] Interface é intuitiva
- [ ] Fila gerencia jobs múltiplos corretamente
- [ ] Testes unitários passam
- [ ] Documentação atualizada
