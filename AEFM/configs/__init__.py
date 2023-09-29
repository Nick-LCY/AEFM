import os, yaml
from ..models import Node, PodSpec, TestCases
from ..utils.logger import log

CONFIG_FILE_PATH = None


class Configs:
    """Help you to manage configs of AEFM."""

    class FilePaths:
        """Used to store file paths, bascially include ``collector_data``, ``log``
        , and ``yaml_repo``. Other customized keys are welcome, and can be acces
        s by ``configs_obj.file_path.$CUSTOMIZED_KEY$``.
        """

        def __init__(self) -> None:
            """Used to store file paths, bascially include ``collector_data``,
            ``log``, and ``yaml_repo``. Other customized keys are welcome, and c
            an be access by ``configs_obj.file_path.$CUSTOMIZED_KEY$``.
            """
            self.collector_data: str = ""
            self.log: str = ""
            self.yaml_repo: str = ""

        @staticmethod
        def load_from_dict(data) -> "Configs.FilePaths":
            """Create FilePaths object based on YAML data.

            Args:
                data (dict): Loaded YAML object.

            Returns:
                Configs.FilePaths: Corresponding FilePaths object.
            """
            file_paths = Configs.FilePaths()
            for key in data:
                match key:
                    case "collector_data":
                        file_paths.collector_data = data[key]
                    case "log":
                        file_paths.log = data[key]
                    case "yaml_repo":
                        file_paths.yaml_repo = data[key]
                    case _:
                        file_paths.__setattr__(key, data[key])
            return file_paths

        def __getitem__(self, key):
            return self.__getattribute__(key)

    def __init__(self) -> None:
        """Help you to manage configs of AEFM. By default, ``file_paths``, ``nodes``,
        ``pod_spec``, ``test_cases``, ``namespace``, ``duation`` and ``app_img``
        will be available to use, but you can also set your customized config items.
        """
        self.file_paths: Configs.FilePaths
        self.nodes: dict[str, list[Node]] = {}
        self.pod_spec: PodSpec
        self.test_cases: TestCases

        self.namespace: str
        self.app_img: str
        self.duration: int

    @staticmethod
    def load_from_yaml(config_yaml: dict[str]) -> "Configs":
        """Load configs from a YAML object.

        Args:
            config_yaml (dict[str]): YAML object.

        Returns:
            Configs: Corresponding Configs object.
        """
        configs = Configs()
        for key in config_yaml:
            match key:
                case "file_paths":
                    configs.file_paths = Configs.FilePaths.load_from_dict(
                        config_yaml[key]
                    )
                case "nodes":
                    nodes = [Node.load_from_dict(x) for x in config_yaml[key]]
                    for node in nodes:
                        roles = node.get_roles()
                        for role in roles:
                            if role not in configs.nodes:
                                configs.nodes[role] = [node]
                            else:
                                configs.nodes[role].append(node)
                case "pod_spec":
                    configs.pod_spec: PodSpec = PodSpec.load_from_dict(config_yaml[key])
                case "test_cases":
                    configs.test_cases = TestCases.load_from_dict(config_yaml[key])
                case _:
                    configs.__setattr__(key, config_yaml[key])
        return configs

    def get_nodes_by_role(self, role: str) -> list[Node]:
        """Filter nodes by their roles.

        Args:
            role (str): Select nodes that have this ``role``.

        Returns:
            list[Node]: Selected nodes.
        """
        return self.nodes[role]

    def __getitem__(self, key):
        return self.__getattribute__(key)


def load_configs() -> Configs:
    """Load configs from YAML file. There are two way to specify the YAML file l
    ocation. By setting environment variable ``AEFM_CONFIGS`` or change the vari
    able ``configs.AEFM_CONFIGS``. The later one has higher priority than the fo
    rmer one. File location can be either abolute or relative path.

    Returns:
        Configs: Loaded configs object.
    """
    if CONFIG_FILE_PATH is not None:
        config_file = CONFIG_FILE_PATH
    else:
        config_file = os.environ.get("AEFM_CONFIGS", "aefm_configs.yaml")
    try:
        with open(config_file, "r") as file:
            configs_yaml = yaml.load(file, Loader=yaml.CLoader)
    except:
        raise BaseException("Wrong file type or file path!")
    log.key(f"Loading configs file from: {config_file}")
    return Configs.load_from_yaml(configs_yaml)
