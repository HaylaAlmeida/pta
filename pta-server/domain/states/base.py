from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
from domain.models import RequestMessage, ResponseMessage

if TYPE_CHECKING:
    from domain.state_machine import SessionContext


class ProtocolState(ABC):
    """Interface base do State Pattern para o ciclo de vida da sessão."""

    @abstractmethod
    def handle(self, request: RequestMessage, context: SessionContext) -> ResponseMessage:
        """Processa a mensagem de acordo com as regras do estado atual."""
        pass
