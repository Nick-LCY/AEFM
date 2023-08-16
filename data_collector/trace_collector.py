from abc import ABC, abstractmethod
from utils.jaeger_fetcher import JaegerFetcher
import json
import pandas as pd
import utils.trace_processor as t_processor
from utils.logger import log


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


class JaegerTraceCollector(TraceCollectorInterface):
    """Jaeger-based trace collector."""

    def __init__(self, jaeger_fetcher: JaegerFetcher) -> None:
        """Jaeger-based trace collector.

        Args:
            jaeger_fetcher (JaegerFetcher): Jaeger fetcher that used to communic
            ate with jaeger.
        """
        self.fetcher = jaeger_fetcher

    def collect_trace(
        self,
        start_time: float,
        end_time: float,
        operation: str = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Collect trace data. And parse them into Dataframe object.

        Args:
            start_time (float): Start time timestamp, unit in second.
            end_time (float): End time timestamp, unit in second.
            operation (str, optional): Target operation, check Jaeger documentat
            ion for more information. Defaults to None.
            limit (int, optional): Limitation of records, check Jaeger documenta
            tion for more information. Defaults to 1000.

        Returns:
            pd.DataFrame: Collected data from jaeger in DataFrame, columns:
            trace_id, trace_time, start_time, end_time, parent_id, child_id,
            child_operation, parent_operation, child_ms, child_pod, parent_ms,
            parent_pod, parent_duration, child_duration

        """
        response = self.fetcher.fetch(start_time, end_time, operation, limit)
        log.debug(f"Fetch latency data from: {response.url}", to_file=True)
        data = json.loads(response.content)["data"]
        if len(data) == 0:
            log.error(f"No traces are fetched!", to_file=True)
            return
        else:
            log.debug(f"Number of traces: {len(data)}", to_file=True)
            return t_processor.load_from_json(data)

    def process_trace(
        self, collected_data: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Process collected data, return statistical and original data in a tup
        le. The first item of tuple is statistical data, and the second one is r
        aw data.

        Args:
            collected_data (pd.DataFrame): Data get from ``self.collect_trace()``,
            required columns: start_time, end_time, child_id, trace_id, parent_i
            d, child_duration, parent_ms, parent_pod, child_ms, child_pod

        Returns:
            tuple[pd.DataFrame]: Processed data, seperated into two parts, the f
            irst one is statistical data, columns: microservice, pod, p50, p95\n
            The second one is raw data, columns: all original columns + exact_pa
            rent_duration and steps.
        """
        exact_parent_duration_data = t_processor.exact_parent_duration(collected_data)
        p50_data = t_processor.decouple_parent_and_child(
            exact_parent_duration_data, 0.5
        ).rename(columns={"latency": "p50"})
        p95_data = t_processor.decouple_parent_and_child(
            exact_parent_duration_data, 0.95
        ).rename(columns={"latency": "p95"})
        statistical_data = p50_data.merge(p95_data)
        original_data = exact_parent_duration_data
        return statistical_data, original_data
