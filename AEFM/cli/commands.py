import os, shutil, click, yaml
from .messages import *
from .utils import update


@click.command()
@click.option("-d", "--dir", default=".")
def init(dir):
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = os.path.join(ROOT_DIR, "templates")
    if dir != ".":
        shutil.copytree(TEMPLATE_DIR, dir)
    else:
        shutil.copytree(TEMPLATE_DIR, os.getcwd())


@click.command()
def auto_config():
    from .utils import get_nodes

    app = click.prompt(
        CHOOSE_APP_MSG,
        default="hotel",
        hide_input=True,
        show_default=True,
        show_choices=True,
        type=click.Choice(APP_CHOICES),
    )
    match app:
        case "hotel":
            from .config_template import HOTEL_TEMPLATE as template
        case "social":
            from .config_template import SOCIAL_TEMPLATE as template

    nodes = get_nodes()
    if len(nodes) < 3:
        click.echo("Not enough nodes", err=True)
        exit(1)

    node_names = [x["name"] for x in nodes]
    click.echo(f"Available nodes: {', '.join(node_names)}")

    def node_check(user_input: str):
        user_selection = [x.strip() for x in user_input.split(",")]
        for node in user_selection:
            if node not in node_names:
                raise click.BadParameter(f"Invalid node name: {node}")
        return user_selection

    infra_nodes = click.prompt(CHOOSE_INFRA_MSG, value_proc=node_check)
    testbed_nodes = click.prompt(CHOOSE_TESTBED_MSG, value_proc=node_check)

    nodes_in_config = []
    for node in nodes:
        node_obj = {"name": node["name"], "ip": node["ip"], "roles": []}
        if node["name"] in infra_nodes:
            node_obj["roles"].append("infra")
        if node["name"] in testbed_nodes:
            node_obj["roles"].append("testbed")
        nodes_in_config.append(node_obj)

    prom_host = click.prompt(PROMETHEUS_HOST_MSG, default="http://localhost:9090")

    cpu_capacity = nodes[0]["cpu"]
    mem_capacity = nodes[0]["memory"]

    # At least 8 cores, 32GB?
    cpu_percentages = [0.4, 0.55, 0.7, 0.85]
    mem_percentages = [0.15, 0.35, 0.55, 0.75]

    cpu_infs = [int(int(cpu_capacity) * percentage) for percentage in cpu_percentages]
    mem_infs = [
        int(int(mem_capacity[:-2]) / 1024 / 1024 * percentage // 4)
        for percentage in mem_percentages
    ]

    config_yaml = yaml.load(template, Loader=yaml.CLoader)
    config_yaml = update(config_yaml, "prometheus_host", prom_host)
    config_yaml = update(config_yaml, "nodes", nodes_in_config)
    config_yaml = update(
        config_yaml, "test_cases.interferences.mem_capacity.range", mem_infs
    )
    config_yaml = update(config_yaml, "test_cases.interferences.cpu.range", cpu_infs)
    yaml.Dumper.ignore_aliases = lambda *_: True
    with open(f"{app}_config.yaml", "w") as file:
        yaml.dump(config_yaml, file, default_flow_style=False)
