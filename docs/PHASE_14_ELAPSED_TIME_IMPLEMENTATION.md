# Fase 14: Implementação do Tempo Decorrido na Janela de Conversão

## Visão Geral

Esta fase implementa a exibição do tempo decorrido na janela de conversão de arquivos. O objetivo é fornecer ao usuário informações em tempo real sobre quanto tempo já passou desde o início de cada processo de conversão.

## Alterações Realizadas

### 1. Modificação do RealTimeEncodingMonitor

#### Arquivo: `src/ui/realtime_monitor.py`

- Adicionado atributo `_elapsed_time` para armazenar o tempo decorrido
- Atualizado o método `update_progress()` para calcular e atualizar o tempo decorrido
- Adicionado campo "Tempo Decorrido" à tabela de estatísticas de encoding
- Corrigido o título do painel para evitar problemas com caracteres Unicode no Windows

### 2. Detalhes Técnicos

#### Cálculo do tempo decorrido:
- O tempo decorrido é calculado como a diferença entre o tempo atual e o tempo de início do processo
- O formato exibido é HH:MM:SS
- O cálculo é feito tanto quando há informações de duração quanto quando não há

#### Interface:
- O tempo decorrido é exibido na tabela de estatísticas de encoding ao lado de outros dados como FPS, velocidade, bitrate, etc.
- O formato de exibição segue o padrão HH:MM:SS para consistência com o tempo restante

## Código Modificado

### Novos Atributos
```python
self._elapsed_time: str = "00:00:00"  # Tempo decorrido desde o início do processo
```

### Atualização do Método update_progress
```python
def update_progress(self, progress: float, current_time: float = 0):
    """Atualiza progresso."""
    with self._lock:
        self._progress = progress
        self._current_time = current_time
        if self._total_duration > 0 and current_time > 0:
            elapsed = time.time() - self._start_time
            if progress > 0:
                estimated_total = elapsed / (progress / 100)
                remaining = estimated_total - elapsed
                self._time_remaining = time.strftime('%H:%M:%S', time.gmtime(max(0, remaining)))
            # Calcular tempo decorrido
            self._elapsed_time = time.strftime('%H:%M:%S', time.gmtime(elapsed))
        else:
            # Calcular tempo decorrido mesmo sem informações de duração
            elapsed = time.time() - self._start_time
            self._elapsed_time = time.strftime('%H:%M:%S', time.gmtime(elapsed))
        
        # Quando o progresso atinge 100%, atualiza o status automaticamente
        if progress >= 100.0:
            self._status = "Finalizado"
```

### Atualização da Tabela de Estatísticas
```python
encoding_table.add_row("Tempo Decorrido:", self._elapsed_time)
```

## Testes Realizados

Um script de teste (`test_elapsed_time.py`) foi criado e executado com sucesso para validar a funcionalidade. O teste confirma que:

- O tempo decorrido é calculado corretamente
- O tempo decorrido é exibido na interface
- Não ocorrem erros durante a execução
- O formato de exibição é adequado (HH:MM:SS)

## Benefícios

- O usuário pode acompanhar quanto tempo já foi gasto com o processo de conversão
- Melhora a experiência do usuário com informações mais completas
- Facilita a estimativa de tempo total necessário para processos longos
- Fornece contexto adicional sobre o desempenho do sistema

## Compatibilidade

- A funcionalidade é compatível com todas as plataformas suportadas
- Não afeta o desempenho do processo de conversão
- Funciona com todos os tipos de perfis e codecs suportados
- Integra-se perfeitamente com o sistema existente de monitoramento em tempo real