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
            self.inf_types: list[str] = []
            self.inf_configs: list[dict] = []
            self.inf_count: list[int] = []

        def copy(self) -> "TestCase.Interference":
            """Return a copy of this object.

            Returns:
                TestCase.Interference: Copied object.
            """
            obj = TestCase.Interference()
            obj.inf_types = [x for x in self.inf_types]
            obj.inf_configs = [x for x in self.inf_configs]
            obj.inf_count = [x for x in self.inf_count]
            return obj

    def __init__(self) -> None:
        """A single test case of an experiment."""
        self.workload: TestCase.Workload
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
        """Marker is used to mark an event. After a test case with markers has b
        een used, events of its markers will be triggered.

        Args:
            marker (str): Name of marker.
        """        
        self.markers.append(marker)

    def append_inf(self, inf_type: str, inf_configs: dict, inf_count: int) -> None:
        """Append a new kind of interference.

        Args:
            inf_type (str): Type of interference.
            inf_configs (dict): Configs of interference.
            inf_count (int): Amount (by N.O. of pods) of interference.
        """        
        self.interferences.inf_types.append(inf_type)
        self.interferences.inf_configs.append(inf_configs)
        self.interferences.inf_count.append(inf_count)

    def copy(self) -> "TestCase":
        """Return a copy of this object.

        Returns:
            TestCase: Copied object.
        """
        obj = TestCase()
        obj.workload = self.workload.copy()
        obj.interferences = self.interferences.copy()
        obj.round = self.round
        obj.markers = deepcopy(self.markers)
        obj.additional = deepcopy(self.additional)
        return obj

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        content = f"["
        content += f"round: {self.round}, " if self.round is not None else ""
        content += (
            f"throughput: {self.workload.throughput}, "
            if self.workload is not None
            else ""
        )
        for inf_type, inf_count in zip(
            self.interferences.inf_types, self.interferences.inf_count
        ):
            content += f"{inf_type}: {inf_count}, "
        content += f"{self.additional}, " if len(self.additional) != 0 else ""
        return content[:-2] + "]"
