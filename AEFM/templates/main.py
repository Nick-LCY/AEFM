from handlers import *
from AEFM.manager import manager
from AEFM import set_config_file, set_log_level

set_config_file("sample_configs.yaml")
set_log_level("info")

manager.run()
