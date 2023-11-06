from .jaeger_trace_collector import JaegerTraceCollector
from .prom_hardware_collector import PromHardwareCollector
from .wrk_throughput_collector import WrkThroughputCollector
from dataclasses import dataclass
from .models import TestCaseData
from .interfaces import DataCollectorInterface
from ..utils.logger import log
from ..utils.files import append_csv_to_file, create_folder
import traceback, multiprocessing
import pandas as pd


@dataclass
class TraceData:
    raw_data: pd.DataFrame
    statistical_data: pd.DataFrame
    end_to_end_data: pd.DataFrame


@dataclass
class ToBeSavedData:
    data: pd.DataFrame
    path: str


def try_except(operation_name: str):
    """
    A decorator that wraps a function with a try-except block.

    Parameters:
    - operation_name (str): The name of the operation being performed.

    Returns:
    - The decorated function.
    """

    def inner(func):
        def wrapper(self: "BaseDataCollector", *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except:
                message = f"{self.test_case_data.name} {operation_name} failed!"
                log.error(message, to_file=True)
                traceback.print_exc()

        return wrapper

    return inner


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

    @try_except("throughput collection")
    def collect_throughput(self, test_case_data: TestCaseData) -> pd.DataFrame:
        """
        Collects throughput data for a given test case.

        Args:
            test_case_data (TestCaseData): The test case data object.

        Returns:
            pd.DataFrame: A DataFrame containing the collected throughput data.
        """
        throughput_data = self.throughput_collector.collect(test_case_data.name)
        throughput_data = pd.DataFrame([{"real_throughput": throughput_data}])
        return throughput_data

    @try_except("trace collection")
    def collect_traces(self, test_case_data: TestCaseData) -> TraceData:
        """
        Collects traces for the given test case data.

        Args:
            test_case_data (TestCaseData): The test case data containing the start time,
                end time, and operation.

        Returns:
            TraceData: The collected trace data, including raw data, statistical data,
                and end-to-end data.
        """
        trace_data = self.trace_collector.collect_trace(
            test_case_data.start_time,
            test_case_data.end_time,
            test_case_data.operation,
        )
        statistical_data, raw_data = self.trace_collector.process_trace(trace_data)
        end_to_end_data = self.trace_collector.end_to_end_data(raw_data)
        return TraceData(raw_data, statistical_data, end_to_end_data)

    def collect_cpu(
        self, test_case_data: TestCaseData, statistical_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Collects CPU usage data for each microservice within a given time frame.

        Args:
            test_case_data (TestCaseData): The test case data containing the start and end time.
            statistical_data (pd.DataFrame): The statistical data containing the microservices.

        Returns:
            pd.DataFrame: The CPU usage data for each microservice.
        """
        microservices = statistical_data["microservice"].dropna().unique().tolist()
        cpu_data = (
            self.hardware_collector.collect_cpu_usage(
                microservices, test_case_data.start_time, test_case_data.end_time
            )
            .to_pandas()
            .rename(columns={"usage": "cpu_usage"})
        )
        return cpu_data

    def collect_mem(
        self, test_case_data: TestCaseData, statistical_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Collects memory usage data for a given test case and statistical data.

        Args:
            test_case_data (TestCaseData): The test case data containing the start and end times.
            statistical_data (pd.DataFrame): The statistical data containing the microservices.

        Returns:
            pd.DataFrame: The memory usage data for the specified microservices.
        """
        microservices = statistical_data["microservice"].dropna().unique().tolist()
        mem_data = (
            self.hardware_collector.collect_mem_usage(
                microservices, test_case_data.start_time, test_case_data.end_time
            )
            .to_pandas()
            .rename(columns={"usage": "mem_usage"})
        )
        return mem_data

    @try_except("hardware resource collection")
    def collect_hardware(
        self, test_case_data: TestCaseData, statistical_data: pd.DataFrame
    ) -> pd.DataFrame:
        cpu_data = self.collect_cpu(test_case_data, statistical_data)
        mem_data = self.collect_mem(test_case_data, statistical_data)
        hardware_data = cpu_data.merge(mem_data)
        return hardware_data

    @try_except("save data")
    def append_additional_and_save(
        self, data_list: list[ToBeSavedData], additional_columns: dict
    ) -> bool:
        for data in data_list:
            if additional_columns is not None:
                append_csv_to_file(data.path, data.data.assign(**additional_columns))
            else:
                append_csv_to_file(data.path, data.data)
        return True

    def collect(self, test_case_data: TestCaseData) -> None:
        """Collect throughput, traces and hardware resource usage data and save
        them into files.

        Args:
            test_data (TestCaseData): Test case related data.
        """
        self.test_case_data = test_case_data

        throughput_data = self.collect_throughput(test_case_data)
        if throughput_data is None:
            return
        
        trace_data = self.collect_traces(test_case_data)
        if trace_data is None:
            return

        raw_data = trace_data.raw_data
        statistical_data = trace_data.statistical_data
        end_to_end_data = trace_data.end_to_end_data

        hardware_data = self.collect_hardware(test_case_data, statistical_data)
        if hardware_data is None:
            return

        data_list = [
            ToBeSavedData(statistical_data, f"{self.data_path}/statistical_data.csv"),
            ToBeSavedData(raw_data, f"{self.data_path}/raw_data.csv"),
            ToBeSavedData(hardware_data, f"{self.data_path}/hardware_data.csv"),
            ToBeSavedData(throughput_data, f"{self.data_path}/throughput_data.csv"),
            ToBeSavedData(end_to_end_data, f"{self.data_path}/end_to_end_data.csv"),
        ]
        result = self.append_additional_and_save(data_list, test_case_data.additional_columns)
        if result is None:
            return
        log.key(f"Data collection of {test_case_data.name} success!")

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
