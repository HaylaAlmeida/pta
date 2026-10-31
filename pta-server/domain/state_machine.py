import logging
from typing import Set
from domain.models import RequestMessage, ResponseMessage
from domain.repositories import StorageRepository
from domain.states.base import ProtocolState
from domain.states.waiting import WaitingState

logger = logging.getLogger("PTA-SessionContext")


class SessionContext:
    """Contexto da sessão do cliente que orquestra as transições de estado."""

    def __init__(self, allowed_users: Set[str], storage: StorageRepository):
        self.allowed_users = allowed_users
        self.storage = storage
        self._current_state: ProtocolState = WaitingState()

    @property
    def current_state(self) -> ProtocolState:
        return self._current_state

    def transition_to(self, new_state: ProtocolState):
        """Efetua a transição de estado na FSM."""
        logger.info(
            "Transição de estado: %s -> %s",
            self._current_state.__class__.__name__,
            new_state.__class__.__name__
        )
        self._current_state = new_state

    def handle(self, request: RequestMessage) -> ResponseMessage:
        """Processa a mensagem delegando o comportamento para o estado ativo."""
        if not request.is_valid_format:
            should_close = isinstance(self._current_state, WaitingState)
            return ResponseMessage(
                seq_num=request.seq_num,
                payload=f"{request.seq_num} NOK".encode("ascii"),
                should_close_connection=should_close
            )

        return self._current_state.handle(request, self)
