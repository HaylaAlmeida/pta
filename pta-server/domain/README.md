# Camada de Domínio (Domain Layer)

A Camada de Domínio contém as regras de negócio centrais, entidades e a Máquina de Estados Finita (FSM) que governa o Protocolo de Transferência de Arquivos (PTA).

Esta camada é completamente independente de bibliotecas externas, frameworks, mecanismos de rede ou sistemas de arquivos concretos.

---

## Estrutura de Módulos

```text
domain/
├── models.py          # Enums fundamentais e DTOs de dados imutáveis
├── repositories.py    # Contrato abstrato (Port) para armazenamento
├── state_machine.py   # Contexto da sessão (SessionContext) e orquestração da FSM
├── states/            # Implementação do State Pattern
│   ├── base.py        # Interface abstrata ProtocolState
│   ├── waiting.py     # Estado ESPERANDO (apenas CUMP permitido)
│   └── ready.py       # Estado PRONTO (despacho de LIST, PEGA, TERM)
└── commands/          # Implementação do Command Pattern
    ├── base.py        # Interface abstrata CommandHandler
    └── handlers.py    # Handlers específicos para LIST, PEGA e TERM
```

---

## Decisões de Arquitetura e Padrões

### 1. State Pattern (GoF)
- **Motivação:** O documento de especificação `pta.pdf` define uma máquina de estados explícita entre os estados ESPERANDO e PRONTO. O padrão State substitui condicionais complexas e espalhadas por classes polimórficas bem definidas.
- **Funcionamento:**
  - `WaitingState`: Aceita somente `CUMP <usuario>`. Caso o comando seja outro ou o usuário seja inválido, emite `NOK` e sinaliza o encerramento do socket TCP. Após autenticação bem-sucedida, realiza a transição: `context.transition_to(ReadyState())`.
  - `ReadyState`: Aceita comandos operacionais (`LIST`, `PEGA`, `TERM`). Se um comando inválido for enviado neste estado, emite `NOK` mantendo a conexão TCP aberta, conforme exigido pela especificação.

### 2. Command Pattern (GoF)
- **Motivação:** Isolar o algoritmo de cada operação em classes independentes com responsabilidade única (Single Responsibility Principle).
- **Funcionamento:**
  - `ListCommandHandler`: Consulta o repositório e monta a resposta `SEQ_NUM ARQS <total> <arquivos>`.
  - `PegaCommandHandler`: Lê o arquivo binário e monta a resposta `SEQ_NUM ARQ <tamanho> <bytes>`.
  - `TermCommandHandler`: Transiciona de volta para `WaitingState` e sinaliza o fechamento da conexão TCP com `SEQ_NUM OK`.

### 3. Inversão de Dependência (DIP)
- O arquivo `repositories.py` define a interface `StorageRepository`. O domínio não acessa o disco diretamente; ele apenas interage com essa abstração. A implementação real fica a cargo da camada de infraestrutura.

### 4. Imutabilidade
- Em `models.py`, `RequestMessage` e `ResponseMessage` são declaradas como dataclasses imutáveis (`frozen=True`), assegurando que mensagens não sofram mutação inesperada durante o processamento.
