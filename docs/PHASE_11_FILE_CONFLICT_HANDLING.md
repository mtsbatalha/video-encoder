# Phase 11: File Conflict Handling & Output Folder Naming

## Visão Geral

Esta implementação adiciona funcionalidades para lidar com conflitos de arquivos existentes durante a conversão e validação do nome da pasta de saída.

## Funcionalidades Implementadas

### 1. Detecção de Arquivo Existente

Quando um arquivo de saída já existe, o sistema agora oferece três opções:

1. **Substituir (Overwrite)**: Substitui o arquivo existente
2. **Renomear (Rename)**: Cria uma cópia numerada automaticamente (ex: `arquivo_1.mkv`, `arquivo_2.mkv`)
3. **Pular (Skip)**: Ignora o arquivo e não faz nada

### 2. Comportamento por Modo

#### Modo Interativo (CLI/UI)
- **Pergunta ao usuário** o que fazer quando um arquivo existe
- Menu interativo com opções claras
- Mostra o novo caminho quando renomeia automaticamente

#### Watch Folder / Pasta Recorrente
- **Automático** - não pergunta ao usuário
- Usa configuração `skip_existing_output` e `rename_existing_output`
- Três comportamentos possíveis:
  - `skip_existing_output=True`: Pula arquivos existentes
  - `rename_existing_output=True`: Renomeia automaticamente com numeração
  - Ambos `False`: Substitui arquivos existentes

### 3. Validação do Nome da Pasta

O sistema agora verifica se o nome da pasta de saída inclui:
- Codec (ex: `hevc`, `h264`, `av1`)
- Qualidade/Resolução (ex: `1080`, `720`)

Se o nome não seguir o padrão, uma sugestão é apresentada.

## Arquivos Modificados

### 1. `src/utils/file_utils.py`

**Novas Classes e Funções:**

```python
class FileConflictStrategy(Enum):
    """Estratégias para lidar com conflitos de arquivos existentes."""
    OVERWRITE = "overwrite"
    RENAME = "rename"
    SKIP = "skip"
    ASK = "ask"
```

```python
@staticmethod
def resolve_file_conflict(
    output_path: str,
    interactive: bool = False,
    console=None
) -> Tuple[FileConflictStrategy, str]:
    """
    Resolve conflito de arquivo existente.
    
    Returns:
        Tuple com (estratégia, caminho_final)
    """
```

```python
@staticmethod
def generate_unique_filename(path: str) -> str:
    """
    Gera nome único para arquivo adicionando numeração.
    
    Exemplos:
        filme.mkv -> filme_1.mkv
        filme_1.mkv -> filme_2.mkv
        filme_cq20.mkv -> filme_cq20_1.mkv
    """
```

```python
@staticmethod
def validate_output_folder_name(
    folder_path: str,
    expected_name_pattern: Optional[str] = None,
    codec: Optional[str] = None,
    quality: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Valida se o nome da pasta de saída segue o padrão esperado.
    
    Returns:
        Tuple com (é_válido, mensagem, nome_sugerido)
    """
```

```python
@staticmethod
def generate_output_folder_name(
    base_name: str,
    codec: str,
    quality: Optional[str] = None,
    cq: Optional[str] = None
) -> str:
    """
    Gera nome de pasta de saída com codec e qualidade.
    """
```

### 2. `src/utils/path_utils.py`

**Alterações:**

```python
@staticmethod
def generate_output_path(
    input_path: str,
    output_dir: str,
    suffix: Optional[str] = None,
    extension: Optional[str] = None,
    codec: Optional[str] = None,
    cq: Optional[str] = None,
    handle_conflict: bool = True  # NOVO parâmetro
) -> str:
    """
    Gera caminho de output baseado no input.
    
    Args:
        handle_conflict: Se True, gera nome único se arquivo existir (default: True)
    """
```

### 3. `src/cli.py`

**Alterações no Modo de Arquivo Único:**

```python
# Verificar conflito de arquivo existente (modo interativo)
if Path(output_path).exists():
    console.print(f"\n[yellow]⚠️  Arquivo já existe:[/yellow] {output_path}")
    console.print("[cyan]O que deseja fazer?[/cyan]")
    
    # Opção 1: Substituir
    if Confirm.ask("\nDeseja [bold red]substituir[/bold red] o arquivo existente?", default=False):
        strategy = FileConflictStrategy.OVERWRITE
    # Opção 2: Renomear com numeração
    elif Confirm.ask("Deseja [bold green]criar uma cópia numerada[/bold green] (ex: arquivo_1.mkv)?", default=True):
        strategy = FileConflictStrategy.RENAME
        output_path = FileUtils.generate_unique_filename(output_path)
        console.print(f"[cyan]Novo caminho:[/cyan] {output_path}")
    # Opção 3: Pular
    else:
        console.print("[yellow]Arquivo pulado.[/yellow]")
        return
```

**Alterações no Modo Pasta:**

- Validação do nome da pasta de saída
- Sugestão de nome se não seguir padrão
- Loop por arquivos com verificação individual de conflitos

### 4. `src/ui/recurrent_folder_ui.py`

**Nova Opção na UI:**

```python
self.menu.console.print("\n[cyan]Como lidar com arquivos já existentes no output?[/cyan]")
self.menu.console.print("  [1] Pular arquivo (não fazer nada)")
self.menu.console.print("  [2] Criar cópia numerada automaticamente (ex: arquivo_1.mkv)")
self.menu.console.print("  [3] Substituir arquivo existente (PERIGO: perde o arquivo original)")

conflict_choice = self.menu.ask_int("Escolha uma opção", default=2)
```

**Novas Opções Salvas:**

```python
"options": {
    "preserve_subdirectories": preserve_subdirs,
    "skip_existing_output": skip_existing,
    "rename_existing_output": rename_existing,  # NOVO
    "delete_source_after_encode": delete_source,
    "copy_subtitles": copy_subtitles,
    ...
}
```

### 5. `src/core/watch_folder_monitor.py`

**Nova Configuração:**

```python
self.rename_existing_output = config.get('rename_existing_output', False)
```

**Lógica Atualizada no `_enqueue_file`:**

```python
if output_path.exists():
    if self.skip_existing_output:
        # Pula o arquivo
        self.logger.info(f"Output já existe, pulando: {output_path}")
        return
    elif self.rename_existing_output:
        # Renomeia automaticamente
        output_path = Path(FileUtils.generate_unique_filename(str(output_path)))
        self.logger.info(f"Output já existe, usando nome alternativo: {output_path}")
    # else: substitui o arquivo existente
```

## Exemplos de Uso

### CLI - Arquivo Único

```bash
# Modo interativo (pergunta quando arquivo existe)
python -m src.cli -f filme.mkv -p "4K HEVC"

# O sistema perguntará se o arquivo já existir:
# ⚠️  Arquivo já existe: /output/filme_hevc_cq20.mkv
# O que deseja fazer?
#   Deseja substituir o arquivo existente? (y/N)
#   Deseja criar uma cópia numerada (ex: arquivo_1.mkv)? (Y/n)
```

### CLI - Pasta

```bash
# Processa pasta inteira (pergunta para cada arquivo existente)
python -m src.cli -F /videos -p "1080p HEVC" -o /output
```

### UI - Pasta Recorrente

1. Menu → Gerenciador de Pastas Recorrentes
2. Adicionar nova pasta recorrente
3. Na tela de configurações:
   ```
   Como lidar com arquivos já existentes no output?
     [1] Pular arquivo (não fazer nada)
     [2] Criar cópia numerada automaticamente
     [3] Substituir arquivo existente
   Escolha uma opção: 2
   ```

### Configuração JSON

```json
{
  "recurrent_folders": [
    {
      "name": "Filmes 4K",
      "input_directory": "/videos/filmes",
      "output_directory": "/output/filmes_4k_hevc_cq20",
      "profile_id": "abc123",
      "options": {
        "skip_existing_output": false,
        "rename_existing_output": true,
        "preserve_subdirectories": true
      }
    }
  ]
}
```

## Validação do Nome da Pasta

O sistema valida se o nome da pasta inclui informações do codec e qualidade:

```python
# Exemplo de validação
is_valid, msg, suggested = FileUtils.validate_output_folder_name(
    "/output/filmes",
    codec="hevc_nvenc",
    quality="1080"
)

# Se o nome não incluir "hevc" e "1080":
# is_valid = False
# msg = "Codec 'hevc' não está no nome da pasta, Qualidade '1080' não está no nome da pasta"
# suggested = "filmes_1080_hevc"
```

## Considerações de Segurança

1. **Substituição de Arquivos**: A opção de substituir é claramente marcada como perigosa na UI
2. **Numeração Automática**: O sistema usa numeração incremental (_1, _2, etc.) para evitar sobrescrita acidental
3. **Watch Folder Automático**: Por padrão, watch folders são configuradas para pular ou renomear, nunca substituir

## Testes Sugeridos

1. **Teste de Conflito - Modo Interativo**:
   - Criar arquivo de output existente
   - Executar conversão
   - Verificar se menu de opções aparece
   - Testar cada opção (substituir, renomear, pular)

2. **Teste de Conflito - Watch Folder**:
   - Configurar pasta recorrente com `rename_existing_output=True`
   - Adicionar arquivo que gera output existente
   - Verificar se arquivo é renomeado automaticamente

3. **Teste de Validação de Pasta**:
   - Criar pasta recorrente com nome genérico
   - Verificar se sugestão de nome é apresentada
   - Aceitar sugestão e verificar se nome é atualizado

## Histórico de Versões

- **v1.0** (2026-04-01): Implementação inicial
  - Enum FileConflictStrategy
  - Funções utilitárias em file_utils.py
  - Integração CLI e UI
  - Suporte a watch folder
