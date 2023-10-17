from kubernetes import config, client
from ..utils.kubernetes_YAMLs import search_path
import re

config.load_kube_config()


def get_nodes():
    api_client = client.CoreV1Api()
    resp_data = api_client.list_node().to_dict()["items"]
    nodes = [
        {
            "ip": node["status"]["addresses"][0]["address"],
            "name": node["metadata"]["name"],
            "cpu": node["status"]["capacity"]["cpu"],
            "memory": node["status"]["capacity"]["memory"],
        }
        for node in resp_data
        if "node-role.kubernetes.io/control-plane" not in node["metadata"]["labels"]
    ]
    return nodes


def update(yaml_obj, path: str, value):
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

