from abc import ABC, abstractmethod
from ..models import Node


class InfGeneratorInterface(ABC):
    """Interference generator interface, need to have at least two methods: gene
    rate and clear."""

    @abstractmethod
    def generate(self, count: int, nodes: list[Node], wait: bool) -> None:
        """Generate interference with certain amount."""

    @abstractmethod
    def clear(self, wait: bool) -> None:
        """Clear all generated interference."""
