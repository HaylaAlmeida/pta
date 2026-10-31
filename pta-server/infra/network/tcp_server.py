import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Set
from domain.repositories import StorageRepository
from application.service import ProtocolApplicationService

logger = logging.getLogger("PTA-TcpServer")


class TcpServer:
    """
    Servidor TCP com pool de threads controlado (ThreadPoolExecutor).
    Limita o número máximo de conexões simultâneas, aplica timeout por socket,
    restringe tamanho máximo de mensagens e gerencia a fila de backlog do SO.
    """

    def __init__(
        self,
        host: str,
        port: int,
        buffer_size: int,
        storage: StorageRepository,
        max_workers: int = 10,
        socket_timeout: float = 30.0,
        backlog: int = 128,
        max_message_size: int = 65536,
        encoding: str = "ascii"
    ):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.storage = storage
        self.max_workers = max_workers
        self.socket_timeout = socket_timeout
        self.backlog = backlog
        self.max_message_size = max_message_size
        self.encoding = encoding
        self.allowed_users: Set[str] = self.storage.get_allowed_users()

    def start(self):
        """Inicia a escuta no socket TCP utilizando ThreadPoolExecutor limitado."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.host, self.port))
            server_sock.listen(self.backlog)
            logger.info(
                "TCP Server ouvindo em %s:%d (Pool: max %d workers, Backlog: %d)",
                self.host, self.port, self.max_workers, self.backlog
            )

            with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="PTA-Worker") as pool:
                while True:
                    client_sock, client_addr = server_sock.accept()
                    logger.info("Conexão aceita de %s:%d", *client_addr)

                    pool.submit(self._client_worker, client_sock, client_addr)

    def _client_worker(self, client_sock: socket.socket, client_addr):
        """Executa a rotina de atendimento com timeout de inatividade e encerramento garantido."""
        client_sock.settimeout(self.socket_timeout)

        try:
            self._handle_client(client_sock)
        except socket.timeout:
            logger.warning("Conexão com %s:%d expirou por inatividade (timeout de %.1fs).", *client_addr, self.socket_timeout)
        except Exception as e:
            logger.error("Erro durante atendimento do cliente %s: %s", client_addr, e)
        finally:
            try:
                client_sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            client_sock.close()
            logger.info("Conexão encerrada com %s:%d", *client_addr)

    def _handle_client(self, client_sock: socket.socket):
        """Gerencia o ciclo de vida do cliente conectado com limite de buffer de mensagem."""
        app_service = ProtocolApplicationService(
            allowed_users=self.allowed_users,
            storage=self.storage
        )

        buffer = ""
        while True:
            data = client_sock.recv(self.buffer_size)
            if not data:
                break

            # Proteção contra ataque de exaustão de memória (Buffer Flood / OOM)
            if len(buffer) + len(data) > self.max_message_size:
                logger.warning("Mensagem de cliente excedeu o limite máximo de %d bytes. Rejeitando.", self.max_message_size)
                client_sock.sendall(b"-1 NOK")
                break

            buffer += data.decode(self.encoding, errors="replace")
            message = buffer.strip()
            buffer = ""

            if not message:
                continue

            response_bytes, should_close = app_service.process_raw_input(message)
            client_sock.sendall(response_bytes)

            if should_close:
                break
