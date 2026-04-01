# Phase 11: CUDA Acceleration Support

## Visão Geral

Esta fase implementa suporte à aceleração hardware CUDA para codecs NVIDIA NVENC no Video Encoder.

## Problema Anterior

O projeto estava usando comandos FFmpeg sem aceleração hardware de decoding:

```bash
# Comando ANTERIOR (sem aceleração CUDA)
ffmpeg -y -stats -i entrada.mkv -c:v h264_nvenc ...
```

**Limitação**: O decoding do vídeo de entrada era feito pela CPU, e os frames eram copiados para a GPU apenas para encoding.

## Solução Implementada

Adicionado suporte às flags `-hwaccel cuda -hwaccel_output_format cuda`:

```bash
# Comando ATUAL (com aceleração CUDA)
ffmpeg -y -stats -hwaccel cuda -hwaccel_output_format cuda -i entrada.mkv -c:v h264_nvenc ...
```

**Benefícios**:
1. **Decoding via GPU**: Vídeo de entrada decodificado pela GPU NVIDIA via CUDA
2. **Zero-copy**: Frames decodificados permanecem na VRAM
3. **CPU liberada**: CPU disponível para outras tarefas
4. **Velocidade**: Até 2-3x mais rápido em alguns cenários

## Mudanças no Código

### Arquivo: `src/core/ffmpeg_wrapper.py`

#### 1. Novo parâmetro `cuda_accel` no método `build_encoding_command()`

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
    conversion_speed: Optional[str] = None,
    hardware_category: Optional[str] = None,
    cuda_accel: bool = True  # NOVO PARÂMETRO
) -> List[str]:
```

#### 2. Construção do comando com flags CUDA

```python
# ✅ FIX: Usa stderr padrão com -stats para output de progresso
# ✅ CUDA ACCEL: Adiciona flags de aceleração hardware para codecs NVIDIA
cmd = [self.ffmpeg, '-y', '-stats']

# Adicionar aceleração CUDA para codecs NVIDIA
if cuda_accel and codec in ['hevc_nvenc', 'h264_nvenc', 'av1_nvenc']:
    cmd.extend(['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda'])

cmd.extend(['-i', input_path])
```

### Comportamento

| Codec | cuda_accel=True (default) | cuda_accel=False |
|-------|---------------------------|------------------|
| `hevc_nvenc` | `-hwaccel cuda -hwaccel_output_format cuda` | Sem flags CUDA |
| `h264_nvenc` | `-hwaccel cuda -hwaccel_output_format cuda` | Sem flags CUDA |
| `av1_nvenc` | `-hwaccel cuda -hwaccel_output_format cuda` | Sem flags CUDA |
| `hevc_amf` | Sem flags CUDA | Sem flags CUDA |
| `hevc_qsv` | Sem flags CUDA | Sem flags CUDA |
| `libx265` | Sem flags CUDA | Sem flags CUDA |
| `libx264` | Sem flags CUDA | Sem flags CUDA |

## Compatibilidade

### Chamadas Existentes

Todas as chamadas existentes para `build_encoding_command()` continuam funcionando sem modificações, usando o valor default `cuda_accel=True`.

**Locais verificados**:
- [`src/core/encoder_engine.py:300`](src/core/encoder_engine.py:300)
- [`src/cli.py:547`](src/cli.py:547)

### Exemplo de Uso

```python
from src.core.ffmpeg_wrapper import FFmpegWrapper

ffmpeg = FFmpegWrapper()

# Uso padrão (CUDA habilitado automaticamente para NVENC)
command = ffmpeg.build_encoding_command(
    input_path="video.mkv",
    output_path="video.mp4",
    codec='hevc_nvenc',
    cq='18'
)
# Resultado: ffmpeg -y -stats -hwaccel cuda -hwaccel_output_format cuda -i video.mkv ...

# CUDA desabilitado manualmente
command = ffmpeg.build_encoding_command(
    input_path="video.mkv",
    output_path="video.mp4",
    codec='hevc_nvenc',
    cq='18',
    cuda_accel=False
)
# Resultado: ffmpeg -y -stats -i video.mkv ...
```

## Testes

### Arquivo: `tests/test_cuda_accel.py`

Testes implementados:
1. ✅ `hevc_nvenc` com CUDA habilitado
2. ✅ `h264_nvenc` com CUDA habilitado
3. ✅ `av1_nvenc` com CUDA habilitado
4. ✅ `hevc_nvenc` com CUDA desabilitado
5. ✅ `hevc_amf` (AMD) - CUDA não adicionado
6. ✅ `libx265` (CPU) - CUDA não adicionado
7. ✅ Estrutura do comando validada

**Executar testes**:
```bash
python tests/test_cuda_accel.py
```

## Exemplo de Comando Gerado

### H.264 com NVENC (GPU NVIDIA)

```bash
ffmpeg -y -stats -hwaccel cuda -hwaccel_output_format cuda \
  -i "entrada.mkv" \
  -c:v h264_nvenc \
  -preset p5 \
  -cq 21 \
  -pix_fmt yuv420p \
  -profile:v high \
  -map 0:a? -c:a aac -b:a 192k \
  -map 0:s? -c:s copy \
  -movflags +faststart \
  "saida.mp4"
```

### HEVC com NVENC (GPU NVIDIA)

```bash
ffmpeg -y -stats -hwaccel cuda -hwaccel_output_format cuda \
  -i "entrada.mkv" \
  -c:v hevc_nvenc \
  -preset p5 \
  -cq 18 \
  -pix_fmt yuv420p10le \
  -profile:v main10 \
  -map 0:a? -c:a aac -b:a 192k \
  -map 0:s? -c:s copy \
  -movflags +faststart \
  "saida.mp4"
```

## Fluxo de Dados

### Sem Aceleração CUDA (Anterior)
```
Arquivo → CPU (Decode) → RAM → [Cópia CPU→GPU] → GPU (Encode NVENC) → Saída
```

### Com Aceleração CUDA (Atual)
```
Arquivo → GPU (Decode CUDA) → VRAM → GPU (Encode NVENC) → Saída
                    ↑________Sem cópia________↓
```

## Requisitos

- **GPU NVIDIA**: Requer GPU NVIDIA com suporte NVENC
- **Drivers NVIDIA**: Drivers atualizados com suporte CUDA
- **FFmpeg**: Compilado com suporte `--enable-cuda --enable-cuvid --enable-nvenc`

## Verificação de Suporte

```bash
# Verificar GPUs NVIDIA
nvidia-smi

# Verificar codecs NVENC no FFmpeg
ffmpeg -encoders | findstr nvenc

# Verificar aceleração CUDA no FFmpeg
ffmpeg -hwaccels
```

## Arquivos Modificados

| Arquivo | Mudança |
|---------|---------|
| `src/core/ffmpeg_wrapper.py` | Adicionado parâmetro `cuda_accel` e lógica de flags CUDA |
| `tests/test_cuda_accel.py` | Criado arquivo de testes para validação |
| `docs/EXEMPLO_COMANDO_NVENC.md` | Atualizado com exemplos CUDA |
| `docs/PHASE_11_CUDA_ACCELERATION.md` | Criado (este arquivo) |

## Próximos Passos (Opcional)

1. Adicionar campo `cuda_accel` nos perfis do `profiles/profiles.json`
2. Implementar detecção automática de GPUs NVIDIA via `hw_detector.py`
3. Adicionar opção de linha de comando `--no-cuda-accel` para desabilitar manualmente

## Referências

- [FFmpeg CUDA Documentation](https://trac.ffmpeg.org/wiki/HWAccelIntro#CUDA)
- [NVIDIA NVENC Documentation](https://developer.nvidia.com/video-codec-sdk)
- [Documentação de Exemplos NVENC](docs/EXEMPLO_COMANDO_NVENC.md)
