# Fabrica de Conversão Multi-Hardware Pro v2.0

Codificação de vídeo acelerada por GPU (NVIDIA NVENC, AMD AMF, Intel QSV) e CPU com interface CLI moderna e menu interativo.

## Requisitos

- Python 3.8+
- GPU com suporte a aceleração hardware (NVIDIA NVENC, AMD AMF, Intel QSV) ou CPU
- FFmpeg com codecs de hardware (nvenc, amf, qsv)
- Drivers de vídeo atualizados

### Dependências Opcionais (Detecção Automática de Hardware)

```bash
pip install pynvml pywin32
```

## Detecção de Hardware

```bash
# Detectar hardware e perfis recomendados
python vigia_nvenc.py --detect-hardware

# Listar perfis por categoria de hardware
python vigia_nvenc.py --profile-list --hardware nvidia_gpu
python vigia_nvenc.py --profile-list --hardware amd_gpu
python vigia_nvenc.py --profile-list --hardware intel_igpu
python vigia_nvenc.py --profile-list --hardware amd_igpu
python vigia_nvenc.py --profile-list --hardware cpu
```

## Uso Rápido

### CLI Moderna

```bash
# Ajuda
python vigia_nvenc.py --help

# Codificar arquivo único com perfil
python vigia_nvenc.py -f video.mkv -p "Filmes 4K HEVC"

# Codificar pasta inteira
python vigia_nvenc.py -F /input/videos -O /output -p "Series 1080p"

# Modo watch (monitorar pastas configuradas)
python vigia_nvenc.py --watch

# Menu interativo
python vigia_nvenc.py --interactive
```

### Opções de Encoding

```bash
# Codec específico
python vigia_nvenc.py -f video.mkv --codec hevc_nvenc --cq 20

# Com downscale
python vigia_nvenc.py -f video.mkv --resolution 1080 --cq 24

# Two-pass encoding (H264/HEVC)
python vigia_nvenc.py -f video.mkv --two-pass

# HDR para SDR
python vigia_nvenc.py -f video.mkv --hdr-to-sdr

# Deinterlacing
python vigia_nvenc.py -f video.mkv --deinterlace
```

### Gerenciamento de Perfis

```bash
# Listar perfis
python vigia_nvenc.py --profile-list

# Criar perfil
python vigia_nvenc.py --profile-create "Meu Perfil"

# Exportar perfil
python vigia_nvenc.py --profile-export "Filmes 4K" -o backup.json

# Importar perfil
python vigia_nvenc.py --profile-import perfil.json
```

### Estatísticas

```bash
# Ver estatísticas
python vigia_nvenc.py --stats

# Exportar relatório
python vigia_nvenc.py --stats-export -o relatorio.json

# Resetar estatísticas
python vigia_nvenc.py --stats-reset
```

### Gerenciamento de Fila

```bash
# Ver fila
python vigia_nvenc.py --queue

# Pausar fila
python vigia_nvenc.py --queue-pause

# Retomar fila
python vigia_nvenc.py --queue-resume

# Limpar fila
python vigia_nvenc.py --queue-clear
```

## Perfis Incluídos

### Matriz de Codecs por Hardware

| Hardware | Codec HEVC | Codec H264 | Presets |
|----------|------------|------------|---------|
| NVIDIA GPU | hevc_nvenc | h264_nvenc | p1-p7 |
| AMD GPU | hevc_amf | h264_amf | quality/balanced/speed |
| Intel iGPU | hevc_qsv | h264_qsv | fast/balanced/slow |
| CPU | libx265 | libx264 | ultrafast-veryslow |

### NVIDIA GPU (12 Perfis)

| Perfil | Codec | CQ | Preset | Resolução | HDR→SDR | Descrição |
|--------|-------|-----|--------|-----------|---------|-----------|
| NVIDIA Filmes 4K HEVC | hevc_nvenc | 18 | p5 | Original | Não | Alta qualidade 4K |
| NVIDIA Filmes 4K H264 | h264_nvenc | 20 | p5 | Original | Sim | Compatibilidade máxima |
| NVIDIA Filmes 1080p HEVC | hevc_nvenc | 20 | p4 | 1080p | Não | Qualidade balanceada |
| NVIDIA Filmes 1080p H264 | h264_nvenc | 21 | p4 | 1080p | Sim | Compatibilidade |
| NVIDIA Filmes 720p HEVC | hevc_nvenc | 22 | p3 | 720p | Sim | Arquivos menores |
| NVIDIA Filmes 720p H264 | h264_nvenc | 23 | p3 | 720p | Sim | TVs antigas |
| NVIDIA Series 4K HEVC | hevc_nvenc | 22 | p4 | Original | Não | Qualidade 4K |
| NVIDIA Series 4K H264 | h264_nvenc | 24 | p4 | Original | Sim | Compatibilidade |
| NVIDIA Series 1080p HEVC | hevc_nvenc | 24 | p3 | 1080p | Não | Balanceado |
| NVIDIA Series 1080p H264 | h264_nvenc | 25 | p3 | 1080p | Sim | Compatibilidade |
| NVIDIA Series 720p HEVC | hevc_nvenc | 26 | p2 | 720p | Sim | Arquivos leves |
| NVIDIA Series 720p H264 | h264_nvenc | 27 | p2 | 720p | Sim | Máxima compressão |

### AMD GPU (8 Perfis)

| Perfil | Codec | CQ | Preset | Resolução | HDR→SDR | Descrição |
|--------|-------|-----|--------|-----------|---------|-----------|
| AMD Filmes 1080p HEVC | hevc_amf | 20 | quality | 1080p | Não | Alta qualidade |
| AMD Filmes 1080p H264 | h264_amf | 21 | quality | 1080p | Sim | Compatibilidade |
| AMD Filmes 720p HEVC | hevc_amf | 22 | balanced | 720p | Sim | Balanceado |
| AMD Filmes 720p H264 | h264_amf | 23 | balanced | 720p | Sim | Compatibilidade |
| AMD Series 1080p HEVC | hevc_amf | 24 | balanced | 1080p | Não | Balanceado |
| AMD Series 1080p H264 | h264_amf | 25 | balanced | 1080p | Sim | Compatibilidade |
| AMD Series 720p HEVC | hevc_amf | 26 | speed | 720p | Sim | Arquivos leves |
| AMD Series 720p H264 | h264_amf | 27 | speed | 720p | Sim | Máxima compressão |

### Intel iGPU (8 Perfis)

| Perfil | Codec | CQ | Preset | Resolução | HDR→SDR | Descrição |
|--------|-------|-----|--------|-----------|---------|-----------|
| Intel Filmes 1080p HEVC | hevc_qsv | 20 | slow | 1080p | Não | Alta qualidade |
| Intel Filmes 1080p H264 | h264_qsv | 21 | slow | 1080p | Sim | Compatibilidade |
| Intel Filmes 720p HEVC | hevc_qsv | 22 | balanced | 720p | Sim | Balanceado |
| Intel Filmes 720p H264 | h264_qsv | 23 | balanced | 720p | Sim | Compatibilidade |
| Intel Series 1080p HEVC | hevc_qsv | 24 | balanced | 1080p | Não | Balanceado |
| Intel Series 1080p H264 | h264_qsv | 25 | balanced | 1080p | Sim | Compatibilidade |
| Intel Series 720p HEVC | hevc_qsv | 26 | fast | 720p | Sim | Arquivos leves |
| Intel Series 720p H264 | h264_qsv | 27 | fast | 720p | Sim | Máxima compressão |

### AMD iGPU (8 Perfis)

| Perfil | Codec | CQ | Preset | Resolução | HDR→SDR | Descrição |
|--------|-------|-----|--------|-----------|---------|-----------|
| AMD iGPU Filmes 1080p HEVC | hevc_amf | 20 | quality | 1080p | Não | Alta qualidade |
| AMD iGPU Filmes 1080p H264 | h264_amf | 21 | quality | 1080p | Sim | Compatibilidade |
| AMD iGPU Filmes 720p HEVC | hevc_amf | 22 | balanced | 720p | Sim | Balanceado |
| AMD iGPU Filmes 720p H264 | h264_amf | 23 | balanced | 720p | Sim | Compatibilidade |
| AMD iGPU Series 1080p HEVC | hevc_amf | 24 | balanced | 1080p | Não | Balanceado |
| AMD iGPU Series 1080p H264 | h264_amf | 25 | balanced | 1080p | Sim | Compatibilidade |
| AMD iGPU Series 720p HEVC | hevc_amf | 26 | speed | 720p | Sim | Arquivos leves |
| AMD iGPU Series 720p H264 | h264_amf | 27 | speed | 720p | Sim | Máxima compressão |

### CPU Qualidade (4 Perfis)

| Perfil | Codec | CQ | Preset | Resolução | HDR→SDR | Descrição |
|--------|-------|-----|--------|-----------|---------|-----------|
| CPU Filmes 1080p HEVC | libx265 | 20 | slow | 1080p | Não | Máxima qualidade CPU |
| CPU Filmes 1080p H264 | libx264 | 21 | slow | 1080p | Sim | Compatibilidade |
| CPU Series 1080p HEVC | libx265 | 24 | medium | 1080p | Não | Balanceado |
| CPU Series 1080p H264 | libx264 | 25 | medium | 1080p | Sim | Compatibilidade |

### CPU Rápido (4 Perfis)

| Perfil | Codec | CQ | Preset | Resolução | HDR→SDR | Descrição |
|--------|-------|-----|--------|-----------|---------|-----------|
| CPU Rápido 1080p HEVC | libx265 | 26 | fast | 1080p | Não | Encoding rápido |
| CPU Rápido 1080p H264 | libx264 | 27 | fast | 1080p | Sim | Compatibilidade |
| CPU Rápido 720p HEVC | libx265 | 28 | faster | 720p | Sim | Máxima velocidade |
| CPU Rápido 720p H264 | libx264 | 29 | faster | 720p | Sim | Compatibilidade |

**Total: 44 Perfis**

## Configuração

Edite `config.json` para personalizar:

- Pastas watch
- Limites de encoding simultâneo
- Notificações (email/webhook)
- Monitoramento de hardware
- Logs

## Estrutura do Projeto

```
video-encoder/
├── vigia_nvenc.py       # Main app
├── config.json          # Configuração centralizada
├── src/
│   ├── core/            # FFmpeg wrapper, HW monitor, encoder
│   ├── managers/        # Profiles, Jobs, Queue, Stats
│   ├── ui/              # Menu, progress, validators
│   ├── utils/           # Path, file, notification utils
│   └── cli.py           # Interface CLI
├── profiles/            # Perfis de encoding (JSON)
├── jobs/                # Fila de jobs (JSON)
├── logs/                # Logs de execução
└── stats/               # Estatísticas
```

## API Python

```python
from src.managers.profile_manager import ProfileManager
from src.managers.job_manager import JobManager
from src.core.ffmpeg_wrapper import FFmpegWrapper

# Usar perfil
profile_mgr = ProfileManager()
profile = profile_mgr.get_profile_by_name("Filmes 4K HEVC")

# Codificar
ffmpeg = FFmpegWrapper()
command = ffmpeg.build_encoding_command(
    input_path="video.mkv",
    output_path="video_encoded.mkv",
    **profile
)
success, error = ffmpeg.run_encoding(command)
```

## Troubleshooting

### "FFmpeg não encontrado"
Instale FFmpeg com suporte NVENC: https://www.gyan.dev/ffmpeg/builds/

### "Nenhum codec NVENC encontrado"
- Atualize drivers NVIDIA
- Verifique se GPU é compatível com NVENC

### "psutil não disponível"
```bash
pip install psutil
```

## Licença

MIT
