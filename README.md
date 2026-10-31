# Protocolo de Transferência de Arquivos (PTA) — Servidor

Implementação de referência do servidor para o Protocolo de Transferência de Arquivos (PTA), desenvolvido em conformidade estrita com a especificação didática apresentada no documento `pta.pdf`.

A solução foi projetada sob a ótica de Engenharia de Software Moderna e **Computação em Nuvem (Cloud Computing)**, aplicando princípios de Clean Architecture, separação em camadas (Domínio, Aplicação, Infraestrutura), padrões de projeto GoF (State Pattern e Command Pattern) e diretrizes de resiliência, escalabilidade e conteinerização.

---

## 1. Visão Geral da Arquitetura e Decisões de Design

A arquitetura dissocia completamente o protocolo de comunicação (regras de transição de estado e tratamento de comandos) dos detalhes de infraestrutura (sockets TCP, leitura de arquivos em disco e variáveis de ambiente).

```text
                      +------------------------------------------+
                      |               Cliente TCP                |
                      +------------------------------------------+
                                           |
                                  (Socket TCP :11550)
                                           v
[ INFRAESTRUTURA ]    +------------------------------------------+
                      |      TcpServer (ThreadPoolExecutor)      |
                      +------------------------------------------+
                                           |
                                (String crua recebida)
                                           v
[ APLICAÇÃO ]         +------------------------------------------+
                      |       ProtocolApplicationService         |
                      |        MessageParser (DTO Parse)         |
                      +------------------------------------------+
                                           |
                           (RequestMessage DTO tipado)
                                           v
[ DOMÍNIO ]           +------------------------------------------+
                      |       SessionContext (FSM Manager)       |
                      |                                          |
                      |   [State Pattern]                        |
                      |   - WaitingState (Autenticação CUMP)     |
                      |   - ReadyState   (Despacho de Comandos)  |
                      |                                          |
                      |   [Command Pattern]                      |
                      |   - ListCommandHandler                   |
                      |   - PegaCommandHandler                   |
                      |   - TermCommandHandler                   |
                      +------------------------------------------+
                                           |
                            (Inversão de Dependência)
                                           v
[ CONTRATO DOMÍNIO ]  +------------------------------------------+
                      |         StorageRepository (Port)         |
                      +------------------------------------------+
                                           ^
                                           | (Implementa interface)
[ INFRAESTRUTURA ]    +------------------------------------------+
                      |    FileSystemStorage (Adapter seguro)    |
                      +------------------------------------------+
```

---

## 2. Pilares de Computação em Nuvem (Cloud Native)

Como o projeto se insere no contexto de Computação em Nuvem, foram implementadas salvaguardas e padrões recomendados para cargas de trabalho de rede resilientes:

### 2.1. Concorrência e Gestão de Recursos (Resource Throttling)
- **Problema:** A criação irrestrita de processos ou threads por conexão (`Thread per connection`) expõe a aplicação a ataques de negação de serviço (DoS/Fork Bomb) e exaustão de descritores de arquivo ou memória da máquina host.
- **Solução Implementada:** Utilização de um pool pré-alocado e controlado via `ThreadPoolExecutor` com tamanho configurável (`PTA_MAX_WORKERS`, padrão 10). Conexões excedentes aguardam ordenadamente na fila do backlog do socket configurável (`PTA_BACKLOG`, padrão 128) sem degradar a estabilidade do nó de computação.

### 2.2. Resiliência e Mitigação de Ataques DoS (Buffer Flood e Slowloris)
- **Proteção contra Buffer Flood (OOM):** Implementado teto máximo de tamanho por mensagem (`PTA_MAX_MESSAGE_SIZE`, padrão 65536 bytes / 64KB). Streams intermináveis enviados por clientes maliciosos são interrompidos antes de provocar estouro de memória RAM.
- **Mitigação de Slowloris:** Aplicação de timeout estrito por socket (`PTA_SOCKET_TIMEOUT`, padrão 30.0s). Conexões inativas são encerradas de forma segura e determinística via bloco `finally` com `client_sock.shutdown(socket.SHUT_RDWR)` e `close()`, liberando recursos de imediato.

### 2.3. Isolamento e Contenção de Falhas (Fault Isolation)
- Exceções ocorridas na sessão de um cliente conectado (como desconexão repentina, dados truncados ou arquivos inexistentes) são capturadas e tratadas exclusivamente dentro do worker correspondente.
- A falha de um cliente jamais interrompe o socket de escuta principal ou prejudica outros clientes conectados.

### 2.4. Escalabilidade Horizontal e Statelessness
- O protocolo mantém estado em memória apenas durante o ciclo de vida da conexão TCP ativa (sessão local efêmera).
- **Adequação para Kubernetes / Load Balancer:** Em um cenário de produção em larga escala, o serviço pode ser escalado horizontalmente criando múltiplas réplicas do container atrás de um balanceador de carga TCP de camada 4 (ex.: AWS Network Load Balancer ou NGINX Stream com IP Hash / Source IP Affinity), permitindo aumento dinâmico de capacidade sem alterar o código de domínio.
- **Persistência Externa:** Graças à Inversão de Dependência (`StorageRepository`), a camada de armazenamento local (`FileSystemStorage`) pode ser substituída sem alterações no domínio por um adapter de armazenamento em nuvem compartilhado (ex.: bucket Amazon S3, Google Cloud Storage ou volume NFS/EFS montado).

### 2.5. Conteinerização e Observabilidade (12-Factor App)
- **Configuração via Ambiente:** Toda a parametrização de rede, portas, concorrência, timeouts e caminhos de arquivos respeita o princípio III do Twelve-Factor App, sendo injetada via variáveis de ambiente (`.env`).
- **Logs Estruturados e Suporte a JSON:** Suporte a logs de texto simples ou formato JSON estruturado (`PTA_LOG_JSON=true`) com timestamps ISO e níveis de severidade, permitindo ingestão automática por pipelines de observabilidade (ex.: AWS CloudWatch, Datadog, Prometheus/Grafana Loki).
- **Eficiência da Imagem:** Baseada em `python:3.12-slim`, resultando em footprint reduzido de memória e menor superfície de vulnerabilidades.

---

## 3. Variáveis de Ambiente Disponíveis

| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `PTA_HOST` | `0.0.0.0` | Endereço IP de escuta do socket TCP |
| `PTA_PORT` | `11550` | Porta TCP do serviço PTA |
| `PTA_BUFFER_SIZE` | `2048` | Tamanho do buffer de leitura do socket (bytes) |
| `PTA_BACKLOG` | `128` | Tamanho da fila de conexões pendentes no SO |
| `PTA_MAX_MESSAGE_SIZE` | `65536` | Limite máximo de bytes por mensagem de comando (proteção DoS/OOM) |
| `PTA_ENCODING` | `ascii` | Codificação de caracteres para mensagens textuais |
| `PTA_MAX_WORKERS` | `10` | Quantidade máxima de threads simultâneas no ThreadPool |
| `PTA_SOCKET_TIMEOUT` | `30.0` | Tempo máximo de inatividade por conexão antes de encerrar (segundos) |
| `PTA_LOG_LEVEL` | `INFO` | Nível de detalhamento dos logs (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `PTA_LOG_JSON` | `false` | Se `true`, emite logs em formato JSON estruturado para observabilidade |
| `PTA_USERS_FILE` | *(automático)* | Caminho customizado para o arquivo `users.txt` |
| `PTA_FILES_DIR` | *(automático)* | Caminho customizado para o diretório de arquivos `files/` |

---

## 4. Documentação Detalhada por Camada

Para explicações detalhadas sobre as decisões de implementação de cada camada, consulte os respectivos arquivos:

- **[Camada de Domínio](pta-server/domain/README.md):** Modelos, contratos, Máquina de Estados Finita (State Pattern) e processadores de comandos (Command Pattern).
- **[Camada de Aplicação](pta-server/application/README.md):** Parsing de mensagens e serviços de orquestração de caso de uso.
- **[Camada de Infraestrutura](pta-server/infra/README.md):** Manipulação de sockets TCP de rede, ThreadPoolExecutor, persistência no sistema de arquivos e configurações.

---

## 5. Estrutura de Diretórios

```text
pta/
├── pta-server/
│   ├── domain/
│   │   ├── README.md
│   │   ├── models.py
│   │   ├── repositories.py
│   │   ├── state_machine.py
│   │   ├── states/
│   │   │   ├── base.py
│   │   │   ├── waiting.py
│   │   │   └── ready.py
│   │   └── commands/
│   │       ├── base.py
│   │       └── handlers.py
│   ├── application/
│   │   ├── README.md
│   │   ├── parser.py
│   │   └── service.py
│   ├── infra/
│   │   ├── README.md
│   │   ├── config/
│   │   │   └── settings.py
│   │   ├── network/
│   │   │   └── tcp_server.py
│   │   └── storage/
│   │       └── filesystem.py
│   ├── files/
│   ├── users.txt
│   └── main.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── pta-client.py
├── comprehensive_tests.py
├── pta.pdf
└── README.md
```

---

## 6. Instruções de Execução

### 6.1. Execução via Docker (Ambiente Recomendado)

O projeto conta com configuração para Docker e Docker Compose com *live reload* automático para desenvolvimento. 
Dentro do container, a ferramenta `watchmedo` (CLI da biblioteca `watchdog` versão `6.0.0`) monitora recursivamente qualquer alteração em arquivos `.py` no diretório `/app` e reinicia o processo do servidor instantaneamente sem necessidade de reconstruir a imagem:
```bash
watchmedo auto-restart --directory=/app --pattern=*.py --recursive -- python -u main.py
```

1. Criar o arquivo de ambiente com base no exemplo:
   ```bash
   cp .env.example .env
   ```

2. Iniciar o container em segundo plano:
   ```bash
   docker compose up -d
   ```

3. Exibir os logs da aplicação em tempo real:
   ```bash
   docker compose logs -f
   ```

4. Parar a execução dos containers:
   ```bash
   docker compose down
   ```

### 6.2. Execução Local (Sem Containers)

Requer Python 3.10 ou superior.

```bash
cd pta-server
python main.py
```

---

## 7. Validação e Testes Automatizados

Com o servidor em execução na porta configurada (padrão 11550), execute as ferramentas de validação disponíveis na raiz do projeto:

### Teste Oficial do Professor (Critérios Básicos)
```bash
python pta-client.py 127.0.0.1 11550 user1
```
Valida os 6 critérios originais e o encerramento ordenado (`Points: 6/6`).

### Suíte Exaustiva de Testes (19 Cenários de Borda)
```bash
python comprehensive_tests.py
```
Testa isolamento concorrente, segurança contra Directory Traversal (`../`), sensibilidade a maiúsculas/minúsculas no nome, `SEQ_NUM` inicial arbitrário e robustez da máquina de estados.
