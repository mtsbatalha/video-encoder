# Exemplo de Comando NVENC para Conversão H.264 com Aceleração CUDA

## Comando Básico FFmpeg com NVIDIA NVENC (CUDA Hardware Acceleration)

Para converter um arquivo de vídeo para H.264 usando uma GPU NVIDIA com aceleração hardware completa:

```bash
ffmpeg -y -hwaccel cuda -hwaccel_output_format cuda -i "C:\Videos\entrada.mkv" \
  -c:v h264_nvenc \
  -preset p5 \
  -cq 21 \
  -pix_fmt yuv420p \
  -profile:v high \
  -map 0:a? -c:a aac -b:a 192k \
  -map 0:s? -c:s copy \
  -movflags +faststart \
  "C:\Videos\saida_h264.mp4"
```

## Parâmetros de Hardware Acceleration

| Parâmetro | Descrição |
|-----------|-----------|
| `-hwaccel cuda` | Usa CUDA para aceleração de decoding do vídeo de entrada |
| `-hwaccel_output_format cuda` | Mantém o vídeo decodificado na memória da GPU (evita cópia CPU↔GPU) |

## Parâmetros Completos Explicados

| Parâmetro | Descrição |
|-----------|-----------|
| `-y` | Sobrescrever arquivo de saída sem perguntar |
| `-stats` | Mostrar estatísticas de progresso durante encoding |
| `-hwaccel cuda` | Aceleração hardware CUDA para decoding |
| `-hwaccel_output_format cuda` | Manter dados na GPU após decoding |
| `-i` | Arquivo de entrada |
| `-c:v h264_nvenc` | Codec de vídeo NVENC H.264 |
| `-preset p5` | Preset de qualidade (p1-p7, onde p7 é mais lento e melhor qualidade) |
| `-cq 21` | Qualidade Constante (1-51, menor = melhor qualidade) |
| `-pix_fmt yuv420p` | Formato de pixel para máxima compatibilidade |
| `-profile:v high` | Perfil High do H.264 |
| `-map 0:a?` | Mapear todas as faixas de áudio (se existirem) |
| `-c:a aac -b:a 192k` | Codec de áudio AAC com bitrate 192kbps |
| `-map 0:s? -c:s copy` | Copiar legendas sem re-encoding |
| `-movflags +faststart` | Otimizar para streaming web |

## Exemplos por Caso de Uso

### 1. Filme 1080p (Alta Qualidade)
```bash
ffmpeg -y -hwaccel cuda -hwaccel_output_format cuda -stats -i "filme_1080p.mkv" \
  -c:v h264_nvenc \
  -preset p5 \
  -cq 20 \
  -pix_fmt yuv420p \
  -profile:v high \
  -map 0:a? -c:a aac -b:a 192k \
  -map 0:s? -c:s copy \
  -movflags +faststart \
  "filme_1080p_h264.mp4"
```

### 2. Filme 4K com Conversão HDR para SDR
```bash
ffmpeg -y -hwaccel cuda -hwaccel_output_format cuda -stats -i "filme_4k_hdr.mkv" \
  -vf "zscale=t=linear:npl=100,format=gbrpf32le,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p" \
  -c:v h264_nvenc \
  -preset p5 \
  -cq 20 \
  -pix_fmt yuv420p \
  -profile:v high \
  -map 0:a? -c:a aac -b:a 192k \
  -map 0:s? -c:s copy \
  -movflags +faststart \
  "filme_4k_sdr_h264.mp4"
```

### 3. Série 720p (Arquivo Menor)
```bash
ffmpeg -y -hwaccel cuda -hwaccel_output_format cuda -stats -i "serie_720p.mkv" \
  -vf "scale=-2:720" \
  -c:v h264_nvenc \
  -preset p4 \
  -cq 23 \
  -pix_fmt yuv420p \
  -profile:v high \
  -map 0:a? -c:a aac -b:a 192k \
  -map 0:s? -c:s copy \
  -movflags +faststart \
  "serie_720p_h264.mp4"
```

### 4. Vídeo Entrelaçado (TV Antiga)
```bash
ffmpeg -y -hwaccel cuda -hwaccel_output_format cuda -stats -i "video_entrelacado.ts" \
  -vf "bwdif=mode=send:par=1" \
  -c:v h264_nvenc \
  -preset p5 \
  -cq 21 \
  -pix_fmt yuv420p \
  -profile:v high \
  -map 0:a? -c:a aac -b:a 192k \
  -map 0:s? -c:s copy \
  -movflags +faststart \
  "video_desentrelacado.mp4"
```

### 5. HEVC (H.265) com Melhor Eficiência
```bash
ffmpeg -y -hwaccel cuda -hwaccel_output_format cuda -stats -i "entrada.mkv" \
  -c:v hevc_nvenc \
  -preset p5 \
  -cq 18 \
  -pix_fmt yuv420p10le \
  -profile:v main10 \
  -map 0:a? -c:a aac -b:a 192k \
  -map 0:s? -c:s copy \
  -movflags +faststart \
  "saida_hevc.mp4"
```

### 6. Two-Pass Encoding (Qualidade Máxima)
```bash
# Primeira passada
ffmpeg -y -hwaccel cuda -hwaccel_output_format cuda -i "entrada.mkv" \
  -c:v h264_nvenc \
  -preset p5 \
  -b:v 5000k \
  -rc twopass \
  -pass 1 \
  -an -f null NUL

# Segunda passada
ffmpeg -y -hwaccel cuda -hwaccel_output_format cuda -i "entrada.mkv" \
  -c:v h264_nvenc \
  -preset p5 \
  -b:v 5000k \
  -rc twopass \
  -pass 2 \
  -map 0:a? -c:a aac -b:a 192k \
  -map 0:s? -c:s copy \
  -movflags +faststart \
  "saida.mp4"
```

## Usando o Video Encoder (Python)

### Via CLI:
```bash
python vigia_nvenc.py --profile nvidia_filmes_1080p_h264 --input "C:\Videos\entrada.mkv" --output "C:\Videos\saida.mp4"
```

### Via Python:
```python
from src.core.ffmpeg_wrapper import FFmpegWrapper

ffmpeg = FFmpegWrapper()

# O comando é construído automaticamente baseado no profile
command = ffmpeg.build_encoding_command(
    input_path="C:\\Videos\\entrada.mkv",
    output_path="C:\\Videos\\saida.mp4",
    codec='h264_nvenc',
    cq='21',
    preset='p5',
    resolution=None,
    two_pass=False,
    hdr_to_sdr=True,  # Converter HDR para SDR
    deinterlace=False,
    plex_compatible=True
)

# Nota: O wrapper atual não inclui -hwaccel cuda automaticamente
# Para adicionar aceleração CUDA, modifique o comando manualmente:
command = [ffmpeg.ffmpeg, '-y', '-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda'] + command[1:]

# Executar encoding
success, error = ffmpeg.run_encoding(command)
```

## Valores de CQ Recomendados

| Resolução | H.264 CQ | HEVC CQ |
|-----------|----------|---------|
| 4K        | 20-22    | 18-20   |
| 1080p     | 20-21    | 18-20   |
| 720p      | 22-23    | 20-22   |
| 480p      | 23-24    | 21-23   |

## Presets NVENC

| Preset | Velocidade | Qualidade | Uso Recomendado |
|--------|------------|-----------|-----------------|
| p1     | Mais rápido | Mais baixa | Testes rápidos |
| p4     | Rápido     | Boa       | Conversão em lote |
| p5     | Balanceado | Melhor    | Uso geral (recomendado) |
| p7     | Mais lento | Máxima    | Arquivo final de qualidade |

## Verificar GPUs NVIDIA Disponíveis

```bash
# Usando nvidia-smi
nvidia-smi

# Usando FFmpeg para listar codecs NVENC
ffmpeg -encoders | findstr nvenc

# Verificar suporte a CUDA no FFmpeg
ffmpeg -hwaccels
```

## Benefícios do `-hwaccel cuda -hwaccel_output_format cuda`

1. **Decoding acelerado**: O vídeo de entrada é decodificado pela GPU em vez da CPU
2. **Menos cópias de memória**: Os frames decodificados permanecem na VRAM da GPU
3. **Encoding mais rápido**: O NVENC acessa diretamente os frames na GPU
4. **CPU livre**: A CPU fica disponível para outras tarefas

## Fluxo com vs. sem CUDA Acceleration

### Sem aceleração CUDA:
```
Entrada → CPU (decode) → RAM → GPU (encode) → Saída
         ↑_______________↓
         Cópia CPU→GPU necessária
```

### Com aceleração CUDA:
```
Entrada → GPU (decode via CUDA) → VRAM → GPU (encode NVENC) → Saída
                              ↑______Sem cópia necessária______↓
```

## Perfis Disponíveis no Video Encoder

Os seguintes perfis NVIDIA estão disponíveis em [`profiles/profiles.json`](../profiles/profiles.json):

- `nvidia_filmes_4k_hevc` - HEVC 4K, CQ 18, HDR preservado
- `nvidia_filmes_4k_h264` - H.264 4K, CQ 20, HDR→SDR
- `nvidia_filmes_1080p_hevc` - HEVC 1080p, CQ 20, HDR preservado
- `nvidia_filmes_1080p_h264` - H.264 1080p, CQ 21, HDR→SDR
- `nvidia_filmes_720p_hevc` - HEVC 720p, CQ 22, HDR→SDR
- `nvidia_filmes_720p_h264` - H.264 720p, CQ 23, HDR→SDR
- `nvidia_series_1080p_hevc` - HEVC séries 1080p, CQ 22
- `nvidia_series_1080p_h264` - H.264 séries 1080p, CQ 23
