from .jaeger_trace_collector import JaegerTraceCollector
from .prom_hardware_collector import PromHardwareCollector
from .wrk_throughput_collector import WrkThroughputCollector
from .models import TestCaseData
from .interfaces import DataCollectorInterface
from ..utils.logger import log
from ..utils.files import append_csv_to_file, create_folder
import traceback, multiprocessing
import pandas as pd


class BaseDataCollector(DataCollectorInterface):
    """A default data collector that collects data based on jaeger, prometheus a
    nd wrk."""

    def __init__(
        self,
        data_path: str,
        trace_collector: JaegerTraceCollector,
        hardware_collector: PromHardwareCollector,
        throughput_collector: WrkThroughputCollector,
        max_processes: int = 10,
    ) -> None:
        """A default data collector that collects data based on jaeger, promethe
        us and wrk.

        Args:
            data_path (str): Where to save data files.
            trace_collector (JaegerTraceCollector): Used to collect traces.
            hardware_collector (PromHardwareCollector): Used to collect hardware
            usage.
            throughput_collector (WrkThroughputCollector): Used to collect throu
            ghput.
            max_processes (int): Maximum processes used when collecting data und
            er async mode. Defaults to 10.
        """
        self.data_path = data_path
        create_folder(data_path)
        self.trace_collector = trace_collector
        self.hardware_collector = hardware_collector
        self.throughput_collector = throughput_collector
        self.max_processes = max_processes
        self.proc_pool = None

    def collect_async(self, test_case_data: TestCaseData) -> None:
        """Collect throughput asynchronously, traces and hardware resource usage
        data and save them into files.

        Args:
            test_case_data (TestCaseData): _description_
        """
        if self.proc_pool is None:
            self.proc_pool = multiprocessing.Pool(self.max_processes)
        self.proc_pool.apply_async(self.collect, (test_case_data,))

    def collect(self, test_case_data: TestCaseData) -> None:
        """Collect throughput, traces and hardware resource usage data and save
        them into files.

        Args:
            test_data (TestCaseData): Test case related data.
        """
        try:
            throughput_data = self.throughput_collector.collect(test_case_data.name)
            throughput_data = pd.DataFrame([{"real_throughput": throughput_data}])
        except:
            log.error(
                f"{test_case_data.name} throughput collection failed!", to_file=True
            )
            traceback.print_exc()
            return

        try:
            trace_data = self.trace_collector.collect_trace(
                test_case_data.start_time,
                test_case_data.end_time,
                test_case_data.operation,
            )
            statistical_data, raw_data = self.trace_collector.process_trace(trace_data)
        except:
            log.error(f"{test_case_data.name} trace collection failed!", to_file=True)
            traceback.print_exc()
            return

        try:
            microservices = statistical_data["microservice"].dropna().unique().tolist()
            cpu_data = (
                self.hardware_collector.collect_cpu_usage(
                    microservices, test_case_data.start_time, test_case_data.end_time
                )
                .to_pandas()
                .rename(columns={"usage": "cpu_usage"})
            )
            mem_data = (
                self.hardware_collector.collect_mem_usage(
                    microservices, test_case_data.start_time, test_case_data.end_time
                )
                .to_pandas()
                .rename(columns={"usage": "mem_usage"})
            )
            hardware_data = cpu_data.merge(mem_data)
        except:
            log.error(
                f"{test_case_data.name} hardware resource collection failed!",
                to_file=True,
            )
            traceback.print_exc()
            return

        try:
            if test_case_data.additional_columns is not None:
                statistical_data = statistical_data.assign(
                    **test_case_data.additional_columns
                )
                raw_data = raw_data.assign(**test_case_data.additional_columns)
                hardware_data = hardware_data.assign(
                    **test_case_data.additional_columns
                )
                throughput_data = throughput_data.assign(
                    **test_case_data.additional_columns
                )
            append_csv_to_file(
                f"{self.data_path}/statistical_data.csv", statistical_data
            )
            append_csv_to_file(f"{self.data_path}/raw_data.csv", raw_data)
            append_csv_to_file(f"{self.data_path}/hardware_data.csv", hardware_data)
            append_csv_to_file(f"{self.data_path}/throughput_data.csv", throughput_data)

        except:
            log.error(f"{test_case_data.name} data save failed!", to_file=True)
            traceback.print_exc()
        log.info(f"Data collection of {test_case_data.name} success!")

    def wait(self) -> None:
        """Wait until all async data collection processes done."""
        if self.proc_pool is not None:
            self.proc_pool.close()
            self.proc_pool.join()
        self.proc_pool = multiprocessing.Pool(self.max_processes)

    def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict["proc_pool"]
        return self_dict

    def __setstate__(self, state):
        self.__dict__.update(state)
