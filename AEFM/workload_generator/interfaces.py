from abc import ABC, abstractmethod
from typing import Any


class WorkloadGeneratorInterface(ABC):
    @abstractmethod
    def run(self, workload: int, test_case_name: str) -> Any:
        """Start workload generator and return results"""