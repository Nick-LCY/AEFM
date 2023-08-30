from .interfaces import InfGeneratorInterface
import os, pathlib, yaml
from utils.kubernetes import deploy_by_yaml, wait_deletion, delete_by_name
from utils.files import delete_path
from models import Node
from utils.kubernetes_YAMLs import KubernetesYAMLs
from typing import Literal

_AFFINITY_TEMPLATE = (
    "nodeAffinity:\n"
    "  requiredDuringSchedulingIgnoredDuringExecution:\n"
    "    nodeSelectorTerms:\n"
    "    - matchExpressions:\n"
    "      - key: kubernetes.io/hostname\n"
    "        operator: In\n"
    "        values: %%%\n"
)
TEMPLATE_FOLDER = pathlib.Path(__file__).parent.resolve().joinpath("templates")


class BaseInfGenerator(InfGeneratorInterface):
    """Default interference generator."""

    def __init__(
        self,
        inf_type: Literal["cpu", "mem_capacity", "mem_bandwidth", "network"],
        configs: dict,
        namespace: str = "interference",
        duration: int = 86400,
    ):
        """Initialize a interference generator with certain type.

        Args:
            inf_type (str): "cpu" for CPU interference, "mem_capacity" for memor
            y capaciry interference, "mem_bandwidth" for memory bandwidth interf
            erence and "network" for network bandwidth interference.
            configs (dict): Configuration of interference, available keys: "mem_
            size", "cpu_size" and "throughput".
            namespace (str): Namespace used to deploy interference.
            duration (int): Duration of interference pods.
        """
        self.resource_limits = {
            "requests": {"memory": configs["mem_size"], "cpu": configs["cpu_size"]},
            "limits": {"memory": configs["mem_size"], "cpu": configs["cpu_size"]},
        }
        self.inf_type = inf_type
        self.namespace = namespace
        self.command = {
            "cpu": "/ibench/src/cpu",
            "mem_capacity": "/ibench/src/memCap",
            "mem_bandwidth": "/ibench/src/memBw",
            "network": "",
        }[self.inf_type]

        match self.inf_type:
            case "cpu":
                self.args = [f"{duration}s"]
            case "mem_capacity":
                self.args = [f"{duration}s", "wired", "100000s"]
            case "mem_bandwidth":
                self.args = [f"{duration}s"]
            case "network":
                self.args = [configs["throughput"], duration]

    def generate(self, count: int, nodes: list[Node], wait: bool = True) -> None:
        """Generate interferences on ``nodes`` with ``count`` pods.

        Args:
            count (int): Number of generated pods on each node.
            nodes (list[Node]): Nodes that needs to be deployed with interference.
            wait (bool, optional): Wait until generation finished? Defaults to True.
        """
        self.deployed_nodes = nodes
        delete_path("tmp/net-interference")
        delete_path("tmp/interference")
        self.clear(wait=False)
        if self.inf_type == "network":
            self._generate_network_inf(nodes, count)
            deploy_by_yaml("tmp/net-interference", wait, self.namespace)
        else:
            for node, name in zip(nodes, self._get_inf_names()):
                self._generate_single_interference(node, name, count)
            deploy_by_yaml("tmp/interference", wait, self.namespace)

    def _get_inf_names(self):
        if self.inf_type == "network":
            cm_name = "-".join(self.deployed_nodes) + "-launch-script"
            ds_name = "network-" + "-".join(self.deployed_nodes)
            return [cm_name, ds_name]
        names = []
        for node in self.deployed_nodes:
            names.append(f"{self.inf_type}-{node}".replace("_", "-"))
        return names

    def clear(self, wait: bool = False):
        """Delete all interference pod generated by this generator

        Args:
            wait (bool, optional): Wait untile deletion finished? Defaults to False.
        """
        if self.inf_type == "network":
            cm_name, ds_name = self._get_inf_names()
            # todo: find a better way to delete
            os.system(f"kubectl delete cm -n {self.namespace} {cm_name}")
            os.system(f"kubectl delete ds -n {self.namespace} {ds_name}")
            if wait:
                wait_deletion(self.namespace, 300)
        for name in self._get_inf_names():
            delete_by_name(name, self.namespace, wait)

    def _generate_network_inf(self, nodes: list[Node], count: int):
        nodes_str = [str(x) for x in nodes]
        cm_name, ds_name = self._get_inf_names()

        k8s_yaml = KubernetesYAMLs(TEMPLATE_FOLDER.joinpath("net-inf.yaml"))
        affinity = yaml.load(
            _AFFINITY_TEMPLATE.replace("%%%", f"[{','.join(nodes_str)}]"),
            Loader=yaml.CLoader,
        )
        ds_pairs = [
            ("metadata.namespace", self.namespace),
            ("metadata.name", ds_name),
            ("spec.template.spec.affinity", affinity),
            ("spec.template.spec.containers[0].resources", self.resource_limits),
            ("spec.template.spec.containers[1].resources", self.resource_limits),
            ("spec.template.spec.containers[1].env[1].value", self.args[0]),
            ("spec.template.spec.containers[1].env[2].value", str(self.args[1])),
            ("spec.template.spec.containers[1].env[3].value", str(count)),
            ("spec.template.spec.volumes[0].configMap.name", cm_name),
        ]

        for pair in ds_pairs:
            k8s_yaml.update(pair[0], pair[1], target_kind="DaemonSet")

        cm_pairs = [
            ("metadata.namespace", self.namespace),
            ("metadata.name", cm_name),
            ("data.data", "\n".join([x.ip for x in nodes] + [nodes[0].ip])),
        ]

        for pair in cm_pairs:
            k8s_yaml.update(pair[0], pair[1], target_kind="ConfigMap")

        k8s_yaml.save("tmp/net-interference")

    def _generate_single_interference(self, node: Node, name: str, count: int):
        k8s_yaml = KubernetesYAMLs(TEMPLATE_FOLDER.joinpath("interference.yaml"))
        affinity = yaml.load(
            _AFFINITY_TEMPLATE.replace("%%%", f"[{node}]"),
            Loader=yaml.CLoader,
        )
        pairs = [
            ("metadata.name", name),
            ("metadata.namespace", self.namespace),
            ("spec.replicas", count),
            ("spec.template.spec.containers[0].resources", self.resource_limits),
            ("spec.template.spec.containers[0].command[0]", self.command),
            ("spec.template.spec.containers[0].args", self.args),
            ("spec.template.spec.affinity", affinity),
        ]
        for pair in pairs:
            k8s_yaml.update(pair[0], pair[1])
        k8s_yaml.save(f"tmp/interference/{name}.yaml")
