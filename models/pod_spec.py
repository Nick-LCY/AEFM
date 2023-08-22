from typing import Union


class PodSpec:
    """Used to define specification of pods, i.e. CPU limits or memory limits."""

    def __init__(self, cpu_size: Union[str, float, int], mem_size: str) -> None:
        """Used to define specification of pods, i.e. CPU limits or memory limits.

        Args:
            cpu_size (Union[str, float, int]): Limits of CPU, same as CPU limits
            /requests in Kubernetes config YAML.
            mem_size (str): Limits of memory capacity, same as memory limits/req
            uests in Kubernetes config YAML.
        """
        self.cpu_size: Union[str, float, int] = cpu_size
        self.mem_size: str = mem_size

    @staticmethod
    def load_from_dict(data: dict[str, Union[str, float, int]]) -> "PodSpec":
        """Used to generate object based on config YAML.

        Args:
            data (dict[str, Union[str, float, int]]): "pod_spec" part of config
            YAML.

        Returns:
            PodSpec: Corresponding object.
        """
        return PodSpec(data["cpu_size"], data["mem_size"])

    def to_k8s_resource(self) -> dict[str, dict[str, Union[str, float, int]]]:
        """Parse object to Kubernetes config YAML.

        Returns:
            dict[str, dict[str, Union[str, float, int]]]: Dict that can parse to
            validate YAML.
        """
        return {
            "requests": {
                "memory": self.get_mem(),
                "cpu": self.get_cpu(),
            },
            "limits": {
                "memory": self.get_mem(),
                "cpu": self.get_cpu(),
            },
        }

    def get_mem(self) -> str:
        """Get memory limitation.

        Returns:
            str: Memory limitation.
        """
        return self.mem_size

    def get_cpu(self) -> Union[str, float, int]:
        """Get CPU limitation

        Returns:
            Union[str, float, int]: CPU limitation.
        """
        return self.cpu_size
