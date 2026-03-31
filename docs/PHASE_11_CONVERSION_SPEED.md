# Phase 11: Conversion Speed Feature

## Visão Geral
Implementação da feature de velocidade de conversão nos perfis de encoding, permitindo que usuários selecionem entre 4 níveis de velocidade (very_fast, fast, medium, slow) que são automaticamente traduzidos para presets específicos de cada hardware.

## Data de Implementação
2026-03-31

## Arquivos Modificados

### 1. `src/managers/profile_manager.py`
**Mudanças:**
- Adicionado dicionário `SPEED_TO_PRESET` com mapeamento de velocidades para presets por categoria de hardware
- Adicionado campo `conversion_speed` em todos os perfis do `DEFAULT_PROFILES`
- Adicionado método `get_preset_from_speed()` para traduzir velocidade para preset específico
- Adicionado método `get_conversion_speeds()` para listar velocidades disponíveis
- Adicionado método `update_profile_conversion_speed()` para atualizar velocidade de um perfil
- Atualizado método `create_profile()` para aceitar parâmetros `conversion_speed` e `hardware_category`

**Novas APIs:**
```python
# Mapeamento de velocidades
SPEED_TO_PRESET = {
    'nvidia_gpu': {'very_fast': 'p2', 'fast': 'p3', 'medium': 'p5', 'slow': 'p6'},
    'amd_gpu': {'very_fast': 'speed', 'fast': 'speed', 'medium': 'balanced', 'slow': 'quality'},
    'intel_igpu': {'very_fast': 'fastest', 'fast': 'faster', 'medium': 'balanced', 'slow': 'slow'},
    'amd_igpu': {'very_fast': 'speed', 'fast': 'speed', 'medium': 'balanced', 'slow': 'quality'},
    'cpu': {'very_fast': 'veryfast', 'fast': 'fast', 'medium': 'medium', 'slow': 'slow'}
}

# Obter preset baseado na velocidade
preset = profile_mgr.get_preset_from_speed(codec, conversion_speed, hardware_category, current_preset)

# Listar velocidades disponíveis
speeds = profile_mgr.get_conversion_speeds()  # ['very_fast', 'fast', 'medium', 'slow']

# Atualizar velocidade de um perfil
profile_mgr.update_profile_conversion_speed(profile_id, 'fast')
```

### 2. `src/core/ffmpeg_wrapper.py`
**Mudanças:**
- Adicionado parâmetro `conversion_speed` no método `build_encoding_command()`
- Adicionado parâmetro `hardware_category` no método `build_encoding_command()`
- Adicionado método `get_preset_from_speed()` para traduzir velocidade para preset

**Nova Assinatura:**
```python
def build_encoding_command(
    self,
    input_path: str,
    output_path: str,
    codec: str = 'hevc_nvenc',
    cq: Optional[str] = None,
    bitrate: Optional[str] = None,
    resolution: Optional[str] = None,
    preset: str = 'p5',
    two_pass: bool = False,
    hdr_to_sdr: bool = False,
    deinterlace: bool = False,
    audio_tracks: Optional[List[int]] = None,
    subtitle_burn: bool = False,
    plex_compatible: bool = True,
    conversion_speed: Optional[str] = None,  # NOVO
    hardware_category: Optional[str] = None  # NOVO
) -> List[str]
```

### 3. `src/ui/menu.py`
**Mudanças:**
- Adicionada opção "Velocidade" no menu de edição de perfis (opção 9)
- Adicionada interface para seleção de velocidade (very_fast, fast, medium, slow)
- Atualização automática do preset quando velocidade é alterada

**Nova Opção no Menu:**
```
9. Velocidade: [green]medium[/green]
```

### 4. `profiles/profiles.json`
**Mudanças:**
- Adicionado campo `conversion_speed` em 44 perfis existentes
- Distribuição de velocidades:
  - `medium`: 24 perfis (padrão para maioria dos perfis)
  - `fast`: 10 perfis (perfis 720p e alguns otimizados)
  - `slow`: 6 perfis (perfis de qualidade máxima)
  - `very_fast`: 4 perfis (perfis "CPU Rápido")

## Mapeamento de Velocidades

| Velocidade | NVIDIA NVENC | AMD AMF | Intel QSV | CPU (libx26x) |
|------------|--------------|---------|-----------|---------------|
| very_fast | p2 | speed | fastest | veryfast |
| fast | p3 | speed | faster | fast |
| medium | p5 | balanced | balanced | medium |
| slow | p6 | quality | slow | slow |

## Backward Compatibility
- Perfis sem o campo `conversion_speed` continuam funcionando usando o campo `preset` diretamente
- O campo `conversion_speed` é opcional em `create_profile()`
- Método `build_encoding_command()` usa `conversion_speed` apenas quando fornecido

## Testes Realizados
Script de teste `test_conversion_speed.py` criado e executado com sucesso:
- [PASS] ProfileManager - SPEED_TO_PRESET e get_preset_from_speed()
- [PASS] FFmpegWrapper - get_preset_from_speed()
- [PASS] profiles.json - 44 perfis com conversion_speed

## Como Usar

### Via Menu UI
1. Selecione um perfil para editar
2. Escolha a opção "9. Velocidade"
3. Selecione a velocidade desejada
4. O preset será atualizado automaticamente

### Via Código
```python
from src.managers.profile_manager import ProfileManager

pm = ProfileManager()

# Obter velocidades disponíveis
speeds = pm.get_conversion_speeds()  # ['very_fast', 'fast', 'medium', 'slow']

# Atualizar velocidade de um perfil
pm.update_profile_conversion_speed('nvidia_filmes_4k_hevc', 'fast')

# Criar perfil com velocidade específica
pm.create_profile(
    name='Meu Perfil',
    codec='hevc_nvenc',
    cq='20',
    conversion_speed='fast',
    hardware_category='nvidia_gpu'
)
```

## Próximos Passos (Opcional)
- Adicionar filtro de perfis por velocidade na UI
- Adicionar atalhos de teclado para seleção rápida de velocidade
- Criar presets personalizados para velocidades específicas

## Notas
- Perfis temporários/edições (9 perfis) não foram atualizados com `conversion_speed`
- A feature é totalmente backward compatible
- Não há impacto de performance na conversão
