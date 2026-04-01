# Plano de Implementação: Suporte a Diretório Remoto

## Visão Geral

Este plano descreve os passos para implementar o suporte a diretórios remotos no video-encoder, conforme especificado em [`PHASE_13_REMOTE_DIRECTORY.md`](PHASE_13_REMOTE_DIRECTORY.md).

## Protocolos Suportados

| Protocolo | Descrição | Biblioteca |
|-----------|-----------|------------|
| **SSHFS** | Filesystem sobre SSH | paramiko, sshfs |
| **SMB/CIFS** | Windows Share/Samba | smbprotocol |
| **NFS** | Network File System | nfs3 |
| **Mounted (rclone)** | Diretórios montados | pathlib (nativo) |
| **UNC** | Caminho de Rede Windows | pathlib (nativo) |

## Fases de Implementação

### Fase 1: Estrutura de Configuração e Utilitários Base
**Agente Responsável:** Backend Specialist

#### 1.1 Atualizar ConfigManager
- Adicionar suporte para `remote_connections` no config.json
- Adicionar suporte para configuração de `temp_base` e `auto_cleanup`
- Criar métodos para salvar/carregar conexões remotas

**Arquivos:**
- [`src/managers/config_manager.py`](src/managers/config_manager.py)

#### 1.2 Criar TempDirectoryManager
- Implementar classe para gerenciar diretórios temporários
- Criar métodos para criar, validar e limpar diretórios temp
- Implementar verificação de espaço em disco

**Arquivos:**
- [`src/utils/temp_directory_manager.py`](src/utils/temp_directory_manager.py) (novo)

#### 1.3 Atualizar path_utils
- Adicionar método para detectar se caminho é remoto
- Adicionar método para identificar protocolo

**Arquivos:**
- [`src/utils/path_utils.py`](src/utils/path_utils.py)

---

### Fase 2: Clientes de Protocolos Remotos
**Agente Responsável:** Backend Specialist

#### 2.1 Criar Interface Base RemoteProtocol
- Definir interface abstrata para protocolos
- Implementar métodos base

**Arquivos:**
- [`src/utils/remote/remote_protocol.py`](src/utils/remote/remote_protocol.py) (novo)

#### 2.2 Implementar SSHFSClient
- Implementar cliente SSHFS usando paramiko/sshfs
- Suportar autenticação por senha e chave SSH
- Implementar listagem de arquivos e cópia

**Arquivos:**
- [`src/utils/remote/sshfs_client.py`](src/utils/remote/sshfs_client.py) (novo)

#### 2.3 Implementar SMBClient
- Implementar cliente SMB/CIFS usando smbprotocol
- Suportar autenticação Windows/Samba
- Implementar listagem e cópia de arquivos

**Arquivos:**
- [`src/utils/remote/smb_client.py`](src/utils/remote/smb_client.py) (novo)

#### 2.4 Implementar NFSClient
- Implementar cliente NFS
- Suportar mount de exports NFS
- Implementar listagem e cópia de arquivos

**Arquivos:**
- [`src/utils/remote/nfs_client.py`](src/utils/remote/nfs_client.py) (novo)

#### 2.5 Implementar MountedClient
- Implementar acesso a diretórios montados (rclone, etc.)
- Usar pathlib para acesso nativo
- Implementar listagem e cópia de arquivos

**Arquivos:**
- [`src/utils/remote/mounted_client.py`](src/utils/remote/mounted_client.py) (novo)

#### 2.6 Implementar UNCClient
- Implementar acesso a caminhos UNC Windows
- Usar pathlib para acesso nativo

**Arquivos:**
- [`src/utils/remote/unc_client.py`](src/utils/remote/unc_client.py) (novo)

---

### Fase 3: RemoteDirectoryManager
**Agente Responsável:** Backend Specialist

#### 3.1 Criar RemoteDirectoryManager
- Implementar gerenciador central
- Factory para criar clientes baseado no protocolo
- Implementar método `copy_to_temp`

**Arquivos:**
- [`src/managers/remote_directory_manager.py`](src/managers/remote_directory_manager.py) (novo)

---

### Fase 4: Interface do Usuário
**Agente Responsável:** Frontend Specialist

#### 4.1 Atualizar Menu Principal
- Adicionar pergunta sobre tipo de diretório (local/remoto)
- Integrar com fluxo de conversão de pasta

**Arquivos:**
- [`src/ui/menu.py`](src/ui/menu.py)
- [`src/cli.py`](src/cli.py)

#### 4.2 Criar UI para Conexão Remota
- Implementar menu de seleção de protocolo
- Implementar formulários de configuração
- Implementar teste de conexão

**Arquivos:**
- [`src/ui/remote_connection_ui.py`](src/ui/remote_connection_ui.py) (novo)

#### 4.3 Implementar UI de Progresso de Cópia
- Exibir progresso de download/cópia
- Mostrar tempo estimado
- Permitir cancelamento

**Arquivos:**
- [`src/ui/remote_copy_progress.py`](src/ui/remote_copy_progress.py) (novo)

---

### Fase 5: Integração com Fluxo de Conversão
**Agente Responsável:** Backend Specialist

#### 5.1 Atualizar run_folder_mode
- Integrar RemoteDirectoryManager no fluxo
- Copiar arquivos para temp antes da conversão
- Limpar temp após conversão (opcional)

**Arquivos:**
- [`src/cli.py`](src/cli.py)

#### 5.2 Atualizar RecurrentFolderManager
- Adicionar suporte a diretórios remotos
- Configurar cópia automática para temp

**Arquivos:**
- [`src/managers/recurrent_folder_manager.py`](src/managers/recurrent_folder_manager.py)

---

### Fase 6: Testes e Documentação
**Agente Responsável:** Security & QA Tester

#### 6.1 Criar Testes Unitários
- Testes para TempDirectoryManager
- Testes para detectção de protocolo
- Testes para cada cliente remoto (mock)

**Arquivos:**
- [`tests/test_temp_directory.py`](tests/test_temp_directory.py) (novo)
- [`tests/test_remote_protocols.py`](tests/test_remote_protocols.py) (novo)

#### 6.2 Criar Testes de Integração
- Testar fluxo completo com servidor SFTP local
- Testar cópia SMB
- Testar cleanup de temp

**Arquivos:**
- [`tests/test_remote_integration.py`](tests/test_remote_integration.py) (novo)

#### 6.3 Documentação
- Atualizar README com novas funcionalidades
- Criar guia de uso de diretórios remotos

**Arquivos:**
- [`docs/PHASE_13_REMOTE_DIRECTORY_GUIDE.md`](docs/PHASE_13_REMOTE_DIRECTORY_GUIDE.md) (novo)

---

## Estrutura de Arquivos Proposta

```
src/
├── managers/
│   ├── config_manager.py (atualizar)
│   ├── remote_directory_manager.py (novo)
│   └── ...
├── utils/
│   ├── path_utils.py (atualizar)
│   ├── temp_directory_manager.py (novo)
│   └── remote/
│       ├── __init__.py (novo)
│       ├── remote_protocol.py (novo)
│       ├── sshfs_client.py (novo)
│       ├── smb_client.py (novo)
│       ├── nfs_client.py (novo)
│       ├── mounted_client.py (novo)
│       └── unc_client.py (novo)
├── ui/
│   ├── menu.py (atualizar)
│   ├── remote_connection_ui.py (novo)
│   └── remote_copy_progress.py (novo)
└── ...

tests/
├── test_temp_directory.py (novo)
├── test_remote_protocols.py (novo)
└── test_remote_integration.py (novo)
```

---

## Dependências Externas

Adicionar ao `requirements.txt` (ou similar):

```
paramiko>=3.0.0
smbprotocol>=1.9.0
requests>=2.28.0
sshfs>=2023.0.0
nfs3>=1.0.0
```

---

## Dependências de Sistema

### Windows
- WinFsp (para suporte a SSHFS)
- https://winfsp.dev/rel/

### Linux
- nfs-common (para NFS)
- sshfs (para SSHFS)

### Opcional
- rclone (para mounts de cloud storage)
- https://rclone.org/

---

## Critérios de Aceitação por Fase

### Fase 1
- [ ] ConfigManager salva/carrega conexões remotas
- [ ] TempDirectoryManager cria e limpa diretórios temp
- [ ] PathUtils detecta caminhos remotos

### Fase 2
- [ ] SFTPClient conecta e baixa arquivos
- [ ] SMBClient acessa shares e copia arquivos
- [ ] HTTPClient faz downloads com resume
- [ ] UNCClient acessa caminhos de rede

### Fase 3
- [ ] RemoteDirectoryManager gerencia todos os protocolos
- [ ] copy_to_temp funciona para todos os protocolos

### Fase 4
- [ ] UI pergunta se diretório é local ou remoto
- [ ] Configuração de conexão é intuitiva
- [ ] Progresso de cópia é exibido

### Fase 5
- [ ] Conversão inicia após cópia bem-sucedida
- [ ] Cleanup de temp funciona corretamente
- [ ] Pastas recorrentes suportam remoto

### Fase 6
- [ ] Todos os testes passam
- [ ] Documentação completa

---

## Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Paramiko incompatível com Windows | Alto | Testar exaustivamente no Windows |
| SMB requer credenciais Windows | Médio | Documentar requisitos |
| Downloads grandes falham | Médio | Implementar resume robusto |
| Espaço em disco insuficiente | Alto | Validar espaço antes de copiar |

---

## Estimativa de Esforço

| Fase | Complexidade |
|------|-------------|
| Fase 1 | Baixa |
| Fase 2 | Alta |
| Fase 3 | Média |
| Fase 4 | Média |
| Fase 5 | Média |
| Fase 6 | Baixa |
