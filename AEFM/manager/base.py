from ..models import TestCases
from .interfaces import ManagerInterface, _Events, _Components, _Data
from ..utils.logger import log
from ..utils.timer import timer


class BaseManager(ManagerInterface):
    """Base experiment manager, used to manage data, events and components of ex
    periment. To access data, events and components, please use ``manager.data``
    , ``manager.events`` and ``manager.componenets``.
    """

    def __init__(self) -> None:
        """Base experiment manager, used to manage data, events and components o
        f experiment. To access data, events and components, please use ``manage
        r.data``, ``manager.events`` and ``manager.componenets``.
        """
        self.events = _Events()
        self.components = _Components()
        self.data = _Data()

    def run(self):
        """A built-in experiment process. You can customize your own experiment
        process by trigger different events with ``manager.events.trigger``.
        """
        trigger = self.events.trigger
        trigger("start_experiment")
        trigger("init_environment")
        test_cases = self.data.get("test_cases")
        assert isinstance(test_cases, TestCases)

        @timer(name="single test case", total_count=len(test_cases), level="key")
        def test_case_workflow():
            trigger("start_single_test_case")
            trigger("start_data_collection")
        log.info(f"Total test cases: {len(test_cases)}")
        test_cases.iter(test_case_workflow)
        trigger("end_experiment")


manager = BaseManager()
