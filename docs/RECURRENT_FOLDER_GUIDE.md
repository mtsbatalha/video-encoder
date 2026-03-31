# Guia de Codificação Recorrente

## Introdução

A **Codificação Recorrente** é uma funcionalidade que permite monitorar continuamente pastas específicas e processar automaticamente novos arquivos de vídeo que são adicionados a elas. Diferente da codificação única (que processa todos os arquivos de uma vez), a codificação recorrente mantém um monitor ativo que detecta e enfileira novos arquivos automaticamente.

### Quando Usar

| Cenário | Tipo Recomendado |
|---------|------------------|
| Processar uma coleção existente de vídeos | Codificação Única |
| Downloads automáticos de torrents | Codificação Recorrente |
| Pasta de captura de DVR/streaming | Codificação Recorrente |
| Backup de vídeos de câmera | Codificação Recorrente |
| Processamento pontual de arquivos | Codificação Única |

### Como Funciona

1. Você configura uma pasta de entrada e uma pasta de saída
2. O sistema monitora a pasta de entrada periodicamente
3. Quando um novo arquivo é detectado:
   - Verifica se o arquivo está completo (debounce)
   - Valida extensão e tamanho mínimo
   - Adiciona automaticamente à fila de codificação
4. O arquivo é processado conforme o perfil selecionado
5. O histórico é registrado para acompanhamento

---

## Configuração Rápida

### Passo a Passo Inicial

1. **Inicie o menu interativo:**
   ```bash
   python vigia_nvenc.py --interactive
   ```

2. **Selecione "Gerenciar Conversões Recorrentes"** no menu principal

3. **Escolha "Adicionar nova pasta recorrente"**

4. **Preencha as informações básicas:**
   - **Nome descritivo:** Ex: "Downloads de Séries"
   - **Caminho de entrada:** Ex: `C:/Downloads/Series`
   - **Caminho de saída:** Ex: `D:/Videos/Series_Encoded`
   - **Perfil:** Selecione um perfil de codificação

5. **Configure as opções adicionais:**
   - Preservar subdiretórios: Sim/Não
   - Pular arquivos existentes: Sim/Não
   - Excluir origem após codificação: Sim/Não
   - Copiar legendas: Sim/Não

6. **Confirme e adicione a pasta**

7. **Inicie o monitor:**
   - Volte ao menu principal
   - Selecione "Iniciar/Parar monitores"
   - Escolha "Iniciar todos os monitores"

---

## Menu Principal

Ao acessar **"Gerenciar Conversões Recorrentes"**, você verá as seguintes opções:

| Opção | Descrição |
|-------|-----------|
| 1. Listar pastas recorrentes | Mostra todas as pastas configuradas com status |
| 2. Adicionar nova pasta recorrente | Cria uma nova configuração de monitoramento |
| 3. Remover pasta recorrente | Remove uma configuração existente |
| 4. Editar pasta recorrente | Modifica configurações de uma pasta |
| 5. Ativar/Desativar pasta | Habilita ou desabilita o monitoramento |
| 6. Iniciar/Parar monitores | Controla a execução dos monitores ativos |
| 7. Ver histórico de processamento | Visualiza o histórico e estatísticas |
| 0. Voltar ao menu principal | Retorna ao menu anterior |

---

## Opções de Configuração

### preserve_subdirectories

**Tipo:** `boolean`  
**Padrão:** `true`

Quando habilitado, preserva a estrutura de subdiretórios da pasta de entrada na pasta de saída.

**Exemplo:**
```
Entrada: C:/Videos/
├── Filme1.mkv
└── Pasta/
    └── Filme2.mkv

Saída (preserve_subdirectories=true):
D:/Encoded/
├── Filme1.mkv
└── Pasta/
    └── Filme2.mkv
```

### delete_source_after_encode

**Tipo:** `boolean`  
**Padrão:** `false`

Exclui o arquivo de origem após a codificação ser concluída com sucesso.

⚠️ **Atenção:** Use com cautela. Certifique-se de que a codificação foi bem-sucedida antes de habilitar esta opção.

### copy_subtitles

**Tipo:** `boolean`  
**Padrão:** `true`

Copia arquivos de legenda (.srt, .sub, .idx) associados aos vídeos para a pasta de saída.

### supported_extensions

**Tipo:** `array[string]`  
**Padrão:** `[".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpeg", ".mpg"]`

Lista de extensões de arquivo que serão monitoradas. Apenas arquivos com estas extensões serão processados.

**Exemplo de personalização:**
```json
"supported_extensions": [".mp4", ".mkv", ".avi"]
```

### min_file_size_mb

**Tipo:** `number`  
**Padrão:** `0`

Tamanho mínimo do arquivo em megabytes. Arquivos menores que este valor serão ignorados.

**Caso de uso:** Evitar processar arquivos temporários ou incompletos.

### skip_existing_output

**Tipo:** `boolean`  
**Padrão:** `true`

Quando habilitado, verifica se o arquivo de saída já existe antes de adicionar à fila. Se existir, o arquivo é pulado.

---

## Gerenciamento

### Listar Pastas

Para visualizar todas as pastas recorrentes configuradas:

1. Acesse: **Gerenciar Conversões Recorrentes → 1. Listar pastas recorrentes**

A tabela exibirá:
- Número de identificação
- Nome descritivo
- Caminho de entrada
- Caminho de saída
- Perfil de codificação
- Status (Ativa/Desativada, Pasta existe/não existe)
- Total de arquivos processados

### Adicionar Pasta

1. Acesse: **Gerenciar Conversões Recorrentes → 2. Adicionar nova pasta recorrente**

2. Preencha o formulário:
   ```
   Nome descritivo: [Digite um nome]
   Caminho da pasta de entrada: [Caminho completo]
   Caminho da pasta de saída: [Caminho completo]
   Número do perfil: [Selecione da lista]
   ```

3. Configure as opções:
   ```
   Preservar subdiretórios no output? [y/n]
   Pular arquivos já existentes no output? [y/n]
   Excluir arquivo de origem após conversão? [y/n]
   Copiar legendas? [y/n]
   ```

4. Confirme a adição

### Editar Pasta

1. Acesse: **Gerenciar Conversões Recorrentes → 4. Editar pasta recorrente**

2. Selecione a pasta pelo número

3. Modifique os campos desejados (pressione Enter para manter o valor atual)

4. Confirme as alterações

### Remover Pasta

1. Acesse: **Gerenciar Conversões Recorrentes → 3. Remover pasta recorrente**

2. Selecione a pasta pelo número

3. Confirme a remoção

⚠️ **Atenção:** A remoção não apaga arquivos já codificados, apenas remove a configuração de monitoramento.

### Ativar/Desativar

1. Acesse: **Gerenciar Conversões Recorrentes → 5. Ativar/Desativar pasta**

2. Selecione a pasta

3. Escolha ativar ou desativar

Pastas desativadas não são monitoradas, mas mantêm suas configurações salvas.

### Iniciar/Parar Monitores

1. Acesse: **Gerenciar Conversões Recorrentes → 6. Iniciar/Parar monitores**

Opções disponíveis:
- **Iniciar todos os monitores:** Inicia o monitoramento de todas as pastas ativas
- **Parar todos os monitores:** Para todos os monitores em execução
- **Iniciar monitor específico:** Inicia apenas um monitor selecionado
- **Parar monitor específico:** Para apenas um monitor selecionado

---

## Histórico e Estatísticas

### Visualizar Histórico

1. Acesse: **Gerenciar Conversões Recorrentes → 7. Ver histórico de processamento**

2. Selecione a pasta para visualizar

O histórico mostra:
- Arquivo de entrada
- Arquivo de saída
- Status (completo/falhou)
- Data/hora de início e conclusão
- Duração do processamento
- Mensagem de erro (se aplicável)

### Estatísticas

As estatísticas incluem:
- **Total processado:** Número total de arquivos processados
- **Sucessos:** Quantidade de codificações bem-sucedidas
- **Falhas:** Quantidade de codificações que falharam
- **Duração total:** Tempo total de processamento
- **Duração média:** Tempo médio por arquivo
- **Último processamento:** Data/hora do último arquivo processado

### Limpar Histórico

Para limpar o histórico de uma pasta específica:
1. No menu de histórico, selecione a opção de limpar
2. Confirme a ação

---

## Exemplos de Uso

### Exemplo 1: Downloads Automáticos

**Cenário:** Você usa um cliente de torrents que baixa séries para uma pasta específica.

**Configuração:**
```json
{
  "name": "Series Downloads",
  "input_directory": "C:/Downloads/Torrents/Series",
  "output_directory": "D:/Videos/Series",
  "profile_id": "nvidia-series-1080p-hevc",
  "options": {
    "preserve_subdirectories": true,
    "delete_source_after_encode": false,
    "copy_subtitles": true,
    "skip_existing_output": true,
    "min_file_size_mb": 100
  }
}
```

### Exemplo 2: Backup de Câmera de Segurança

**Cenário:** Câmeras de segurança gravam vídeos continuamente em uma pasta.

**Configuração:**
```json
{
  "name": "Backup Câmeras",
  "input_directory": "E:/Camera_Recordings",
  "output_directory": "F:/Backup/Cameras_Compressed",
  "profile_id": "nvidia-low-motion-hevc",
  "options": {
    "preserve_subdirectories": false,
    "delete_source_after_encode": true,
    "copy_subtitles": false,
    "skip_existing_output": false,
    "min_file_size_mb": 10
  }
}
```

### Exemplo 3: Processamento de DVR

**Cenário:** DVR grava programas de TV em uma pasta compartilhada.

**Configuração:**
```json
{
  "name": "Gravações DVR",
  "input_directory": "//nas/dvr/recordings",
  "output_directory": "D:/TV_Shows",
  "profile_id": "nvidia-tv-720p-hevc",
  "options": {
    "preserve_subdirectories": true,
    "delete_source_after_encode": false,
    "copy_subtitles": true,
    "skip_existing_output": true,
    "min_file_size_mb": 200,
    "supported_extensions": [".mp4", ".ts", ".mkv"]
  }
}
```

---

## Troubleshooting

### Problemas Comuns

#### Monitor Não Inicia

**Sintoma:** Ao tentar iniciar o monitor, ele não começa o monitoramento.

**Causas possíveis:**
- Pasta de entrada não existe
- Sem permissão de leitura na pasta
- Perfil de codificação inválido

**Soluções:**
1. Verifique se o caminho de entrada existe
2. Verifique as permissões da pasta
3. Confirme que o perfil selecionado existe no `profiles.json`

#### Arquivos Não São Processados

**Sintoma:** Novos arquivos são adicionados à pasta, mas não são processados.

**Causas possíveis:**
- Extensão do arquivo não está na lista de suportadas
- Arquivo abaixo do tamanho mínimo configurado
- Arquivo de saída já existe (skip_existing_output = true)

**Soluções:**
1. Verifique a extensão do arquivo
2. Ajuste `min_file_size_mb` se necessário
3. Verifique se o output já existe

#### Monitor Para Inesperadamente

**Sintoma:** O monitor para de funcionar após algum tempo.

**Causas possíveis:**
- Erro de permissão ao tentar escrever output
- Espaço em disco insuficiente
- Perfil de codificação foi removido

**Soluções:**
1. Verifique espaço em disco disponível
2. Confirme permissões de escrita na pasta de saída
3. Reinicie o monitor

#### Arquivos São Processados Múltiplas Vezes

**Sintoma:** O mesmo arquivo é codificado repetidamente.

**Causas possíveis:**
- `skip_existing_output` está desabilitado
- Output está sendo removido após codificação

**Soluções:**
1. Habilite `skip_existing_output`
2. Verifique se não há processos removendo os arquivos de saída

### Logs e Debug

Para diagnosticar problemas, verifique os logs:

1. **Logs da aplicação:**
   ```
   logs/
   ├── app.log
   └── monitor.log
   ```

2. **Habilite logging detalhado no `config.json`:**
   ```json
   "logging": {
     "level": "DEBUG"
   }
   ```

3. **Verifique o status dos monitores:**
   - No menu interativo, visualize o status
   - Monitores ativos devem mostrar "is_running: true"

---

## API Reference

Para desenvolvedores que desejam integrar programaticamente, consulte [`docs/RECURRENT_FOLDER_API.md`](RECURRENT_FOLDER_API.md) para documentação completa da API.

### Classes Principais

- [`RecurrentFolderManager`](../src/managers/recurrent_folder_manager.py) - Gerenciamento CRUD
- [`WatchFolderMonitor`](../src/core/watch_folder_monitor.py) - Monitoramento de pastas
- [`RecurrentMonitorService`](../src/services/recurrent_monitor_service.py) - Orquestração
- [`RecurrentHistoryManager`](../src/managers/recurrent_history_manager.py) - Histórico

---

## Dicas e Melhores Práticas

1. **Use nomes descritivos** para facilitar a identificação das pastas
2. **Configure `min_file_size_mb`** para evitar processar arquivos temporários
3. **Habilite `skip_existing_output`** para evitar retrabalho
4. **Monitore o espaço em disco** regularmente
5. **Revise o histórico periodicamente** para identificar falhas
6. **Use perfis adequados** ao tipo de conteúdo (filmes vs séries vs esportes)
7. **Considere usar `delete_source_after_encode`** apenas após validar a qualidade

---

## Suporte

Para mais informações:
- [README Principal](../README.md)
- [Plano de Implementação](../plans/IMPLEMENTATION_PLAN.md)
- [Especificação Técnica](../plans/SPEC.md)
