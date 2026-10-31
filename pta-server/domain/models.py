from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional


class SessionState(Enum):
    """Estados possíveis da sessão de um cliente no protocolo PTA."""
    WAITING = auto()
    READY = auto()


class CommandType(Enum):
    """Comandos suportados pelo protocolo PTA."""
    CUMP = "CUMP"
    LIST = "LIST"
    PEGA = "PEGA"
    TERM = "TERM"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_string(cls, value: str) -> "CommandType":
        # Case-sensitive estrito: comandos em minúsculas (ex: 'list') são UNKNOWN
        try:
            return cls[value]
        except KeyError:
            return cls.UNKNOWN


@dataclass(frozen=True)
class RequestMessage:
    """Representa uma mensagem de pedido enviada pelo cliente."""
    seq_num: str
    command: CommandType
    raw_command: str
    args: str
    is_valid_format: bool


@dataclass(frozen=True)
class ResponseMessage:
    """Representa a resposta gerada para o cliente."""
    seq_num: str
    payload: bytes
    should_close_connection: bool
