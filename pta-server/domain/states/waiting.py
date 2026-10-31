from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from domain.models import CommandType, RequestMessage, ResponseMessage
from domain.states.base import ProtocolState

if TYPE_CHECKING:
    from domain.state_machine import SessionContext

logger = logging.getLogger("PTA-WaitingState")


class WaitingState(ProtocolState):
    """Estado 'ESPERANDO' da especificação: apenas CUMP com usuário válido é permitido."""

    def handle(self, request: RequestMessage, context: SessionContext) -> ResponseMessage:
        if request.command != CommandType.CUMP:
            logger.warning("Comando recebido em WAITING diferente de CUMP: %s", request.raw_command)
            return ResponseMessage(
                seq_num=request.seq_num,
                payload=f"{request.seq_num} NOK".encode("ascii"),
                should_close_connection=True
            )

        username = request.args.strip()
        if not username or " " in username or username not in context.allowed_users:
            logger.warning("Usuário inválido ou não autorizado em WAITING: '%s'", username)
            return ResponseMessage(
                seq_num=request.seq_num,
                payload=f"{request.seq_num} NOK".encode("ascii"),
                should_close_connection=True
            )

        logger.info("Usuário '%s' autenticado com sucesso.", username)
        from domain.states.ready import ReadyState
        context.transition_to(ReadyState())

        return ResponseMessage(
            seq_num=request.seq_num,
            payload=f"{request.seq_num} OK".encode("ascii"),
            should_close_connection=False
        )
