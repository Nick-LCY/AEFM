from copy import deepcopy
from typing import Any


class TestCase:
    """A single test case of an experiment."""

    class Workload:
        """Workload configs and throughput of workload generator."""

        def __init__(self, throughput: int, configs: dict) -> None:
            """Workload configs and throughput of workload generator.

            Args:
                throughput (int): Requests per second.
                configs (dict): Workload generator configs.
            """
            self.throughput = throughput
            self.configs = configs

        def copy(self) -> "TestCase.Workload":
            """Return a copy of this object.

            Returns:
                TestCase.Workload: Copied object.
            """
            return TestCase.Workload(self.throughput, deepcopy(self.configs))

    class Interference:
        """Configs and amount of interferences."""

        def __init__(self) -> None:
            """Configs and amount of interferences."""
            self.inf_count: dict[str, int] = {}

        def __iter__(self) -> "TestCase.Interference":
            self.idx = 0
            self.inf_types = list(self.inf_count.keys())
            return self

        def __next__(self) -> tuple[str, int]:
            if self.idx >= len(self.inf_types):
                raise StopIteration
            result = (
                self.inf_types[self.idx],
                self.inf_count[self.inf_types[self.idx]],
            )
            self.idx += 1
            return result

        def __len__(self) -> int:
            return len(self.inf_count)

        def __getitem__(self, key):
            return self.inf_count[key]
        
        def __setitem__(self, key, value):
            self.inf_count[key] = value

        def copy(self) -> "TestCase.Interference":
            """Return a copy of this object.

            Returns:
                TestCase.Interference: Copied object.
            """
            obj = TestCase.Interference()
            obj.inf_count = deepcopy(self.inf_count)
            return obj

    def __init__(self) -> None:
        """A single test case of an experiment."""
        self.workload: TestCase.Workload = None
        self.interferences = TestCase.Interference()
        self.round: int = None
        self.markers: list[str] = []
        self.additional: dict[str, Any] = {}

    def set_additional(self, key: str, value: Any) -> None:
        """Store additional data of test case

        Args:
            key (str): Additional data name.
            value (Any): Additional data value.
        """
        self.additional[key] = value

    def set_workload(self, workload: "TestCase.Workload") -> None:
        """Set workload configuration.

        Args:
            workload (TestCase.Workload): Workload configuration.
        """
        self.workload = workload

    def set_round(self, round: int) -> None:
        """Set round (repeat) of current test case.

        Args:
            round (int): A.K.A. repeat.
        """
        self.round = round

    def append_marker(self, marker: str) -> None:
        """Marker is used to mark an event. Before a test case with markers star
        ts, events of its markers will be triggered.

        Args:
            marker (str): Name of marker.
        """
        self.markers.append(marker)

    def set_inf(self, inf_type: str, inf_count: int) -> None:
        """Set a new kind of interference.

        Args:
            inf_type (str): Type of interference.
            inf_count (int): Amount (by N.O. pods) of interference.
        """
        self.interferences[inf_type] = inf_count

    def copy(self) -> "TestCase":
        """Return a copy of this object.

        Returns:
            TestCase: Copied object.
        """
        obj = TestCase()
        if self.workload is not None:
            obj.workload = self.workload.copy()
        obj.interferences = self.interferences.copy()
        obj.round = self.round
        obj.markers = deepcopy(self.markers)
        obj.additional = deepcopy(self.additional)
        return obj

    def generate_name(self) -> str:
        content = f"round={self.round}|" if self.round is not None else ""
        content += (
            f"throughput={self.workload.throughput}|"
            if self.workload is not None
            else ""
        )
        for inf_type, inf_count in self.interferences:
            content += f"{inf_type}={inf_count}|"
        for key in self.additional:
            content += f"{key}={self.additional[key]}|"
        return content[:-1]

    def to_dict(self) -> dict[str, Any]:
        result = {}
        if self.round is not None:
            result["round"] = self.round
        if self.workload is not None:
            result["throughput"] = self.workload.throughput
        for inf_type, inf_count in self.interferences:
            result[inf_type] = inf_count
        for key in self.additional:
            result[key] = self.additional[key]
        return result

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return "[" + self.generate_name().replace("|", ", ").replace("=", ": ") + "]"
