from abc import abstractmethod, ABC
from typing import Any, Literal
from collections.abc import Callable
from utils.logger import log


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
            "start_single_test_case",
            "start_data_collection",
            "update_environment",
            "end_experiment",
        ],
    ) -> Any:
        if not hasattr(self, event):
            log.warn(f'Event: "{event}" doesn\'t have a handler.')
            return
        log.key(f'Event: "{event}" has triggered.')
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


class ManagerInterface(ABC):
    """An experiment manager must have ``run()`` method. Which represents the wo
    rkflow of an experiment. It also have other three required attributes: ``events``,
    ``componenets`` and ``data``. They are used for globally manage data and met
    hods.
    """

    def __init__(self) -> None:
        self.events = _Events()
        self.components = _Components()
        self.data = _Data()

    @abstractmethod
    def run(self):
        """Workflow of an experiment."""
