from ..models import PodSpec, Node
from typing import Optional
from ..utils.kubernetes_YAMLs import KubernetesYAMLs
from ..utils.kubernetes import delete_by_yaml, deploy_by_yaml
from ..utils.files import delete_path, create_folder
from .intrefaces import DeployerInterface
import pathlib

TEMPLATE_FOLDER = (
    pathlib.Path(__file__).parent.parent.resolve().joinpath("yaml_repository")
)


class BaseDeployer(DeployerInterface):
    """AEFM default deployer, can help to manage applications. We seperate micro
    services of applications into two types: infra microservices and under test
    microservices. ``BaseDeployer`` allows user to deploy and config different t
    ype seperately. It also provides methods to quickly restart/reload applicati
    on.
    """

    def __init__(
        self,
        namespace: str,
        pod_spec: PodSpec,
        infra_nodes: list[Node],
        testbed_nodes: list[Node],
        yaml_repo: str,
        app_img: Optional[str] = None,
    ):
        """BaseDeployer constructor

        Args:
            namespace (str): where to deploy application.
            pod_spec (PodSpec): Resource limiation of under test pods.
            infra_nodes (list[Node]): List of nodes that used to deploy infra co
            mponents.
            testbed_nodes (list[Node]): List of nodes that used to deploy under
            test microservices.
            yaml_repo (str): Path to the YAML files folder.
            app_img (str, optional): Docker image of application, set
            to none to keep not change of original ones. Defaults to None.
        """
        self.namespace: str = namespace
        self.pod_spec: PodSpec = pod_spec
        self.testbed_nodes: list[Node] = testbed_nodes
        self.infra_nodes: list[Node] = infra_nodes
        self.yaml_repo: str = yaml_repo.replace("$MODULE_DEFAULT", TEMPLATE_FOLDER.as_posix())
        self.tmp_under_test_path = f"tmp/under_test_{namespace}"
        self.tmp_infra_path = f"tmp/infra_{self.namespace}"
        self.app_img: Optional[str] = app_img

    def prepare_infra_yaml(self) -> "BaseDeployer":
        """Prepare YAMLs for infra microservices.

        Returns:
            BaseDeployer: Return self for chaining.
        """
        # Clear YAML files generated previously
        delete_path(self.tmp_infra_path)
        create_folder(self.tmp_infra_path)
        # Edit infra YAMLs, save them to tmp folder
        infra_yamls = KubernetesYAMLs(f"{self.yaml_repo}/infra")
        infra_yamls.update(
            "metadata.namespace", self.namespace, target_kind=None
        ).assign_affinity(self.infra_nodes).update(
            "spec.template.spec.containers[0].imagePullPolicy", "IfNotPresent"
        ).save(
            self.tmp_infra_path
        )
        return self

    def deploy_infra_yaml(self) -> "BaseDeployer":
        """Deploy infra microservices.

        Returns:
            BaseDeployer: Return self for chaining.
        """
        delete_by_yaml(self.tmp_infra_path)
        deploy_by_yaml(self.tmp_infra_path, wait=True, namespace=self.namespace)
        return self

    def prepare_under_test_yaml(
        self, replicas: Optional[dict[str, int]] = None
    ) -> "BaseDeployer":
        """Prepare YAMLs for under test microservices.

        Args:
            replicas (dict[str, int]): Dict of replicas, key is deployment name
            and value is the replicas of that deployment.

        Returns:
            BaseDeployer: Return self for chaining.
        """
        replicas = replicas if replicas is not None else {}
        # Clear YAML files generated previously
        delete_path(self.tmp_under_test_path)
        create_folder(self.tmp_under_test_path)
        # Edit under_test YAMLs, save them to tmp folder
        under_test = KubernetesYAMLs(f"{self.yaml_repo}/under_test")
        under_test.base_yaml_preparation(
            self.namespace, self.pod_spec, self.app_img
        ).assign_affinity(self.testbed_nodes).assign_containers(replicas).update(
            "spec.template.spec.containers[0].imagePullPolicy", "IfNotPresent"
        ).save(
            self.tmp_under_test_path
        )
        return self

    def deploy_under_test_yaml(self) -> "BaseDeployer":
        """Deploy under test microservices.

        Returns:
            BaseDeployer: Return self for chaining.
        """
        delete_by_yaml(self.tmp_under_test_path)
        deploy_by_yaml(self.tmp_under_test_path, True, self.namespace)
        return self

    def restart(self, application: str, port: int):
        """Restart the whole application.

        Args:
            application (str): Which application you are using.
            port (int): Entrance port of that application, used to write data.
        """
        self.prepare_infra_yaml().deploy_infra_yaml()
        self.prepare_under_test_yaml().deploy_under_test_yaml()

        match application:
            case "social":
                from .init_social_network import main

                main(port=port)
            case "media":
                from .init_media_microsvc_1 import main

                main(server_address=f"http://localhost:{port}")
                from .init_media_microsvc_2 import main

                main(server_address=f"http://localhost:{port}")
            case _:
                pass

    def reload(self, replicas: Optional[dict[str, int]] = None):
        """Reload only under test microservices.

        Args:
            replicas (dict[str, int]): Dict of replicas, key is deployment name
            and value is the replicas of that deployment.
        """
        self.prepare_under_test_yaml(replicas).deploy_under_test_yaml()
