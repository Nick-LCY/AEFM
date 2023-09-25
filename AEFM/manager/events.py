from .base import manager
from typing import Literal


def register(
    event: Literal[
        "start_experiment",
        "init_environment",
        "start_single_test_case",
        "start_data_collection",
        "end_experiment",
    ]
):
    """Decorator that used to register a method to handle a event. Besides defau
    lt events, you can also register your customized events.

    Args:
        event (str): Event name.
    """

    def inner(func):
        manager.events.register(event, func)
        return func

    return inner
