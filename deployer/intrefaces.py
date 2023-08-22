from typing import Optional
from abc import ABC, abstractmethod


class DeployerInterface(ABC):
    """A basic deployer component must has at lease two methods: restart and rel
    oad. The former one is used to fully restart the application and the later o
    ne is used to restart under test microservices only."""

    @abstractmethod
    def restart(self, application: str, port: int) -> None:
        """Restart the whole application."""

    @abstractmethod
    def reload(self, replicas: Optional[dict[str, int]] = None) -> None:
        """Reload only under test microservices."""
