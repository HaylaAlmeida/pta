from abc import ABC, abstractmethod
from typing import Set, Tuple


class StorageRepository(ABC):
    """Interface (Port) para operações de leitura de usuários e arquivos."""

    @abstractmethod
    def get_allowed_users(self) -> Set[str]:
        """Recupera o conjunto de usuários autorizados."""
        pass

    @abstractmethod
    def list_files(self) -> Tuple[int, str]:
        """Retorna o total de arquivos e os nomes separados por vírgula."""
        pass

    @abstractmethod
    def read_file(self, filename: str) -> bytes:
        """Lê os bytes de um arquivo. Lança exceção se não encontrado ou inválido."""
        pass

