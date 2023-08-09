from abc import ABC, abstractmethod
from typing import Any


class WorkloadGeneratorInterface(ABC):
    @abstractmethod
    def run(self, workload) -> Any:
        """Start workload generator and return results"""
