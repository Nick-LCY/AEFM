from typing import Union, Callable
from .test_case import TestCase


def _load_range(data: Union[list[int], dict[str, int]]) -> list[int]:
    """Parse a range section in configs YAML into a list of int.

    Args:
        data (Union[list[int], dict[str, int]]): Raw range section in YAML objec
        ts.

    Raises:
        ValueError: Raised if range section is invalid.

    Returns:
        list[int]: Processed range section.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # todo: Exception management
        assert "min" in data and "max" in data and "step" in data
        return [i for i in range(data["min"], data["max"] + 1, data["step"])]
    if data is None:
        return None
    # todo: Exception management
    raise ValueError("value of range field should be either dict of list")


class TestCases:
    """Used to record all test cases."""

    class Workload:
        """Workload configs with its range."""

        def __init__(self) -> None:
            """Workload configs with its range."""
            self.configs = {}
            self.range = list[int]

        @staticmethod
        def load_from_dict(data: dict) -> "TestCases.Workload":
            """Load a Workload object from YAML object.

            Args:
                data (dict): YAML object.

            Returns:
                TestCases.Workload: Corresponding object.
            """
            workload = TestCases.Workload()
            workload.configs = data["configs"]
            workload.range = _load_range(data["range"])
            return workload

        def __getitem__(self, key):
            return self.__getattribute__(key)

    class Interference:
        """Interference configs with its range."""

        def __init__(self) -> None:
            """_summary_Interference configs with its range."""
            self.inf_type: str
            self.configs: dict
            self.range: list[int]

        @staticmethod
        def load_from_dict(data: dict, inf_type: str) -> "TestCases.Interference":
            """Load a Interference object from YAML object.

            Args:
                data (dict): YAML object.
                inf_type (str): Type name of interference.

            Returns:
                TestCases.Interference: Corresponding object.
            """
            interference = TestCases.Interference()
            interference.inf_type = inf_type
            interference.configs = data["configs"]
            interference.range = _load_range(data["range"])
            return interference

    def __init__(self) -> None:
        """_summary_Used to record all test cases."""
        self.orders: list[str]
        self.round: list[int]
        self.workload: TestCases.Workload
        self.interferences: dict[str, TestCases.Interference] = {}
        self.generated_test_cases: list[TestCase] = []

    @staticmethod
    def load_from_dict(data: dict) -> "TestCases":
        """Create a TestCases object based on YAML object.

        Args:
            data (dict): YAML object.

        Returns:
            TestCases: Corresponding object.
        """
        test_cases = TestCases()
        test_cases.orders = data["orders"]
        test_cases.round = _load_range(data["round"])
        test_cases.workload = TestCases.Workload.load_from_dict(data["workload"])
        inf_data = data["interferences"] if data["interferences"] is not None else {}
        for inf_type in inf_data:
            test_cases.interferences[inf_type] = TestCases.Interference.load_from_dict(
                inf_data[inf_type], inf_type
            )
        for key in data:
            if key in ["orders", "round", "workload", "interferences"]:
                continue
            test_cases.__setattr__(key, data[key])
        return test_cases

    def generate(self, force: bool = False) -> list[TestCase]:
        """Based on current TestCases object, generate all test cases configs an
        d save them as a list. The generation order will follow the ``orders`` p
        art of configs, the first item in orders will be looped first. If orders
        doesn't contain a name, its corresponding configs will not be contained
        in the final test cases.

        Args:
            force (bool, optional): Force generate test cases. By default, ``gen
            erate()`` method will cache previous results, using force to remove
            them and regenerate test cases. Defaults to False.
        """
        if len(self.generated_test_cases) != 0 and not force:
            return self.generated_test_cases

        def product(
            order: str,
            test_cases: list[TestCase],
            iterator: list[int],
            data: dict = None,
        ):
            if len(test_cases) == 0:
                test_cases = [TestCase() for _ in iterator]
                for obj, i in zip(test_cases, iterator):
                    match order:
                        case "round":
                            obj.set_round(i)
                        case "workload":
                            wl = TestCase.Workload(i, **data)
                            obj.set_workload(wl)
                        case _:
                            if order in self.interferences:
                                obj.set_inf(inf_count=i, **data)
                            else:
                                obj.set_additional(order, i)
                    obj.append_marker(order)
                return test_cases

            current_test_cases = test_cases
            test_cases = []
            for i in iterator:
                updated_test_cases = [x.copy() for x in current_test_cases]
                match order:
                    case "round":
                        [x.set_round(i) for x in updated_test_cases]
                    case "workload":
                        wl = TestCase.Workload(i, **data)
                        [x.set_workload(wl) for x in updated_test_cases]
                    case _:
                        if order in self.interferences:
                            [x.set_inf(inf_count=i, **data) for x in updated_test_cases]
                        else:
                            [x.set_additional(order, i) for x in updated_test_cases]
                updated_test_cases[0].append_marker(order)
                test_cases.extend(updated_test_cases)
            return test_cases

        test_cases = []
        for order in self.orders:
            match order:
                case "round":
                    test_cases = product(order, test_cases, self.round)
                case "workload":
                    wl = self.workload
                    test_cases = product(
                        order, test_cases, wl.range, {"configs": wl.configs}
                    )
                case _:
                    if order in self.interferences:
                        inf = self.interferences[order]
                        test_cases = product(
                            order,
                            test_cases,
                            inf.range,
                            {"inf_type": inf.inf_type},
                        )
                    else:
                        test_cases = product(
                            order, test_cases, self.__getattribute__(order)
                        )
        self.generated_test_cases = test_cases
        return test_cases

    def __len__(self) -> int:
        self.generate()
        return len(self.generated_test_cases)

    def iter(self, workflow: Callable[[TestCase], None]):
        """Iterate all test cases.

        Args:
            workflow (Callable[[TestCase], None]): A method that contains the wo
            rkflow of a single test case. Current test case will be passed into
            it as a parameter.
        """
        from ..manager import manager

        self.generate()
        for test_case in self.generated_test_cases:
            manager.data.set("current_test_case", test_case)
            for marker in test_case.markers:
                manager.events.trigger(f"start_{marker}")
            workflow()
