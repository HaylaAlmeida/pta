import json
import logging
import sys
from infra.config.settings import config
from infra.storage.filesystem import FileSystemStorage
from infra.network.tcp_server import TcpServer


class JsonFormatter(logging.Formatter):
    """Formatador de log estruturado em JSON para observabilidade Cloud-Native."""
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging():
    log_level = getattr(logging, config.log_level, logging.INFO)
    handler = logging.StreamHandler(sys.stdout)

    if config.log_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S"
        ))

    logging.basicConfig(level=log_level, handlers=[handler], force=True)


def main():
    setup_logging()
    logger = logging.getLogger("PTA-Main")
    logger.info("Inicializando PTA Server")

    try:
        storage = FileSystemStorage(
            users_file=config.users_file,
            files_dir=config.files_dir
        )
        server = TcpServer(
            host=config.host,
            port=config.port,
            buffer_size=config.buffer_size,
            storage=storage,
            max_workers=config.max_workers,
            socket_timeout=config.socket_timeout,
            backlog=config.backlog,
            max_message_size=config.max_message_size,
            encoding=config.encoding
        )
        server.start()
    except KeyboardInterrupt:
        logger.info("Servidor finalizado pelo usuário.")
        sys.exit(0)
    except Exception as e:
        logger.critical("Erro fatal no servidor: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
