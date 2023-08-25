from typing import Optional


class Node:
    """Used to record available nodes.
    """    
    def __init__(self, name: str, roles: list[str], ip: Optional[str] = None) -> None:
        """Used to record available nodes.

        Args:
            name (str): Name of node.
            roles (list[str]): e.g. testbase, infra.
            ip (Optional[str], optional): Internal IP address of node. Defaults 
            to None.
        """        
        self.name: str = name
        self.roles: list[str] = roles
        self.ip: Optional[str] = ip

    @staticmethod
    def load_from_dict(data: dict[str, str]) -> "Node":
        """Used to generate object based on config YAML.

        Args:
            data (dict[str, Union[str, float, int]]): "nodes" part of config YAML.

        Returns:
            Node: Corresponding object.
        """        
        name = data["name"]
        roles = data["roles"]
        ip = data["ip"] if "ip" in data else None
        return Node(name, roles, ip)

    def get_roles(self) -> str:
        """Get node roles.

        Returns:
            str: Node roles.
        """        
        return self.roles

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name
