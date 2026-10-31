# Camada de Infraestrutura (Infrastructure Layer)

A Camada de Infraestrutura implementa os detalhes técnicos, comunicação de rede, persistência de dados no disco e configurações operacionais.

---

## Estrutura de Módulos

```text
infra/
├── config/
│   └── settings.py      # AppConfig e carregamento de variáveis de ambiente
├── network/
│   └── tcp_server.py    # Gerenciamento de sockets TCP e ciclo de vida de conexões
└── storage/
    └── filesystem.py    # Implementação de StorageRepository sobre o disco local
```

---

## Decisões de Arquitetura

### 1. Network Layer (`network/tcp_server.py`)
- **Sockets TCP Nativos:** Utiliza a biblioteca padrão `socket` de baixo nível (`AF_INET`, `SOCK_STREAM`), dispensando frameworks de alto nível que não se adequam ao modelo de socket cru do PTA.
- **Isolamento de Conexões:** Cada cliente conectado é atendido em uma rotina isolada (`_handle_client`). Falhas de comunicação, encerramentos abruptos ou timeouts de um cliente específico são capturados e tratados, garantindo que o servidor principal continue ativo para novos clientes.
- **Port Reuse:** Configura `SO_REUSEADDR` para evitar travamentos de porta ao reiniciar o serviço rapidamente.

### 2. Storage Layer (`storage/filesystem.py`)
- **Implementação de Repositório:** Concretiza a interface `StorageRepository` definida pelo Domínio.
- **Proteção contra Directory Traversal:**
  - O método `read_file()` resolve os caminhos utilizando `pathlib.Path.resolve()`.
  - Valida se o caminho absoluto do arquivo solicitado pertence estritamente ao diretório `files/` configurado.
  - Requisições maliciosas com sequências `../` são bloqueadas com lançamento de `PermissionError`, resultando em resposta `NOK` ao cliente.

### 3. Settings (`config/settings.py`)
- Define a classe imutável `AppConfig(frozen=True)`.
- Recupera parâmetros de ambiente via `os.getenv` com valores padrão seguros (porta 11550, buffer 2048, log level INFO).
