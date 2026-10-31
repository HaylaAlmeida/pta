from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
from domain.models import RequestMessage, ResponseMessage

if TYPE_CHECKING:
    from domain.state_machine import SessionContext


class CommandHandler(ABC):
    """Interface (Command Pattern) para execução de comandos do protocolo PTA."""

    @abstractmethod
    def execute(self, request: RequestMessage, context: SessionContext) -> ResponseMessage:
        """Executa a lógica de um comando específico."""
        pass
