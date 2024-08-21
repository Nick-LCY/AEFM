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
from typing import Callable, Iterable


@dataclass
class ToBeSavedData:
    data: pd.DataFrame
    path: str


@dataclass
class Collection:
    name: str
    saved_path: str
    method: Callable[..., pd.DataFrame]
    args: Iterable | None = None


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
        self.to_be_collected: list[Collection] = []
        # Init default collections
        throughput_collection = Collection(
            "throughput collection",
            f"{self.data_path}/throughput_data.csv",
            self.collect_throughput,
        )
        raw_data_collection = Collection(
            "raw data collection",
            f"{self.data_path}/raw_data.csv",
            self.collect_raw_data,
        )
        statistical_data_collection = Collection(
            "statistical data collection",
            f"{self.data_path}/statistical_data.csv",
            self.collect_statistical_data,
        )
        end_to_end_data_collection = Collection(
            "end to end data collection",
            f"{self.data_path}/end_to_end_data.csv",
            self.collect_end_to_end_data,
        )
        hradware_collection = Collection(
            "hardware resource collection",
            f"{self.data_path}/hardware_data.csv",
            self.collect_hardware,
        )
        self.add_new_collections(
            [
                throughput_collection,
                raw_data_collection,
                statistical_data_collection,
                end_to_end_data_collection,
                hradware_collection,
            ]
        )

    def collect_async(self, test_case_data: TestCaseData) -> None:
        """Collect throughput asynchronously, traces and hardware resource usage
        data and save them into files.

        Args:
            test_case_data (TestCaseData): _description_
        """
        if self.proc_pool is None:
            self.proc_pool = multiprocessing.Pool(self.max_processes)
        self.proc_pool.apply_async(self.collect, (test_case_data,))

    def collect_throughput(self) -> pd.DataFrame:
        """
        Collects throughput data for a given test case.

        Returns:
            pd.DataFrame: A DataFrame containing the collected throughput data.
        """
        throughput_data = self.throughput_collector.collect(self.test_case_data.name)
        throughput_data = pd.DataFrame([{"real_throughput": throughput_data}])
        return throughput_data

    def collect_raw_data(self) -> pd.DataFrame:
        trace_data = self.trace_collector.collect_trace(
            self.test_case_data.start_time,
            self.test_case_data.end_time,
            self.test_case_data.operation,
        )
        raw_data = self.trace_collector.to_raw_data(trace_data)
        self.raw_data = raw_data
        return raw_data

    def collect_statistical_data(self) -> pd.DataFrame:
        statistical_data = self.trace_collector.to_statistical_data(self.raw_data)
        self.statistical_data = statistical_data
        return statistical_data

    def collect_end_to_end_data(self) -> pd.DataFrame:
        end_to_end_data = self.trace_collector.to_end_to_end_data(self.raw_data)
        return end_to_end_data

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

    def collect_hardware(self) -> pd.DataFrame:
        cpu_data = self.collect_cpu(self.test_case_data, self.statistical_data)
        mem_data = self.collect_mem(self.test_case_data, self.statistical_data)
        hardware_data = cpu_data.merge(mem_data)
        return hardware_data

    def append_additional_and_save(
        self, data_list: list[ToBeSavedData], additional_columns: dict
    ) -> bool:
        for data in data_list:
            if additional_columns is not None:
                append_csv_to_file(data.path, data.data.assign(**additional_columns))
            else:
                append_csv_to_file(data.path, data.data)
        return True

    def add_new_collections(self, collections: Collection | list[Collection]):
        """Append a new collection to the end of `to_be_collected`. Data collect
        or will invoke `Collection.method`, and save its returned value to `Coll
        ection.saved_path`.

        Args:
            collections (Collection | list[Collection]): A Collection object or
            a list of Collection objects.
        """
        if isinstance(collections, list):
            for collection in collections:
                self.to_be_collected.append(collection)
        else:
            self.to_be_collected.append(collections)

    def collect(self, test_case_data: TestCaseData) -> None:
        """Invoke data collection method that in self.to_be_collected and save t
        hem to the given path. To check how to add new data collection method, c
        heck "add_new_collections" method.

        Args:
            test_data (TestCaseData): Test case related data.
        """
        self.test_case_data = test_case_data
        data_list = []
        for collection in self.to_be_collected:
            args = collection.args
            if args is None:
                args = []
            try:
                data = collection.method(*args)
            except:
                message = f"{test_case_data.name} {collection.name} failed!"
                log.error(message, to_file=True)
                traceback.print_exc()
                continue
            data_list.append(ToBeSavedData(data, collection.saved_path))
        try:
            self.append_additional_and_save(
                data_list, test_case_data.additional_columns
            )
        except:
            message = f"{test_case_data.name} save data failed!"
            log.error(message, to_file=True)
            traceback.print_exc()

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
