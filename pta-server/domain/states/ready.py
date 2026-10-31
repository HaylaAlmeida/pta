from __future__ import annotations
from typing import TYPE_CHECKING, Dict
import logging
from domain.models import CommandType, RequestMessage, ResponseMessage
from domain.states.base import ProtocolState
from domain.commands.base import CommandHandler
from domain.commands.handlers import (
    ListCommandHandler,
    PegaCommandHandler,
    TermCommandHandler
)

if TYPE_CHECKING:
    from domain.state_machine import SessionContext

logger = logging.getLogger("PTA-ReadyState")


class ReadyState(ProtocolState):
    """Estado 'PRONTO' da especificação: despacha comandos LIST, PEGA e TERM."""

    def __init__(self):
        self._commands: Dict[CommandType, CommandHandler] = {
            CommandType.LIST: ListCommandHandler(),
            CommandType.PEGA: PegaCommandHandler(),
            CommandType.TERM: TermCommandHandler()
        }

    def handle(self, request: RequestMessage, context: SessionContext) -> ResponseMessage:
        handler = self._commands.get(request.command)
        if not handler:
            logger.warning("Comando desconhecido ou não suportado no estado READY: %s", request.raw_command)
            return ResponseMessage(
                seq_num=request.seq_num,
                payload=f"{request.seq_num} NOK".encode("ascii"),
                should_close_connection=False
            )

        return handler.execute(request, context)
