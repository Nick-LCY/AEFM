from abc import ABC, abstractmethod
from models import Node


class InfGeneratorInterface(ABC):
    @abstractmethod
    def generate(self, count: int, nodes: list[Node], wait: bool) -> None:
        """Generate interference with certain amount."""

    @abstractmethod
    def clear(self, wait: bool) -> None:
        """Clear all generated interference."""
