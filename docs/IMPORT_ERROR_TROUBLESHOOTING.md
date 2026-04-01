# Troubleshooting: Import Error

## Erro Comum: "ImportError: attempted relative import with no known parent package"

### Descrição do Problema

Este erro ocorre quando você tenta executar o CLI diretamente usando:

```bash
python3 src/cli.py --interactive
```

**Mensagem de erro completa:**
```
ImportError: attempted relative import with no known parent package
```

### Causa Raiz

O arquivo `src/cli.py` usa **importações relativas** (imports que começam com `.`):

```python
from .managers.config_manager import ConfigManager
from .core.ffmpeg_wrapper import FFmpegWrapper
# ... etc
```

Quando você executa um arquivo Python diretamente (`python3 src/cli.py`), o Python não reconhece que ele faz parte de um pacote, então as importações relativas falham.

### Soluções

#### ✅ Solução 1: Usar o Script Wrapper (Recomendado)

Execute o wrapper `run.py` no diretório raiz:

```bash
cd /opt/video-encoder
python3 run.py --interactive
```

**Vantagens:**
- Mais simples e direto
- Funciona em Windows e Linux
- Não requer conhecimento de módulos Python

#### ✅ Solução 2: Executar Como Módulo Python

Execute o CLI como um módulo Python:

```bash
cd /opt/video-encoder
python3 -m src --interactive
```

Ou de forma mais explícita:

```bash
python3 -m src.cli --interactive
```

**Vantagens:**
- Método Python "oficial"
- Funciona sem scripts adicionais
- Mantém o contexto do pacote

#### ✅ Solução 3: Configurar PYTHONPATH (Temporário)

```bash
export PYTHONPATH=/opt/video-encoder:$PYTHONPATH
python3 -m src.cli --interactive
```

**Vantagens:**
- Útil para debugging
- Permite importações absolutas

**Desvantagens:**
- Requer configuração toda vez
- Variável de ambiente não persiste

#### ❌ O Que NÃO Fazer

Não execute o arquivo diretamente:
```bash
# ❌ ERRADO - Causa ImportError
python3 src/cli.py --interactive

# ❌ ERRADO - Mesmo erro
./src/cli.py --interactive
```

## Comparação dos Métodos

| Método | Comando | Complexidade | Compatibilidade |
|--------|---------|--------------|-----------------|
| Script Wrapper | `python3 run.py` | ⭐ Simples | ✅ Windows/Linux |
| Módulo Python | `python3 -m src` | ⭐⭐ Média | ✅ Windows/Linux |
| PYTHONPATH | `export PYTHONPATH=...` | ⭐⭐⭐ Avançado | ⚠️ Temporário |

## Arquivos Criados para Resolver o Problema

### 1. `src/__main__.py`
Permite executar o pacote como módulo (`python3 -m src`):

```python
from .cli import main

if __name__ == '__main__':
    main()
```

### 2. `run.py`
Script wrapper no diretório raiz para execução fácil:

```python
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cli import main

if __name__ == '__main__':
    main()
```

## Execução em Diferentes Ambientes

### Linux/Unix (Servidor)
```bash
cd /opt/video-encoder
python3 run.py --interactive
```

### Windows (Desenvolvimento)
```cmd
cd C:\projetos\video-encoder
python run.py --interactive
```

### Docker Container
```bash
docker exec -it container_name python3 /app/run.py --interactive
```

### Systemd Service
```ini
[Service]
WorkingDirectory=/opt/video-encoder
ExecStart=/usr/bin/python3 /opt/video-encoder/run.py --watch
```

## Entendendo Importações Relativas vs Absolutas

### Importações Relativas (Usadas no projeto)
```python
# Relativas ao pacote atual
from .managers import ConfigManager
from ..utils import FileUtils
```

**Requisitos:**
- O arquivo deve fazer parte de um pacote (diretório com `__init__.py`)
- Não pode ser executado diretamente como script
- Deve ser executado como módulo (`-m`) ou importado

### Importações Absolutas (Alternativa)
```python
# Caminhos completos
from src.managers import ConfigManager
from src.utils import FileUtils
```

**Requisitos:**
- O diretório raiz deve estar no `PYTHONPATH`
- Mais verboso, mas funciona em mais contextos

## Boas Práticas

1. **✅ Use o script wrapper `run.py`** para execução diária
2. **✅ Use `python3 -m src`** para automação e CI/CD
3. **✅ Configure PYTHONPATH** apenas para desenvolvimento/debugging
4. **❌ Nunca execute** `python3 src/cli.py` diretamente

## Links Relacionados

- [README.md](../README.md) - Documentação principal com exemplos de uso
- [Python Modules Documentation](https://docs.python.org/3/tutorial/modules.html)
- [PEP 328 - Imports: Multi-Line and Absolute/Relative](https://www.python.org/dev/peps/pep-0328/)

## Suporte

Se você ainda tiver problemas após seguir este guia:

1. Verifique que está no diretório correto (`/opt/video-encoder`)
2. Confirme que Python 3.8+ está instalado (`python3 --version`)
3. Verifique que todas as dependências estão instaladas (`pip3 list`)
4. Revise os logs de erro completos para identificar outros problemas
