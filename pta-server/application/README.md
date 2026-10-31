# Camada de Aplicação (Application Layer)

A Camada de Aplicação é responsável por orquestrar os casos de uso do protocolo PTA e mediar a comunicação entre as camadas externas de entrada e o núcleo de Domínio.

---

## Estrutura de Módulos

```text
application/
├── parser.py    # Deserializador de texto em modelos estruturados de domínio
└── service.py   # ProtocolApplicationService (Caso de uso de sessão)
```

---

## Decisões de Arquitetura

### 1. MessageParser (`parser.py`)
- **Responsabilidade:** Converter o stream de texto bruto recebido do socket TCP no objeto de domínio `RequestMessage`.
- **Validações Realizadas:**
  - Separação dos campos do protocolo delimitados por espaço (`SEQ_NUM COMMAND ARGS`).
  - Validação da integridade numérica do `SEQ_NUM`.
  - Mapeamento seguro do comando textual para o enum tipado `CommandType`.
  - Isolamento de erros de sintaxe antes que a requisição atinja as entidades de domínio.

### 2. ProtocolApplicationService (`service.py`)
- **Responsabilidade:** Representar o caso de uso completo de atendimento de uma sessão de cliente PTA.
- **Ciclo de Execução:**
  1. Recebe a mensagem em texto cru do adaptador de rede.
  2. Aciona o `MessageParser` para obter a `RequestMessage`.
  3. Encaminha a requisição para a máquina de estados de domínio (`SessionContext`).
  4. Retorna a tupla contendo o payload em bytes a ser transmitido e a instrução sobre encerrar ou manter a conexão TCP.
- **Independência de Transporte:** Este serviço não possui vínculo com sockets de rede. Ele pode ser executado em testes unitários passando strings diretamente e inspecionando os bytes de retorno.
