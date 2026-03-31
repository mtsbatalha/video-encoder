# Melhorias no Monitor de Encoding em Tempo Real

## Visão Geral

O monitor de encoding em tempo real foi aprimorado para exibir informações detalhadas sobre o processo de transcodificação de forma visualmente intuitiva, mostrando lado a lado as informações de entrada e saída.

## Novas Funcionalidades

### 1. Painel de Informações de Stream (Side-by-Side)

O monitor agora exibe uma tabela comparativa mostrando:

| Stream | Entrada | → | Saída | Status |
|--------|---------|---|-------|--------|
| 📁 Arquivo | Tamanho, duração, bitrate | → | Codec, qualidade | |
| 🎬 Vídeo | Codec, resolução, HDR | → | Codec de saída | ⚡ TRANSCODE |
| 🔊 Áudio | Codecs, idiomas | → | Codec de saída | 📋 COPY |
| 📝 Legendas | Streams, idiomas | → | Status | 📋 COPY |

### 2. Ícones de Status de Transcodificação

- **⚡ (Amarelo)**: TRANSCODE - O stream está sendo transcodificado (codec de saída diferente)
- **📋 (Verde)**: COPY - O stream está sendo copiado sem modificação
- **🔥 (Vermelho)**: BURN-IN - Legendas estão sendo queimadas no vídeo

### 3. Informações Detalhadas de Entrada

- **Tamanho do arquivo**: Em MB
- **Duração**: Formato HH:MM:SS
- **Bitrate**: Em Kbps
- **Codec de vídeo**: Nome do codec original
- **Resolução**: Largura x Altura
- **HDR**: Indicador visual se o conteúdo é HDR
- **Áudio**: Lista de codecs e idiomas
- **Legendas**: Número de streams e codecs

### 4. Informações de Saída

- **Codec de vídeo**: Codec de destino (ex: HEVC (NVENC))
- **Qualidade**: Parâmetro CQ ou bitrate
- **Codec de áudio**: AAC ou Copy
- **Legendas**: Copy ou Burned

### 5. Legenda Explicativa

O monitor inclui uma legenda no rodapé explicando os ícones:
```
Legenda: ⚡ Transcode  📋 Copy  🔥 Burn-in
```

## Arquivos Modificados

### `src/ui/realtime_monitor.py`

#### Novos Métodos Adicionados

1. **`_process_input_media_info(media_info)`**: Processa informações de mídia de entrada
2. **`_generate_output_media_info(profile)`**: Gera informações de saída baseadas no profile
3. **`_determine_transcode_status(profile)`**: Determina status de transcodificação para cada stream
4. **`_get_status_icon(status)`**: Retorna ícone para status
5. **`_get_status_color(status)`**: Retorna cor para status
6. **`_generate_media_info_panel()`**: Gera tabela side-by-side de informações
7. **`_generate_status_legend()`**: Gera legenda explicativa dos ícones

#### Método `start()` Modificado

O método `start()` agora aceita parâmetros adicionais:
- `input_media_info`: Dicionário com informações de mídia de entrada
- `profile`: Dicionário com perfil de encoding

### `src/core/encoder_engine.py`

#### Modificação no Método `_execute_job()`

Agora passa `input_media_info` e `profile` para o monitor:

```python
self.realtime_monitor.start(
    description=f"Encoding: {job.input_path}",
    total_duration=duration,
    input_file=job.input_path,
    output_file=job.output_path,
    input_media_info=media_info,
    profile=profile
)
```

## Exemplo de Uso

Ao iniciar um encoding, o monitor exibirá:

```
╭──────────────────────────────────────────────────────────── 🎬 NVENC Encoder - Tempo Real ─────────────────────────────────────────────────────────────╮
│ Encoding: /mnt/data/Filme.mkv                                                                                                                           │
│ Aguardando...                                                                                                                                              │
│                                                                                                                                                        │
│ [████████████████████░░░░░░░░░░░░░░░░░░░░░░░░] 45.5%                                                                                              │
│                                                                                                                                                        │
│ 📊 Stream Information:                                                                                                                                 │
│ ┌──────────┬─────────────────────────────┬───┬─────────────────────────────┬──────────┐                                                                │
│ │ Stream   │ Entrada                     │ → │ Saída                       │ Status   │                                                                │
│ ├──────────┼─────────────────────────────┼───┼─────────────────────────────┼──────────┤                                                                │
│ │ 📁 Arq.  │ 45.2 GB                     │ → │ Codec: HEVC (NVENC)         │          │                                                                │
│ │          │ Duração: 02:15:30           │   │ Quality: CQ20               │          │                                                                │
│ │          │ Bitrate: 45000 Kbps         │   │                             │          │                                                                │
│ │ 🎬 Vídeo │ HEVC                        │ → │ HEVC (NVENC)                │ 📋 COPY  │                                                                │
│ │          │ 3840x2160                   │   │                             │          │                                                                │
│ │          │ HDR                         │   │                             │          │                                                                │
│ │ 🔊 Áudio │ AC3 (por)                   │ → │ Copy                        │ 📋 COPY  │                                                                │
│ │          │ AAC (eng)                   │   │                             │          │                                                                │
│ │ 📝 Leg.  │ 2 stream(s): PGS (por)...   │ → │ Copy                        │ 📋 COPY  │                                                                │
│ └──────────┴─────────────────────────────┴───┴─────────────────────────────┴──────────┘                                                                │
│ Legenda: ⚡ Transcode  📋 Copy  🔥 Burn-in                                                                                                              │
│                                                                                                                                                        │
│ ⚡ Encoding Stats:                                                                                                                                     │
│  FPS:             65.3                                                                                                                                │
│  Speed:           2.15x                                                                                                                               │
│  Bitrate:         35000 Kbps                                                                                                                          │
│  Progresso:       45.5%                                                                                                                               │
│  Tempo Restante:  01:25:30                                                                                                                            │
│                                                                                                                                                        │
│ 🖥️  Hardware:                                                                                                                                           │
│  GPU:        ████████░░ 80%  72°C                                                                                                                      │
│  VRAM:       6144MB/8192MB                                                                                                                             │
│  CPU:        ████░░░░░░ 40%                                                                                                                            │
│                                                                                                                                                        │
│ Input: /mnt/data/Filme.mkv                                                                                                                             │
│ Output: /mnt/conversions/Filme_hevc_nvenc_cq20.mkv                                                                                                     │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Detecção Inteligente de Status

O sistema detecta automaticamente se o stream será transcodificado ou copiado:

- **Vídeo**: Compara o codec de entrada com o codec de saída (considera codecs equivalentes como HEVC/hevc_nvenc/libx265)
- **Áudio**: Verifica se `keep_audio` está habilitado no profile
- **Legendas**: Verifica se `subtitle_burn` está habilitado

## Benefícios

1. **Transparência**: Usuário sabe exatamente o que está acontecendo com cada stream
2. **Diagnóstico**: Fácil identificar se um erro é causado por codec incompatível
3. **Performance**: Visualização clara se o encoding está sendo feito via transcode ou copy
4. **Informação**: Todos os dados relevantes em um único lugar
