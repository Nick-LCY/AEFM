from handlers import *
from AEFM.manager import manager
from AEFM import configs

configs.CONFIG_FILE_PATH = "sample_configs.yaml"

manager.run()
