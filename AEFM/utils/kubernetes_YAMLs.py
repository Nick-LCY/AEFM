import os, yaml, re
from typing import Any, Optional
from collections.abc import Callable
from ..models import PodSpec, Node
from .files import delete_path, create_folder

_AFFINITY_TEMPLATE = """
nodeAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    nodeSelectorTerms:
    - matchExpressions:
      - key: kubernetes.io/hostname
        operator: In
        values: %%%
"""


class KubernetesYAMLs:
    """KubernetesYAMLs load kubernetes componetns from YAML files and provide me
    thods to edit them quickly.
    """

    def __init__(self, path: str) -> None:
        """Load kubernetes components from a folder or a single YAML file.

        Args:
            path (str): A folder with YAML files or a single YAML file.
        """
        if os.path.isfile(path):
            with open(path, "r") as file:
                self.yamls: list[dict] = [
                    x for x in yaml.load_all(file, Loader=yaml.CLoader) if x is not None
                ]
        elif os.path.isdir(path):
            yaml_files = [
                x for x in os.listdir(path) if x[-5:] == ".yaml" or x[-4:] == ".yml"
            ]
            yaml_list = []
            for file_name in yaml_files:
                with open(f"{path}/{file_name}", "r") as file:
                    yaml_objs = yaml.load_all(file, Loader=yaml.CLoader)
                    yaml_list.extend([x for x in yaml_objs if x is not None])
            self.yamls: list[dict] = yaml_list
        else:
            raise FileNotFoundError(f"{path} not found")

    def update(
        self,
        path: str,
        value: Any,
        target_kind: Optional[str] = "Deployment",
        key_path: Optional[str] = None,
    ) -> "KubernetesYAMLs":
        """Batch update all data at ``path`` to given ``value`` for all YAML obj
        ects.

        Args:
            path (str): Python format like path indictor, example: "here.is.an.e
            xample[0]"
            value (Any): A fixed value if ``key_path`` is None. Or a Dict that w
            ill select different value based on ``key_path``.
            target_kind (str, optional): Which kind of kubernet es YAML is neede
            d to be edit. Defaults to "Deployment".
            key_path (str, optional): If given a path, will select different val
            ue from ``value`` dict based on the value of that path. Defaults to
            None.

        Returns:
            KubernetesYAMLs: Return self for chaining.
        """
        edited_yaml: list[dict] = []
        for yaml_obj in self.yamls:
            if target_kind is not None:
                target_success, target, _ = search_path(yaml_obj, "kind")
                if target != target_kind or not target_success:
                    edited_yaml.append(yaml_obj)
                    continue
            if key_path is not None:
                edited_yaml.append(_mapping_edit(yaml_obj, path, value, key_path))
            else:
                edited_yaml.append(_edit(yaml_obj, path, value))
        self.yamls = edited_yaml
        return self

    def save(self, path: str) -> None:
        """Save current YAML objects into seperated files,
        or save it to a single file if there is only one YAML object

        Args:
            path (str): folder path for multiple YAML objects or file path for single YAML object
        """
        delete_path(path)

        def save_file(yaml_obj, file_path):
            # YAML may dump reference instead of object,
            # following code help to avoid this kind of case.
            # Totally have no idea why this can work
            # Ref: https://stackoverflow.com/questions/51272814/python-yaml-dumping-pointer-references
            yaml.Dumper.ignore_aliases = lambda *_: True
            with open(file_path, "w") as file:
                yaml.dump(yaml_obj, file, default_flow_style=False)

        if len(self.yamls) == 1:
            create_folder(path)
            delete_path(path)
            save_file(self.yamls[0], path)
        else:
            create_folder(path)
            for yaml_obj in self.yamls:
                file_name = f'{yaml_obj["metadata"]["name"]}_{yaml_obj["kind"]}.yaml'
                save_file(yaml_obj, f"{path}/{file_name}")

    def base_yaml_preparation(
        self,
        namespace: str,
        pod_spec: Optional[PodSpec] = None,
        app_img: Optional[str] = None,
    ) -> "KubernetesYAMLs":
        """Add namespace, resource limitation and docker image name to YAMLs.

        Args:
            namespace (str): Kubernetes namespace.
            pod_spec (PodSpec, optional): Resources limitation, set to none will
             allow pods use unlimited resources. Defaults to None.
            app_img (Optional[str], optional): Docker image, set to none will no
            t change docker image. Defaults to None.

        Returns:
            KubernetesYAMLs: Return self for chaining.
        """
        self.update("metadata.namespace", namespace, target_kind=None)
        if pod_spec is not None:
            self.update(
                "spec.template.spec.containers[0].resources",
                pod_spec.to_k8s_resource(),
            )
        if app_img is not None:
            self.update(
                "spec.template.spec.containers[0].image",
                {"APP_IMG": app_img},
                key_path="spec.template.spec.containers[0].image",
            )

        return self

    def assign_containers(self, replicas: dict[str, int]) -> "KubernetesYAMLs":
        """Set the number of replicas of kubernetes deployment based on deployme
        nt names.

        Args:
            replicas (dict[str, int]): Dict of replicas, key is deployment name
            and value is the replicas of that deployment.

        Returns:
            KubernetesYAMLs: Return self for chaining.
        """
        path = "spec.replicas"
        key_path = "metadata.name"
        self.update(path, replicas, key_path=key_path)

        return self

    def assign_affinity(self, nodes: list[Node]) -> "KubernetesYAMLs":
        """Config available nodes of deployment.

        Args:
            nodes (list[Node]): List of available nodes.

        Returns:
            KubernetesYAMLs: Return self for chaining.
        """
        node_strs = [str(x) for x in nodes]
        node_affinity = yaml.load(
            _AFFINITY_TEMPLATE.replace("%%%", f'[{", ".join(node_strs)}]'),
            yaml.CLoader,
        )
        path = "spec.template.spec.affinity"
        value = node_affinity
        self.update(path, value)
        return self


def search_path(
    obj: dict,
    path: str,
    key_not_found: Callable[[str, dict], tuple[bool, dict]] = lambda _, o: (False, o),
    need_append: Callable[[str, dict], tuple[bool, dict]] = lambda _, o: (False, o),
    index_invalid: Callable[[str, dict], tuple[bool, dict]] = lambda _, o: (False, o),
) -> tuple[bool, dict, str]:
    """search_path is a method that used to search a python object by the given
    path. When it reach the target, it will return target's value. Otherwise, it
     will call different method based on different situation.

    Args:
        obj (dict): Python dictionary that is goting to be searched.
        path (str): Path to the target.
        key_not_found (Callable[[str, dict], tuple[bool, dict]], optional): Trig
        gered when the given key is not found.
        need_append (Callable[[str, dict], tuple[bool, dict]], optional): Trigge
        red when the given index is the next index of the list.
        index_invalid (Callable[[str, dict], tuple[bool, dict]], optional): Trig
        gered when the given index is an invalid index of the list.

    Raises:
        TypeError: Raised if user trying to get item by index from a non-list ob
        ject.

    Returns:
        Tuple[bool, dict, str]: is success, last object, last searched path.
    """
    partial_obj = obj
    path_list = path.split(".")
    searched_path = []
    for prop in path_list:
        # Check if prop is trying to find an item from a list
        brackets = re.search(r"(.*)\[(\d+)\]", prop)
        if brackets:
            prop = str(brackets.group(1))
            list_index = int(brackets.group(2))
            if prop not in partial_obj:
                if list_index == 0:
                    # User is trying to create a new list with a single item
                    keep_search, partial_obj = key_not_found(
                        f"{prop}[{list_index}]", partial_obj
                    )
                else:
                    # User is trying to create a new list but provides an invalid index
                    keep_search, partial_obj = index_invalid(
                        f"{prop}[{list_index}]", partial_obj
                    )
                if not keep_search:
                    return False, partial_obj, ".".join(searched_path)
            else:
                if type(partial_obj[prop]) is not list:
                    # Wrong data type, raise an error
                    raise TypeError(
                        f"{'.'.join(searched_path)}.{prop} should be a list"
                    )
                elif len(partial_obj[prop]) == list_index:
                    # Required index is not in the list, but can be append to the end of list
                    keep_search, partial_obj = need_append(
                        f"{prop}[{list_index}]", partial_obj
                    )
                    if not keep_search:
                        return False, partial_obj, ".".join(searched_path)
                elif len(partial_obj[prop]) < list_index:
                    # Required index is not in the list, and cannot append to the end of list
                    keep_search, partial_obj = index_invalid(
                        f"{prop}[{list_index}]", partial_obj
                    )
                    if not keep_search:
                        return False, partial_obj, ".".join(searched_path)
                else:
                    partial_obj = partial_obj[prop][list_index]
        else:
            if prop not in partial_obj:
                keep_search, partial_obj = key_not_found(prop, partial_obj)
                if not keep_search:
                    return False, partial_obj, ".".join(searched_path)
            else:
                partial_obj = partial_obj[prop]
        searched_path.append(prop)
    return True, partial_obj, ".".join(path_list)


def _edit(yaml_obj: dict, path: str, value: Any):
    invalid_index_err = lambda x: IndexError(
        f"{x} is an invalid index! The list will have empty entry after insertion"
    )

    def key_not_found(prop, obj):
        brackets = re.search(r"(.*)\[(\d+)\]", prop)
        new_obj = {}
        if brackets:
            prop = str(brackets.group(1))
            obj[prop] = [new_obj]
        else:
            obj[prop] = new_obj
        return True, new_obj

    def need_append(prop, obj):
        new_obj = {}
        brackets = re.search(r"(.*)\[(\d+)\]", prop)
        prop = str(brackets.group(1))
        obj[prop].append(new_obj)
        return True, new_obj

    def index_invalid(prop, _):
        raise invalid_index_err(prop)

    path = path.split(".")
    if len(path) == 1:
        success, obj = True, yaml_obj
    else:
        before_the_last = ".".join(path[:-1])
        success, obj, _ = search_path(
            yaml_obj, before_the_last, key_not_found, need_append, index_invalid
        )

    if success:
        prop = path[-1]
        brackets = re.search(r"(.*)\[(\d+)\]", prop)
        if brackets:
            prop = str(brackets.group(1))
            list_index = str(brackets.group(2))
            if prop in obj:
                if list_index < len(obj[prop]):
                    obj[prop][list_index] = value
                elif list_index == len(obj[prop]):
                    obj[prop].append(value)
                else:
                    raise invalid_index_err(f"{prop}[{list_index}]")
            elif int(list_index) == 0:
                obj[prop] = [value]
            else:
                raise invalid_index_err(f"{prop}[{list_index}]")
        else:
            obj[path[-1]] = value
    return yaml_obj


def _conditional_edit(yaml_obj: dict, path: str, value, decide_path: str, condition):
    success, result, _ = search_path(yaml_obj, decide_path)
    if (success and result == condition) or (not success and condition is None):
        yaml_obj = _edit(yaml_obj, path, value)
    return yaml_obj


def _mapping_edit(yaml_obj: dict, path: str, value: dict, key_path: str):
    success, key, _ = search_path(yaml_obj, key_path)
    if success and key in value:
        yaml_obj = _edit(yaml_obj, path, value[key])
    return yaml_obj
