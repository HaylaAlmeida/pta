from typing import Tuple, Set
from domain.state_machine import SessionContext
from domain.repositories import StorageRepository
from application.parser import MessageParser


class ProtocolApplicationService:
    """Caso de uso de orquestração do protocolo PTA para cada conexão de cliente."""

    def __init__(self, allowed_users: Set[str], storage: StorageRepository):
        self.session_context = SessionContext(allowed_users=allowed_users, storage=storage)

    def process_raw_input(self, raw_message: str) -> Tuple[bytes, bool]:
        """
        Recebe a mensagem de entrada em texto, faz o parse e delega para o SessionContext.
        Retorna: (payload_bytes, fechar_conexao)
        """
        request = MessageParser.parse(raw_message)
        response = self.session_context.handle(request)
        return response.payload, response.should_close_connection
