from models import TestCases, TestCase
from .interfaces import ManagerInterface, _Events, _Components, _Data


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
        trigger("generate_test_cases")
        test_cases = self.data.get("test_cases")
        assert isinstance(test_cases, TestCases)

        def test_case_workflow(test_case: TestCase):
            print(test_case)
            self.data.set("current_test_case", test_case)
            trigger("start_single_test_case")
            trigger("start_data_collection")
            trigger("update_environment")

        test_cases.iter(test_case_workflow, manager)
        trigger("end_experiment")


manager = BaseManager()
