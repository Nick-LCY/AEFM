from . import manager
from typing import Literal


def register(
    event: Literal[
        "start_experiment",
        "init_environment",
        "generate_test_cases",
        "start_single_test_case",
        "start_data_collection",
        "update_environment",
        "end_experiment",
    ]
):
    def inner(func):
        manager.events.register(event, func)
        return func

    return inner
