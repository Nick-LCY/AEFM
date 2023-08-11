from collections.abc import Callable
from typing import Any, Literal


class _Events(object):
    def __new__(cls) -> "_Events":
        if not hasattr(cls, "instance"):
            cls.instance = super(_Events, cls).__new__(cls)
        return cls.instance

    def trigger(
        self,
        event: Literal[
            "start_experiment",
            "init_environment",
            "generate_test_cases",
            "start_single_test_case",
            "start_data_collection",
            "update_environment",
            "end_experiment",
        ],
    ) -> Any:
        if not hasattr(self, event):
            # todo: exception management
            return
        return self.__getattribute__(event)()

    def register(
        self,
        event: Literal[
            "start_experiment",
            "init_environment",
            "generate_test_cases",
            "start_single_test_case",
            "start_data_collection",
            "update_environment",
            "end_experiment",
        ],
        handler: Callable,
    ) -> None:
        self.__setattr__(event, handler)


class _Components(object):
    def __new__(cls) -> "_Components":
        if not hasattr(cls, "instance"):
            cls.instance = super(_Components, cls).__new__(cls)
        return cls.instance

    def set(self, name: str, component: Any) -> None:
        self.__setattr__(name, component)

    def get(self, name: str):
        return self.__getattribute__(name)


class _Data(object):
    def __new__(cls) -> "_Data":
        if not hasattr(cls, "instance"):
            cls.instance = super(_Data, cls).__new__(cls)
        return cls.instance

    def set(self, name: str, value: Any) -> None:
        self.__setattr__(name, value)

    def get(self, name: str) -> Any:
        if not hasattr(self, name):
            # todo: exception management
            return
        return self.__getattribute__(name)


class ExperimentManager(object):
    """Experiment manager, used to manage data, events and components of experim
    ent. To access data, events and components, please use ``manager.data``, ``m
    anager.events`` and ``manager.componenets``.
    """

    def __init__(self) -> None:
        self.events = _Events()
        self.components = _Components()
        self.data = _Data()

    def run(self):
        """A built-in experiment process. You can customize your own experiment
        process by trigger different events.
        """
        trigger = self.events.trigger
        trigger("start_experiment")
        trigger("init_environment")
        trigger("generate_test_cases")
        for test_case in self.data.get("test_cases"):
            self.data.set("current_test_case", test_case)
            trigger("start_single_test_case")
            trigger("start_data_collection")
            trigger("update_environment")
        trigger("end_experiment")


manager = ExperimentManager()
