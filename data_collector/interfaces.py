from abc import ABC, abstractmethod
from .models import CpuUsage, MemUsage, TestCaseData
import pandas as pd


class HardwareCollectorInterface(ABC):
    """Hardware collector interface, will return usage records."""

    @abstractmethod
    def collect_cpu_usage(
        self, microservices: list[str], start_time: float, end_time: float
    ) -> CpuUsage:
        """Collect CPU usage, range: 0 - 1."""

    @abstractmethod
    def collect_mem_usage(
        self, microservices: list[str], start_time: float, end_time: float
    ) -> MemUsage:
        """Collect memory usage, range: 0 - 1."""


class ThroughputCollectorInterface(ABC):
    """Throughput collector interface, will return workload throughput."""

    @abstractmethod
    def collect(self, test_case_name: str) -> float:
        """Collect and return throughput."""


class TraceCollectorInterface(ABC):
    """Abstract interface of trace collector. The collector should have two abil
    ities: collect trace data with ``collect_trace`` method and process them wit
    h ``process_trace`` method.
    """

    @abstractmethod
    def collect_trace(
        self,
        start_time: float,
        end_time: float,
        operation: str = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Collect trace data. And parse them into Dataframe object."""

    @abstractmethod
    def process_trace(
        self, collected_data: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Process collected data, return statistical and original data in a tup
        le. The first item of tuple is statistical data, and the second one is r
        aw data.
        """


class DataCollectorInterface(ABC):
    """Data collector interface, all sub-class need to support methods listed be
    low."""

    @abstractmethod
    def collect(self, test_case_data: TestCaseData) -> None:
        """Collect data and saved them to files."""

    @abstractmethod
    def collect_async(self, test_case_data: TestCaseData) -> None:
        """Using multiprocess to speed up data collection."""

    @abstractmethod
    def wait(self) -> None:
        """Wait until all async data collection processes done."""
