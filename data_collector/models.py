import pandas as pd
from typing import Any


class TestCaseData:
    """A data structure that used to staore test case information."""

    def __init__(
        self,
        start_time: float,
        end_time: float,
        name: str,
        additional_columns: dict[str, Any] = None,
        operation: str = None,
    ) -> None:
        """A data structure that used to staore test case information.

        Args:
            start_time (float): Start time of current test case.
            end_time (float): End time of current test case.
            name (str): Name of this test case.
            additional_columns (dict[str, Any], optional): Additional columns th
            at needs to be saved in output data of collector. Defaults to None.
            operation (str, optional): Jaeger operation. Defaults to None.
        """
        self.start_time = start_time
        self.end_time = end_time
        self.operation = operation
        self.name = name
        self.additional_columns = additional_columns


class UsageRecords:
    """Used to store hardware resouce usage from different pods under different
    microservices."""

    def __init__(self) -> None:
        self.records: dict[str, dict[str, float]] = {}

    def set(self, microservice: str, pod: str, usage: float):
        """Set ``usage`` of a ``pod`` from a ``microservice``.

        Args:
            microservice (str): Name of microservice.
            pod (str): Name of pod.
            usage (float): Resource usage, range: 0 - 1.
        """
        if microservice not in self.records:
            self.records[microservice] = {}
        self.records[microservice][pod] = usage

    def get(self, microservice: str, pod: str) -> float:
        """Get hardware resource ``usage`` of a ``pod`` from a ``microservice``.

        Args:
            microservice (str): Name of microservice.
            pod (str): Name of pod.

        Returns:
            float: Resource usage, range: 0 - 1.
        """
        if microservice not in self.records:
            # todo: Exception
            return
        if pod not in self.records[microservice]:
            # todo: Exception
            return
        return self.records[microservice][pod]

    def to_pandas(self) -> pd.DataFrame:
        """Return pandas object of records.

        Returns:
            pd.DataFrame: columns: microservice, pod, usage; data type: str, str
            , int.
        """
        records = []
        for microservice in self.records:
            ms_records = self.records[microservice]
            records.append(
                pd.DataFrame(
                    zip(ms_records.keys(), ms_records.values()),
                    columns=["pod", "usage"],
                ).assign(microservice=microservice)
            )
        return pd.concat(records)[["microservice", "pod", "usage"]]


class CpuUsage(UsageRecords):
    """For CPU usage records."""


class MemUsage(UsageRecords):
    """For memory capacity usage records."""
