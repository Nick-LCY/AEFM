from abc import ABC, abstractmethod

from data_collector.models import MemUsage
from .models import CpuUsage, MemUsage
from utils.prom_fetcher import PromFetcher


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


class PromHardwareCollector(HardwareCollectorInterface):
    """Hardware collector that used prometheus as data source."""

    def __init__(self, fetcher: PromFetcher) -> None:
        """Hardware collector that used prometheus as data source.

        Args:
            fetcher (PromFetcher): Middleware that used to communicate with prom
            etheus.
        """
        self.fetcher = fetcher

    def collect_cpu_usage(
        self, microservices: list[str], start_time: float, end_time: float
    ) -> CpuUsage:
        """Collect CPU usage, range: 0 - 1.

        Args:
            microservices (list[str]): Microservices that need to be collected.
            start_time (float): Start time.
            end_time (float): End time.

        Returns:
            CpuUsage: CPU usage records.
        """    
        response = self.fetcher.fetch_cpu_usage(microservices, start_time, end_time)
        # todo: logger need to add log to file method
        # self.write_log(f"Fetch CPU usage from: {response.url}")
        usage = response.json()
        cpu_usage = CpuUsage()
        if usage["data"] and usage["data"]["result"]:
            for data in usage["data"]["result"]:
                pod = str(data["metric"]["pod"])
                microservice = "-".join(pod.split("-")[:-2])
                usage = max([float(v) for v in data["values"]])
                cpu_usage.set(microservice, pod, usage)
        return cpu_usage

    def collect_mem_usage(
        self, microservices: list[str], start_time: float, end_time: float
    ) -> MemUsage:
        """Collect memory usage, range: 0 - 1.

        Args:
            microservices (list[str]): Microservices that need to be collected.
            start_time (float): Start time.
            end_time (float): End time.

        Returns:
            CpuUsage: Memory usage records.
        """    
        response = self.fetcher.fetch_mem_usage(microservices, start_time, end_time)
        # todo: logger need to add log to file method
        # self.write_log(f"Fetch memory usage from: {response.url}")
        usage = response.json()
        mem_usage = MemUsage()
        if usage["data"] and usage["data"]["result"]:
            for data in usage["data"]["result"]:
                pod = str(data["metric"]["pod"])
                microservice = "-".join(pod.split("-")[:-2])
                usage = max([float(v) for v in data["values"]])
                mem_usage.set(microservice, pod, usage)
        return mem_usage
