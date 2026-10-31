import logging
from pathlib import Path
from typing import Set, Tuple
from domain.repositories import StorageRepository

logger = logging.getLogger("PTA-FileSystemStorage")


class FileSystemStorage(StorageRepository):
    """Implementação de infraestrutura do StorageRepository baseado no sistema de arquivos local."""

    def __init__(self, users_file: Path, files_dir: Path):
        self.users_file = users_file
        self.files_dir = files_dir

    def get_allowed_users(self) -> Set[str]:
        """Carrega usuários do arquivo users.txt."""
        if not self.users_file.exists():
            logger.warning("Arquivo de usuários '%s' não encontrado.", self.users_file)
            return set()

        with open(self.users_file, "r", encoding="utf-8") as f:
            users = {line.strip() for line in f if line.strip()}
        logger.info("Usuários autorizados carregados: %s", ", ".join(users))
        return users

    def list_files(self) -> Tuple[int, str]:
        """Lista os arquivos no diretório files/."""
        if not self.files_dir.exists() or not self.files_dir.is_dir():
            raise FileNotFoundError(f"Diretório {self.files_dir} inexistente.")

        file_names = sorted([f.name for f in self.files_dir.iterdir() if f.is_file()])
        return len(file_names), ",".join(file_names)

    def read_file(self, filename: str) -> bytes:
        """Lê os bytes de um arquivo com proteção contra Directory Traversal."""
        target_path = (self.files_dir / filename).resolve()
        files_dir_resolved = self.files_dir.resolve()

        if files_dir_resolved not in target_path.parents and target_path != files_dir_resolved:
            raise PermissionError("Acesso não autorizado fora do diretório de arquivos.")

        if not target_path.is_file():
            raise FileNotFoundError(f"Arquivo '{filename}' não encontrado.")

        return target_path.read_bytes()

