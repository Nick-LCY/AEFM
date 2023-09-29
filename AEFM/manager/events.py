from .base import manager
from typing import Literal


def register(
    event: Literal[
        "start_experiment",
        "init_environment",
        "start_single_test_case",
        "start_data_collection",
        "end_experiment",
    ],
    method: Literal["insert", "replace", "append"] = "replace",
):
    """Decorator that used to register a method to handle a event. Besides defau
    lt events, you can also register your customized events.

    Args:
        event (str): Event name.
        method (str): How to register this handler, append to the end of all han
        lers / insert into the begin of all handlers / discard all other handler
        s and use this one only.
    """

    def inner(func):
        manager.events.register(event, func, method)
        return func

    return inner
