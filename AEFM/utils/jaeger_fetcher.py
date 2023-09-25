import requests
from requests import Response


class JaegerFetcher:
    """Middleware that used to communicate with jaeger."""

    def __init__(self, host: str, entrance_microservice: str) -> None:
        """Middleware that used to communicate with jaeger.

        Args:
            host (str): Where to connect jaeger. e.g. http://1.2.3.4:16686
            entrance_microservice (str): Entrance microservice of jaeger, i.e. s
            ervice option in jaeger web UI
        """
        self.url = f"{host}/api/traces"
        self.entrance_microservice = entrance_microservice

    def fetch(
        self,
        start_time: float,
        end_time: float,
        operation: str = None,
        limit: int = 1000,
    ) -> Response:
        """Basic method that fetch data from jaeger.

        Args:
            start_time (float): Start time timestamp, unit in second.
            end_time (float): End time timestamp, unit in second.
            operation (str, optional): Web UI operation option. Defaults to None.
            limit (int, optional): Web UI limits option. Defaults to 1000.

        Returns:
            Response: Query response.
        """
        request_data = {
            "start": int(start_time * 1000000),
            "end": int(end_time * 1000000),
            "limit": limit,
            "service": self.entrance_microservice,
            "tags": '{"http.status_code":"200"}',
        }
        if operation is not None:
            request_data["operation"] = operation
        req = requests.get(self.url, params=request_data)
        return req
