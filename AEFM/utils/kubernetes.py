import os, json
from time import sleep
from kubernetes import utils, config, client
from .logger import log

config.load_kube_config()


def deploy_by_yaml(
    folder: str,
    wait: bool = False,
    namespace: str = None,
    timeout: int = 300,
):
    """Deploy all YAMLs under certain ``folder``.

    Args:
        folder (str): Path to the Folder.
        wait (bool, optional): Should the program wait for deployment finished?
        Need to specify ``namespace`` if set to True. Defaults to False.
        namespace (str, optional): Where to monitor deployments, need to be spec
        ified if ``wait`` is set to True. Defaults to None.
        timeout (int, optional): Timeout of wait, units in seconds. Defaults to
        300.

    Raises:
        BaseException: Raise when ``namespace`` is not specified but ``wait`` is
        set to True.
    """
    api_client = client.ApiClient()
    for file in [
        x for x in os.listdir(folder) if x[-5:] == ".yaml" or x[-4:] == ".yml"
    ]:
        utils.create_from_yaml(api_client, f"{folder}/{file}")
    if wait:
        if namespace is None:
            raise BaseException("No namespace spcified")
        wait_deployment(namespace, timeout)


def delete_by_name(name: str, namespace: str, wait: bool = False, timeout: int = 300):
    api_client = client.AppsV1Api()
    try:
        api_client.delete_namespaced_deployment(name, namespace)
    except client.ApiException as e:
        if e.status != 404:
            raise e
    if wait:
        wait_deletion(namespace, timeout)


def delete_by_yaml(
    folder: str,
    wait: bool = False,
    namespace: str = None,
    timeout: int = 300,
):
    """Delete kubernetes components by YAMLs under certain ``folder``.

    Args:
        folder (str): Path to the Folder.
        wait (bool, optional): Should the program wait for deletion finished?
        Need to specify ``namespace`` if set to True. Defaults to False.
        namespace (str, optional): Where to monitor deployments, need to be spec
        ified if ``wait`` is set to True. Defaults to None.
        timeout (int, optional): Timeout of wait, units in seconds. Defaults to
        300.

    Raises:
        BaseException: Raise when ``namespace`` is not specified but ``wait`` is
        set to True.
    """
    # TODO: Need to find a better way to delete kubernetes components.
    os.system(f"kubectl delete -Rf {folder} >/dev/null")
    if wait:
        if namespace is None:
            raise BaseException("No namespace spcified")
        wait_deletion(namespace, timeout)


def _wait_core(namespace: str, timeout: int, wait_type: str, condition):
    api = client.CoreV1Api()
    used_time = 0
    finished_flag = False
    log.info(f"Waiting for {wait_type} finished...")
    while used_time < timeout and not finished_flag:
        sleep(5)
        if used_time % 60 == 0 and used_time != 0:
            log.info(f"{used_time} seconds passed")
        api_resp = api.list_namespaced_pod(namespace, _preload_content=False)
        resp_data = json.loads(api_resp.read().decode("utf-8"))["items"]
        finished_flag, unfinished_pods = condition(resp_data)
        if len(unfinished_pods) > 5:
            log.info(f"{len(unfinished_pods)} pods unfinished", update=True)
        elif len(unfinished_pods) != 0:
            log.info(f"Unfinished Pods: {', '.join(unfinished_pods)}", update=True)
        used_time += 5
    if not finished_flag:
        log.warn(f"{wait_type} waiting timeout!")
    else:
        log.info(f"{wait_type} finished! Used time: {used_time}s")


def wait_deployment(namespace: str, timeout: int):
    """Waiting for deployment finished in ``namespace``.

    Args:
        namespace (str): Where to monitor pods.
        timeout (int): How long should the program wait.
    """

    def condition(resp_data):
        unfinished_pods = []
        finished_flag = True
        for pod in resp_data:
            pod_finished_flag = True
            if pod["status"]["phase"] != "Running":
                finished_flag = False
                pod_finished_flag = False
            else:
                for container in pod["status"]["containerStatuses"]:
                    if not container["ready"]:
                        finished_flag = False
                        pod_finished_flag = False
            if not pod_finished_flag:
                unfinished_pods.append(pod["metadata"]["name"])
        return finished_flag, unfinished_pods

    _wait_core(namespace, timeout, "deployment", condition)


def wait_deletion(namespace: str, timeout: int):
    """Waiting for deletion finished in ``namespace``.

    Args:
        namespace (str): Where to monitor pods.
        timeout (int): How long should the program wait.
    """

    def condition(resp_data):
        unfinished_pods = [
            x["metadata"]["name"]
            for x in resp_data
            if "deletionTimestamp" in x["metadata"]
        ]
        finished_flag = len(unfinished_pods) == 0
        return finished_flag, unfinished_pods

    _wait_core(namespace, timeout, "deletion", condition)


def wait_all(namespace: str, timeout: int):
    """Waiting for both deletion and deployment finished in ``namespace``.

    Args:
        namespace (str): Where to monitor pods.
        timeout (int): How long should the program wait.
    """

    def condition(resp_data):
        unfinished_pods = [
            x["metadata"]["name"]
            for x in resp_data
            if "deletionTimestamp" in x["metadata"]
        ]
        finished_flag = len(unfinished_pods) == 0
        for pod in resp_data:
            pod_finished_flag = True
            if pod["status"]["phase"] != "Running":
                finished_flag = False
                pod_finished_flag = False
            else:
                for container in pod["status"]["containerStatuses"]:
                    if not container["ready"]:
                        finished_flag = False
                        pod_finished_flag = False
            if not pod_finished_flag:
                unfinished_pods.append(pod["metadata"]["name"])
        unfinished_pods = list(set(unfinished_pods))
        return finished_flag, unfinished_pods

    _wait_core(namespace, timeout, "deployment and deletion", condition)
