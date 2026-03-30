# 🎬 Monitoramento em Tempo Real - NVENC Encoder

## Visão Geral

O sistema agora possui uma interface de monitoramento em tempo real que mostra durante o processamento dos jobs:

- **Barra de progresso** visual
- **FPS** de encoding (frames por segundo)
- **Speed** (velocidade em relação ao tempo real, ex: 2.5x)
- **Bitrate** atual em Kbps
- **Tempo restante** estimado
- **Uso da GPU** (utilização, temperatura, memória VRAM)
- **Uso da CPU**

## Como Usar

### Método 1: Menu Interativo (Recomendado)

1. **Inicie o aplicativo:**
   ```bash
   python vigia_nvenc.py
   ```

2. **Adicione jobs à fila:**
   - Opção `1` - Codificar arquivo único
   - Opção `2` - Codificar pasta (adiciona múltiplos vídeos à fila)

3. **Processe a fila com monitor em tempo real:**
   - Opção `4` - Ver fila de jobs
   - Opção `6` - ⚡ Processar fila agora

   Isso iniciará o processamento com o monitor em tempo real visível.

### Método 2: Modo Watch (Processamento Contínuo)

1. **Configure pastas watch** em `config.json`:
   ```json
   {
     "directories": {
       "watch_folders": [
         {
           "nome": "Meus Vídeos",
           "entrada": "C:/Videos/Input",
           "saida": "C:/Videos/Output",
           "profile": "meu_perfil"
         }
       ]
     }
   }
   ```

2. **Inicie o Modo Watch:**
   - No menu principal, opção `3` - Modo Watch (monitorar pastas)

   O sistema monitorará as pastas configuradas e processará automaticamente qualquer vídeo novo adicionado.

### Método 3: CLI (Linha de Comando)

```bash
# Processar arquivo único
python vigia_nvenc.py -f "C:/Videos/meu_video.mkv" -p "Filmes 4K"

# Processar pasta inteira
python vigia_nvenc.py -F "C:/Videos/Pasta" -p "Series 1080p"

# Iniciar modo watch
python vigia_nvenc.py --watch
```

## Interface do Monitor

```
╭──────────────────────────────────────────────────────────────╮
│           🎬 NVENC Encoder - Tempo Real                      │
├──────────────────────────────────────────────────────────────┤
│ Encoding: C:/Videos/meu_video.mkv                            │
│ Processando job...                                           │
│                                                              │
│ [██████████████████████████░░░░░░░░░░] 65.3%                │
│                                                              │
│ ⚡ Encoding Stats:                                           │
│    FPS:        45.2                                          │
│    Speed:      1.85x                                         │
│    Bitrate:    8500 Kbps                                     │
│    Progresso:  65.3%                                         │
│    Tempo Restante: 00:05:32                                  │
│                                                              │
│ 🖥️  Hardware:                                                │
│    GPU: [██████████░░] 85%  72°C                             │
│    VRAM: 6144MB/8192MB                                       │
│    CPU: [██████░░░░] 65%                                     │
│                                                              │
│ Input: C:/Videos/meu_video.mkv                               │
│ Output: C:/Videos/Output/meu_video_encoded.mkv               │
╰──────────────────────────────────────────────────────────────╯
```

## Entendendo as Métricas

### Encoding Stats

| Métrica | Descrição | Valor Típico |
|---------|-----------|--------------|
| **FPS** | Frames por segundo sendo codificados | 30-120+ (depende da GPU) |
| **Speed** | Velocidade relativa (1.0x = tempo real) | 1.5x - 5.0x para NVENC |
| **Bitrate** | Taxa de bits atual do vídeo de saída | Varia conforme conteúdo |
| **Tempo Restante** | Estimativa baseada na velocidade atual | --:--:-- se não calculável |

### Hardware Stats

| Métrica | Descrição | Alerta |
|---------|-----------|--------|
| **GPU Util** | Porcentagem de uso da GPU | >90% = uso intenso |
| **GPU Temp** | Temperatura da GPU | >80°C = amarelo, >85°C = vermelho |
| **VRAM** | Memória de vídeo usada/total | >90% = alerta |
| **CPU Util** | Porcentagem de uso da CPU | Varia conforme codec |

## Solução de Problemas

### "Adicionei um job à fila mas ele não começa"

**Problema:** Os jobs não são processados automaticamente.

**Solução:** Você precisa iniciar o processamento:
1. Vá em **Opção 4** - Ver fila de jobs
2. Selecione **Opção 6** - ⚡ Processar fila agora

OU

Use o **Modo Watch** (Opção 3) que processa jobs automaticamente.

### "O monitor não aparece"

**Possíveis causas:**
1. Terminal não suporta Rich (atualize: `pip install --upgrade rich`)
2. Job muito rápido (termina antes do monitor atualizar)
3. Erro na importação (execute `python -c "from src.ui.realtime_monitor import RealTimeEncodingMonitor"`)

### "FPS muito baixo"

**Causas possíveis:**
1. Vídeo de entrada tem codec muito complexo
2. GPU está thermal throttling (temperatura > 85°C)
3. Muitos jobs concorrentes (reduza `encoding.max_concurrent` no config.json)

### "Speed abaixo de 1.0x"

Significa que o encoding está mais lento que o tempo real. Para melhorar:
1. Use preset mais rápido (p1-p3 em vez de p5-p7)
2. Reduza jobs concorrentes para 1 se a GPU estiver sobrecarregada
3. Verifique temperatura da GPU

## Configuração

Edite `config.json` para ajustar:

```json
{
  "encoding": {
    "max_concurrent": 2,        // Jobs simultâneos
    "retry_attempts": 2         // Tentativas em caso de erro
  },
  "monitoring": {
    "gpu_enabled": true,        // Monitorar GPU
    "cpu_enabled": true,        // Monitorar CPU
    "temperature_warning": 85   // Alerta de temperatura
  }
}
```

## Dicas de Performance

1. **Para encoding mais rápido:**
   - Use preset `p1` ou `p2` (mais rápido, menor compressão)
   - Reduza jobs concorrentes para 1 se a GPU estiver sobrecarregada

2. **Para arquivos menores:**
   - Use preset `p6` ou `p7` (mais lento, melhor compressão)
   - Aumente CQ (ex: 28-32) para arquivos menores

3. **Monitoramento:**
   - Mantenha GPU abaixo de 80°C para evitar throttling
   - Deixe pelo menos 10% de VRAM livre

## Atalhos de Teclado

Durante o processamento:
- **Ctrl+C** - Interrompe processamento atual
- **Ctrl+C duas vezes** - Sai do aplicativo

## Suporte

Para issues ou dúvidas, verifique os logs em:
- `logs/` - Logs detalhados de encoding
- `stats/stats.json` - Estatísticas históricas
