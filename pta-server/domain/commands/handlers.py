from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from domain.models import RequestMessage, ResponseMessage
from domain.commands.base import CommandHandler

if TYPE_CHECKING:
    from domain.state_machine import SessionContext

logger = logging.getLogger("PTA-Commands")


class ListCommandHandler(CommandHandler):
    """Trata o comando LIST: retorna quantidade e relação de arquivos."""

    def execute(self, request: RequestMessage, context: SessionContext) -> ResponseMessage:
        if request.args:
            return ResponseMessage(
                seq_num=request.seq_num,
                payload=f"{request.seq_num} NOK".encode("ascii"),
                should_close_connection=False
            )

        try:
            total, files = context.storage.list_files()
            payload = f"{request.seq_num} ARQS {total} {files}".encode("ascii")
            return ResponseMessage(
                seq_num=request.seq_num,
                payload=payload,
                should_close_connection=False
            )
        except Exception as e:
            logger.error("Falha ao listar arquivos: %s", e)
            return ResponseMessage(
                seq_num=request.seq_num,
                payload=f"{request.seq_num} NOK".encode("ascii"),
                should_close_connection=False
            )


class PegaCommandHandler(CommandHandler):
    """Trata o comando PEGA: envia o tamanho e os bytes do arquivo solicitado."""

    def execute(self, request: RequestMessage, context: SessionContext) -> ResponseMessage:
        filename = request.args.strip()
        if not filename or " " in filename:
            return ResponseMessage(
                seq_num=request.seq_num,
                payload=f"{request.seq_num} NOK".encode("ascii"),
                should_close_connection=False
            )

        try:
            file_bytes = context.storage.read_file(filename)
            header = f"{request.seq_num} ARQ {len(file_bytes)} ".encode("ascii")
            return ResponseMessage(
                seq_num=request.seq_num,
                payload=header + file_bytes,
                should_close_connection=False
            )
        except Exception as e:
            logger.warning("Falha ao transferir arquivo '%s': %s", filename, e)
            return ResponseMessage(
                seq_num=request.seq_num,
                payload=f"{request.seq_num} NOK".encode("ascii"),
                should_close_connection=False
            )


class TermCommandHandler(CommandHandler):
    """Trata o comando TERM: finaliza a sessão ordenadamente com OK e encerra TCP."""

    def execute(self, request: RequestMessage, context: SessionContext) -> ResponseMessage:
        if request.args:
            return ResponseMessage(
                seq_num=request.seq_num,
                payload=f"{request.seq_num} NOK".encode("ascii"),
                should_close_connection=False
            )

        logger.info("Comando TERM recebido. Encerrando sessão.")
        from domain.states.waiting import WaitingState
        context.transition_to(WaitingState())

        return ResponseMessage(
            seq_num=request.seq_num,
            payload=f"{request.seq_num} OK".encode("ascii"),
            should_close_connection=True
        )
