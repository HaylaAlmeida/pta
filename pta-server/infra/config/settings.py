import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Configurações da aplicação fornecidas pelo ambiente ou padrões seguros."""
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    users_file: Path = Path(os.getenv("PTA_USERS_FILE", str(Path(__file__).resolve().parent.parent.parent / "users.txt"))).resolve()
    files_dir: Path = Path(os.getenv("PTA_FILES_DIR", str(Path(__file__).resolve().parent.parent.parent / "files"))).resolve()

    # Rede e Protocolo
    host: str = os.getenv("PTA_HOST", "0.0.0.0")
    port: int = int(os.getenv("PTA_PORT", "11550"))
    buffer_size: int = int(os.getenv("PTA_BUFFER_SIZE", "2048"))
    backlog: int = int(os.getenv("PTA_BACKLOG", "128"))
    max_message_size: int = int(os.getenv("PTA_MAX_MESSAGE_SIZE", "65536"))
    encoding: str = os.getenv("PTA_ENCODING", "ascii")

    # Controles de Concorrência e Resiliência
    max_workers: int = int(os.getenv("PTA_MAX_WORKERS", "10"))
    socket_timeout: float = float(os.getenv("PTA_SOCKET_TIMEOUT", "30.0"))

    # Observabilidade
    log_level: str = os.getenv("PTA_LOG_LEVEL", "INFO").upper()
    log_json: bool = os.getenv("PTA_LOG_JSON", "false").lower() in ("true", "1", "yes")

config = AppConfig()
