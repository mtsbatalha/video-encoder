# Phase 12: Debug Toggle com Tecla de Atalho

## Visão Geral

Esta funcionalidade permite ativar ou desativar logs de debug durante a conversão de vídeos pressionando a tecla **'D'**. Os logs são exibidos abaixo da tela de monitoramento em tempo real, mantendo a interface limpa quando o debug está desativado.

## Implementação

### Arquivos Modificados

1. **`src/ui/realtime_monitor.py`**
   - Adicionado estado `_debug_enabled` e lista `_debug_logs` na classe `RealTimeEncodingMonitor`
   - Implementado método `toggle_debug()` para alternar estado do debug
   - Implementado método `is_debug_enabled()` para verificar estado atual
   - Implementado método `_add_debug_log()` para adicionar logs com timestamp
   - Implementado método público `add_debug_log()` que verifica se debug está ativo antes de adicionar
   - Modificado `_generate_display()` para:
     - Exibir dica "Pressione 'D' para ativar/desativar debug"
     - Exibir seção de logs abaixo do monitoramento quando debug está ativado

2. **`src/ui/realtime_monitor.py` - FFmpegProgressParser**
   - Adicionado parâmetro `monitor` no construtor
   - Implementado método `_debug()` para enviar logs ao monitor
   - Atualizado `parse_line()` para usar sistema de debug logs em vez de prints diretos

3. **`src/core/encoder_engine.py`**
   - Implementado método `toggle_debug()` que delega para o monitor
   - Implementado método `is_debug_enabled()` que delega para o monitor
   - Atualizado para passar referência do monitor para o `FFmpegProgressParser`
   - Adicionado logs de debug no início/fim do encoding

4. **`src/cli.py`**
   - Implementada função `check_debug_key()` para capturar tecla 'D' (Windows e Linux/Mac)
   - Atualizado loop de processamento da fila para verificar tecla de debug

5. **`src/ui/queue_menu.py`**
   - Implementada função `check_debug_key()` para capturar tecla 'D' (Windows e Linux/Mac)
   - Atualizado loop de monitoramento para verificar tecla de debug

## Como Usar

1. Durante a conversão de vídeos, o monitor em tempo real exibe:
   - Informações de stream (entrada vs saída)
   - Estatísticas de encoding (FPS, Speed, Bitrate)
   - Uso de hardware (GPU, CPU, VRAM)
   - **Dica: "Pressione 'D' para ativar/desativar debug"**

2. Pressione a tecla **'D'** (maiúscula ou minúscula) para:
   - **Ativar debug**: Logs detalhados começam a ser exibidos abaixo do monitoramento
   - **Desativar debug**: Logs são ocultados, mantendo apenas o monitoramento principal

3. Quando ativado, os logs de debug exibem:
   - Timestamp de cada evento (HH:MM:SS)
   - Informações de parsing do FFmpeg
   - Progresso da conversão
   - Estatísticas extraídas (FPS, Speed, etc.)

## Exemplo de Logs de Debug

```
🐞 Debug Logs:

[14:30:15] Debug ativado
[14:30:15] Iniciando encoding
[14:30:15] Input: C:/Videos/input.mp4
[14:30:15] Output: C:/Videos/output.mp4
[14:30:16] Comando FFmpeg iniciado
[14:30:17] Executando encoding...
[14:30:20] Stats: FPS=30.5, Speed=1.20x
[14:30:25] Stats: FPS=29.8, Speed=1.18x
[14:30:30] Progresso = 5.2% (tempo: 31.2s / 600.0s)
```

## Compatibilidade

- **Windows**: Usa `msvcrt` para captura de teclas não-bloqueante
- **Linux/Mac**: Usa `termios` e `tty` para modo raw do terminal

## Benefícios

1. **Interface limpa**: Logs só são exibidos quando necessário
2. **Debug sob demanda**: Ativa/desativa sem reiniciar a conversão
3. **Logs contextualizados**: Timestamp e organização cronológica
4. **Não intrusivo**: Não interfere no processo de encoding

## Notas Técnicas

- Máximo de 50 logs são mantidos na memória (configurável via `_max_debug_logs`)
- Apenas os últimos 15 logs são exibidos na tela para não sobrecarregar a interface
- O sistema de debug logs é separado dos prints de debug do código (que podem ser removidos futuramente)
