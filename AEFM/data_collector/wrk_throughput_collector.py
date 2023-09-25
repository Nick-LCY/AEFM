from ..utils.logger import log
from .interfaces import ThroughputCollectorInterface


class WrkFetcher:
    """Middleware to collect throughput from wrk."""

    def __init__(self, output_path: str) -> None:
        """Middleware to collect throughput from wrk.

        Args:
            output_path (str): Out put path that defined in wrk workload generat
            or.
        """
        self.throughput_path = f"{output_path}/throughput"

    def fetch(self, test_case_name: str) -> float:
        """Read wrk output file and get throughput.

        Args:
            test_case_name (str): Current test case name, used to identify wrk f
            ile.

        Returns:
            float: Throughput, unit: requests/second.
        """
        with open(f"{self.throughput_path}/{test_case_name}", "r") as file:
            throughput = float(file.readline())
        return throughput


class WrkThroughputCollector(ThroughputCollectorInterface):
    """Throughput collector that based on wrk."""

    def __init__(self, wrk_fetcher: WrkFetcher) -> None:
        """Throughput collector that based on wrk.

        Args:
            wrk_fetcher (WrkFetcher): Middle ware that collects data from wrk.
        """
        self.fetcher = wrk_fetcher

    def collect(self, test_case_name: str) -> float:
        """Collect and return throughput

        Args:
            test_case_name (str): Current test case name, used to identify wrk f
            ile.

        Returns:
            float: Throughput, unit: requests/second.
        """
        throughput = self.fetcher.fetch(test_case_name)
        log.debug(f"{__file__}: Real throughput: {throughput}")
        return throughput
