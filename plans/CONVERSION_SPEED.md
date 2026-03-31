# Conversion Speed Feature Specification

## Overview
Adicionar campo `conversion_speed` aos perfis existentes para permitir que usuários selecionem a velocidade de conversão desejada (very_fast, fast, medium, slow) mantendo os perfis padrão.

## Mapeamento de Velocidades por Hardware

O campo `conversion_speed` será traduzido para o preset específico de cada hardware no momento do encoding.

| conversion_speed | NVIDIA NVENC | AMD AMF | Intel QSV | CPU (libx265/libx264) |
|------------------|--------------|---------|-----------|----------------------|
| `very_fast` | p2 | speed | fastest | veryfast |
| `fast` | p3 | speed | faster | fast |
| `medium` | p5 | balanced | balanced | medium |
| `slow` | p6 | quality | slow | slow |

## Estrutura do Perfil

### Antes
```json
{
  "nvidia_filmes_4k_hevc": {
    "name": "NVIDIA Filmes 4K HEVC",
    "codec": "hevc_nvenc",
    "cq": "18",
    "preset": "p5",
    "resolution": null,
    "hdr_to_sdr": false,
    "deinterlace": false,
    "plex_compatible": true,
    "two_pass": false,
    "hardware_category": "nvidia_gpu"
  }
}
```

### Depois
```json
{
  "nvidia_filmes_4k_hevc": {
    "name": "NVIDIA Filmes 4K HEVC",
    "codec": "hevc_nvenc",
    "cq": "18",
    "preset": "p5",
    "conversion_speed": "medium",
    "resolution": null,
    "hdr_to_sdr": false,
    "deinterlace": false,
    "plex_compatible": true,
    "two_pass": false,
    "hardware_category": "nvidia_gpu"
  }
}
```

## Implementação

### 1. profiles.json
- Adicionar campo `conversion_speed` em todos os perfis existentes
- Valores válidos: `very_fast`, `fast`, `medium`, `slow`
- Perfis padrão manterão `medium` como valor padrão

### 2. profile_manager.py
Adicionar método para obter preset baseado na velocidade:

```python
SPEED_TO_PRESET = {
    'nvidia_gpu': {
        'very_fast': 'p2',
        'fast': 'p3',
        'medium': 'p5',
        'slow': 'p6'
    },
    'amd_gpu': {
        'very_fast': 'speed',
        'fast': 'speed',
        'medium': 'balanced',
        'slow': 'quality'
    },
    'intel_igpu': {
        'very_fast': 'fastest',
        'fast': 'faster',
        'medium': 'balanced',
        'slow': 'slow'
    },
    'amd_igpu': {
        'very_fast': 'speed',
        'fast': 'speed',
        'medium': 'balanced',
        'slow': 'quality'
    },
    'cpu': {
        'very_fast': 'veryfast',
        'fast': 'fast',
        'medium': 'medium',
        'slow': 'slow'
    }
}
```

### 3. ffmpeg_wrapper.py
Adicionar método para traduzir `conversion_speed` para preset:

```python
def get_preset_from_speed(self, codec: str, conversion_speed: str, hardware_category: str) -> str:
    """Traduz conversion_speed para preset específico do codec."""
    # Se conversion_speed não estiver definido, usa o preset diretamente
    if not conversion_speed:
        return preset
    
    # Mapeia hardware_category para chave do SPEED_TO_PRESET
    # Retorna preset baseado no mapeamento
```

### 4. menu.py
Adicionar opção no menu de edição de perfis:
- Opção para selecionar velocidade de conversão
- Mostrar velocidade atual do perfil
- Permitir alteração entre very_fast, fast, medium, slow

## Perfis Existentes

Todos os 44+ perfis existentes serão mantidos. O campo `conversion_speed` será adicionado com valor `medium` como padrão para a maioria dos perfis, exceto aqueles que já são otimizados para velocidade.

### Exceções (perfis que já são "fast")
- `cpu_rapido_*` → `conversion_speed: "very_fast"`

## Backward Compatibility
- Perfis sem o campo `conversion_speed` usarão o campo `preset` diretamente
- Novos perfis criados pelo usuário terão `conversion_speed` como campo opcional

## UI Changes
No menu de edição de perfil, adicionar:
```
5. Velocidade: medium (very_fast, fast, medium, slow)
```

## Testing
1. Verificar que perfis existentes funcionam sem alterações
2. Testar novo campo conversion_speed com cada tipo de hardware
3. Validar que preset correto é aplicado no comando FFmpeg
