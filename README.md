# Fabrica de Conversão NVENC Pro v2.0

Codificação de vídeo acelerada por GPU NVIDIA com interface CLI moderna e menu interativo.

## Requisitos

- Python 3.8+
- NVIDIA GPU com suporte NVENC
- FFmpeg com codecs NVENC
- Drivers NVIDIA atualizados

## Instalação

```bash
# Instalar dependências
pip install rich psutil

# Verificar instalação
python vigia_nvenc.py --check
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

### Filmes (Qualidade Priorizada)

| Perfil | Codec | CQ | Resolução | HDR→SDR | Descrição |
|--------|-------|-----|-----------|---------|-----------|
| Filmes 4K HEVC | hevc_nvenc | 18 | Original | Não | Alta qualidade 4K, HDR preservado |
| Filmes 4K H264 | h264_nvenc | 20 | Original | Sim | Compatibilidade máxima, HDR→SDR |
| Filmes 1080p HEVC | hevc_nvenc | 20 | 1080p | Não | Qualidade balanceada, HDR preservado |
| Filmes 1080p H264 | h264_nvenc | 21 | 1080p | Sim | Compatibilidade, HDR→SDR |
| Filmes 720p HEVC | hevc_nvenc | 22 | 720p | Sim | Arquivos menores, HDR→SDR |
| Filmes 720p H264 | h264_nvenc | 23 | 720p | Sim | TVs antigas, HDR→SDR |

### Séries (Compressão Priorizada)

| Perfil | Codec | CQ | Resolução | HDR→SDR | Descrição |
|--------|-------|-----|-----------|---------|-----------|
| Series 4K HEVC | hevc_nvenc | 22 | Original | Não | Qualidade 4K, HDR preservado |
| Series 4K H264 | h264_nvenc | 24 | Original | Sim | Compatibilidade, HDR→SDR |
| Series 1080p HEVC | hevc_nvenc | 24 | 1080p | Não | Balanceado, HDR preservado |
| Series 1080p H264 | h264_nvenc | 25 | 1080p | Sim | Compatibilidade, HDR→SDR |
| Series 720p HEVC | hevc_nvenc | 26 | 720p | Sim | Arquivos leves, HDR→SDR |
| Series 720p H264 | h264_nvenc | 27 | 720p | Sim | Máxima compressão, HDR→SDR |

### Animação

| Perfil | Codec | CQ | Resolução | HDR→SDR | Descrição |
|--------|-------|-----|-----------|---------|-----------|
| Animação 1080p HEVC | hevc_nvenc | 18 | 1080p | Não | Otimizado para desenhos |
| Animação 720p H264 | h264_nvenc | 20 | 720p | Sim | Compatibilidade |

### Documentários

| Perfil | Codec | CQ | Resolução | HDR→SDR | Descrição |
|--------|-------|-----|-----------|---------|-----------|
| Documentário 1080p HEVC | hevc_nvenc | 24 | 1080p | Não | Conteúdo estático |
| Documentário 720p H264 | h264_nvenc | 26 | 720p | Sim | Compatibilidade |

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
