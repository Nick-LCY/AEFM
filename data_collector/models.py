import pandas as pd


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
                    ms_records.keys(), ms_records.values(), columns=["pod", "usage"]
                ).assign(microservice=microservice)
            )
        return pd.concat(records)[["microservice", "pod", "usage"]]


class CpuUsage(UsageRecords):
    """For CPU usage records"""    


class MemUsage(UsageRecords):
    """For memory capacity usage records"""    
