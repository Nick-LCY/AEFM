from time import time
import requests
from requests import Response
from typing import Literal


class PromFetcher:
    """Middleware that used to communicate with prometheus."""

    def __init__(self, host: str, namespace: str) -> None:
        """Middleware that used to communicate with prometheus.

        Args:
            host (str): Where to connect prometheus. e.g. http://1.2.3.4:9090
            namespace (str): Which namespace should prometheus focuses on.
        """
        self.host = host
        self.namespace = namespace

    def fetch(
        self,
        query: str,
        query_type: Literal["range", "point"],
        step: int = None,
        start_time: float = None,
        end_time: float = None,
        time: float = None,
    ) -> Response:
        """Basic method that fetch data from prometheus.

        Args:
            query (str): PromQL in string.
            query_type (Literal[&quot;range&quot;, &quot;point&quot;]): Two type
            s of prometheus query, ``range`` will return series of data in speci
            fic time range, while ``point`` will return data at exact timestamp.
            step (int, optional): Step, a.k.a. monitor interval, check documenta
            tion of prometheus. Defaults to None.
            start_time (float, optional): Start time timestamp of range query ty
            pe, unit in second. Defaults to None.
            end_time (float, optional): End time timestamp of range query type.
            Defaults to None.
            time (float, optional): Timestamp of point query type, unit in secon
            d. Defaults to None.

        Returns:
            Response: Query response.
        """
        request_data = {
            "query": query,
        }
        if query_type == "range":
            request_data["step"] = step
            request_data["start"] = start_time
            request_data["end"] = end_time
        elif query_type == "point":
            request_data["time"] = time
        url_suffix = {"range": "query_range", "point": "query"}[query_type]
        res = requests.get(f"{self.host}/api/v1/{url_suffix}", params=request_data)
        return res

    def fetch_cpu_usage(
        self,
        deployments: list[str],
        start_time: float,
        end_time: float,
        step: int = 1,
    ) -> Response:
        """Fetch maximum CPU usage in a range of time.

        Args:
            deployments (list[str]): Microservices that needs to be collected.
            start_time (float): Start time timestamp, units in second.
            end_time (float): End time timestamp, units in second.
            step (int, optional): a.k.a. Monitor interval, check prometheus docu
            mentation for more information. Defaults to 1.

        Returns:
            Response: Query response.
        """
        constraint = (
            f'namespace="{self.namespace}", '
            f'container!="POD", '
            f'container!="", '
            f'pod=~"{".*|".join(deployments)}.*"'
        )
        query = (
            f"sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{{{constraint}}}) by (container, pod)/"
            f'sum(kube_pod_container_resource_limits{{{constraint}, resource="cpu"}}) by (container, pod) * 100'
        )
        return self.fetch(
            query, "range", step=step, start_time=start_time, end_time=end_time
        )

    def fetch_mem_usage(
        self,
        deployments: list[str],
        start_time: float,
        end_time: float,
        step: int = 1,
    ) -> Response:
        """Fetch maximum memory usage in a range of time.

        Args:
            deployments (list[str]): Microservices that needs to be collected.
            start_time (float): Start time timestamp, units in second.
            end_time (float): End time timestamp, units in second.
            step (int, optional): a.k.a. Monitor interval, check prometheus docu
            mentation for more information. Defaults to 1.

        Returns:
            Response: Query response.
        """
        constraint = (
            f'container!= "", '
            f'container!="POD", '
            f'namespace="{self.namespace}", '
            f'pod=~"{".*|".join(deployments)}.*"'
        )
        query = (
            f"sum(node_namespace_pod_container:container_memory_working_set_bytes{{{constraint}}}) by (pod) / "
            f'sum(kube_pod_container_resource_limits{{{constraint}, resource="memory"}}) by (pod) * 100'
        )
        return self.fetch(
            query, "range", step=step, start_time=start_time, end_time=end_time
        )

    def fetch_node_mem_usage(self, nodes: list[str]) -> Response:
        """Get current node (physical machine) memory usage.

        Args:
            nodes (list[str]): A list of node names (or IPs) need to be collecte
            d.

        Returns:
            Response: Query response.
        """
        query = f'instance:node_memory_utilisation:ratio{{instance=~"{".*|".join(nodes)}.*"}}'
        return self.fetch(query, "point", time=time())

    def fetch_node_cpu_usage(self, nodes: list[str]) -> Response:
        """Get current node (physical machine) CPU usage.

        Args:
            nodes (list[str]): A list of node names (or IPs) need to be collecte
            d.

        Returns:
            Response: Query response.
        """
        query = (
            f'instance:node_cpu_utilisation:rate1m{{instance=~"{".*|".join(nodes)}.*"}}'
        )
        return self.fetch(query, "point", time=time())

    def fetch_node_cpu_aloc(self, nodes: list[str]) -> Response:
        """Get allocated node (physical machine) CPU resources.

        Args:
            nodes (list[str]): A list of node names (or IPs) need to be collecte
            d.

        Returns:
            Response: Query response.
        """
        query = f'sum(kube_pod_container_resource_limits_cpu_cores{{node=~"{"|".join(nodes)}"}}) by (node)'
        return self.fetch(query, "point", time=time())

    def fetch_node_mem_aloc(self, nodes: list[str]) -> Response:
        """Get allocated node (physical machine) memory resources.

        Args:
            nodes (list[str]): A list of node names (or IPs) need to be collecte
            d.

        Returns:
            Response: Query response.
        """
        query = f'sum(kube_pod_container_resource_limits_memory_bytes{{node=~"{"|".join(nodes)}"}}) by (node) / 1024 / 1024'
        return self.fetch(query, "point", time=time())
