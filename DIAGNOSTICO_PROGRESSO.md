# 🔍 Diagnóstico: Problema de Progresso Não Exibido Durante Encoding

## 📋 Sintomas Observados

- Interface de encoding é exibida corretamente
- Status mostra "Aguardando..."
- Barra de progresso permanece em 0.0%
- Estatísticas (FPS, Speed, Bitrate) mostram "--"
- GPU está ativa (27% utilização, 61°C, 2.14 GB VRAM)
- Encoding parece estar acontecendo mas progresso não é atualizado

## 🎯 Diagnóstico Inicial

### Possíveis Causas Identificadas (7 hipóteses):

1. **Parser de estatísticas não captura stderr do FFmpeg** ⚠️ PROVÁVEL
   - FFmpeg envia estatísticas via stderr
   - Pode não estar sendo lido corretamente

2. **Formato de output do NVENC difere do esperado** ⚠️ PROVÁVEL
   - Quando usando aceleração CUDA, formato pode ser diferente
   - Regex pode não fazer match

3. **Buffer do processo não está sendo lido em tempo real** 
   - Output pode estar bufferizado
   - Não chega ao parser em tempo real

4. **Thread de monitoramento bloqueada/não iniciada**
   - Thread que lê FFmpeg output pode estar travada

5. **Flag `-stats` conflita com hwaccel**
   - Formato CUDA pode alterar como estatísticas são emitidas

6. **Regex incompatível com output multilinha do NVENC**
   - NVENC pode ter formato diferente de linha

7. **Encoding realmente travado na inicialização CUDA**
   - Improvável, pois GPU mostra atividade

### ✅ Causas Mais Prováveis (Top 2):

1. **Parser não está capturando output ou formato é diferente**
2. **Callback chain está quebrado em algum ponto**

## 🔧 Ferramentas de Diagnóstico Criadas

### 1. Script de Teste Completo
**Arquivo:** `test_encoding_debug.py`

Script que:
- Executa um encoding de teste (10 segundos)
- Mostra TODAS as linhas recebidas do FFmpeg
- Identifica se linhas com indicadores de progresso chegam
- Mostra resultado do parsing
- Fornece relatório completo

**Como usar:**
```bash
# Ajuste o caminho do arquivo de entrada no script
# Linha 23: input_file = "SEU_ARQUIVO_AQUI.mkv"

python test_encoding_debug.py
```

### 2. Sistema de Patches Temporários
**Arquivos:** `apply_debug_patches.py` e `revert_debug_patches.py`

Sistema que:
- Adiciona logs extensivos em pontos críticos do código
- Faz backup automático dos arquivos originais
- Pode ser revertido facilmente

**Como usar:**
```bash
# 1. Aplicar patches (adiciona logs)
python apply_debug_patches.py

# 2. Execute sua conversão normalmente
python run.py  # ou como você executa

# 3. Observe os logs no console

# 4. Reverter patches (remove logs)
python revert_debug_patches.py
```

## 📊 Pontos de Log Adicionados

### Patch 1: ffmpeg_wrapper.py
- Log de TODAS as linhas recebidas do processo FFmpeg
- Mostra primeiras 5 linhas e depois a cada 20
- Identifica se output está chegando

### Patch 2: realtime_monitor.py
- Força debug mode sempre ativo
- Garante que logs do parser serão exibidos

### Patch 3: encoder_engine.py
- Log quando callback de progresso é chamado
- Mostra output recebido e stats extraídos
- Identifica se callback chain funciona

## 🔍 Análise Esperada

Após executar os patches, você verá um dos seguintes cenários:

### Cenário A: Nenhuma linha recebida
```
🔍 FFMPEG LINE #0: (nada)
```
**Causa:** Processo FFmpeg não está enviando output
**Solução:** Verificar se stderr está sendo capturado corretamente

### Cenário B: Linhas recebidas mas sem indicadores
```
🔍 FFMPEG LINE #1: ffmpeg version 4.4...
🔍 FFMPEG LINE #2: built with gcc...
(sem fps=, speed=, time=)
```
**Causa:** FFmpeg não está emitindo estatísticas de progresso
**Solução:** Adicionar ou corrigir flag `-stats` no comando

### Cenário C: Linhas com indicadores mas parsing falha
```
🔍 FFMPEG LINE #10: frame= 123 fps=45 speed=1.2x time=00:00:05.00
📊 CALLBACK #10: frame= 123 fps=45 speed=1.2x time=00:00:05.00
📊 STATS: {} (vazio!)
```
**Causa:** Regex do parser não faz match com formato do output
**Solução:** Ajustar regex no FFmpegProgressParser

### Cenário D: Parsing funciona mas UI não atualiza
```
🔍 FFMPEG LINE #10: frame= 123 fps=45 speed=1.2x time=00:00:05.00
📊 CALLBACK #10: frame= 123 fps=45 speed=1.2x time=00:00:05.00
📊 STATS: {'fps': 45, 'speed': 1.2, 'current_time': 5.0, 'progress': 2.5}
(mas UI ainda mostra 0%)
```
**Causa:** Problema na atualização da UI
**Solução:** Verificar thread de atualização do monitor

## ✅ Próximos Passos Recomendados

1. **Execute o script de teste:**
   ```bash
   python test_encoding_debug.py
   ```

2. **OU aplique os patches e execute conversão normal:**
   ```bash
   python apply_debug_patches.py
   # Execute sua conversão
   python revert_debug_patches.py
   ```

3. **Analise os logs gerados** e identifique qual cenário ocorre

4. **Reporte os resultados** para que possamos aplicar a correção apropriada

## 🎯 Correção Esperada

Baseado nos logs, aplicaremos uma das seguintes correções:

- **Se output não chega:** Corrigir captura de stderr
- **Se formato é diferente:** Ajustar regex do parser
- **Se callback não é chamado:** Corrigir chain de callbacks
- **Se UI não atualiza:** Corrigir thread de atualização

## 📝 Informações Adicionais

### Código Relevante Analisado

1. **ffmpeg_wrapper.py linhas 352-443:**
   - Processo iniciado com `stderr=subprocess.STDOUT`
   - Leitura não-bloqueante configurada
   - Callback chamado para cada linha

2. **realtime_monitor.py linhas 656-732:**
   - Parser com regex para fps, speed, bitrate, time
   - Patterns: `fps=(\d+\.?\d*)`, `speed=(\d+\.?\d*)x`, etc.

3. **encoder_engine.py linhas 310-323:**
   - Callback que chama parser
   - Atualiza monitor com stats extraídos

### Flags FFmpeg Observadas
```bash
-y -stats -hwaccel cuda -hwaccel_output_format cuda
```

A flag `-stats` está presente, o que deveria forçar emissão de estatísticas.

---

**Criado em:** 2026-04-01  
**Modo:** Debug  
**Status:** Aguardando execução dos testes de diagnóstico
