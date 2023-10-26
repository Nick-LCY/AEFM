from . import configs
from . import data_collector
from . import deployer
from . import inf_generator
from . import manager
from . import models
from . import utils
from . import workload_generator
from typing import Literal


def set_log_level(level: Literal["debug", "info", "key", "warn", "error", "off"]):
    from .utils.logger import log

    log.level = level


def set_config_file(file_path: str):
    configs.CONFIG_FILE_PATH = file_path
