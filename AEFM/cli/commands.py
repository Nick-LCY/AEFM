import os, shutil, click, yaml
from .messages import *
from .utils import update
from ..utils.files import create_folder


@click.command()
@click.option("-d", "--dir", default=".")
def init(dir):
    ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
    TEMPLATE_DIR = os.path.join(ROOT_DIR, "templates")
    if dir != ".":
        if os.path.exists(dir):
            print("The directory already exists.")
            exit(1)
        create_folder(dir)
    else:
        dir = os.getcwd()
    for file in ["handlers.py", "main.py", "sample_configs.yaml"]:
        shutil.copyfile(os.path.join(TEMPLATE_DIR, file), os.path.join(dir, file))


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
        case "media":
            from .config_template import MEDIA_TEMPLATE as template
        case "train":
            from .config_template import TRAIN_TEMPLATE as template

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
        if len(node_obj["roles"]) != 0:
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

    exp_name = click.prompt(EXPERIMENT_NAME_MSG, type=click.STRING)

    config_yaml = yaml.load(template, Loader=yaml.CLoader)
    config_yaml = update(config_yaml, "prometheus_host", prom_host)
    config_yaml = update(config_yaml, "nodes", nodes_in_config)
    config_yaml = update(
        config_yaml, "test_cases.interferences.mem_capacity.range", mem_infs
    )
    config_yaml = update(config_yaml, "test_cases.interferences.cpu.range", cpu_infs)
    config_yaml = update(config_yaml, "file_paths.collector_data", f"data/{exp_name}")
    config_yaml = update(config_yaml, "file_paths.log", f"log/{exp_name}.log")
    config_yaml = update(
        config_yaml, "file_paths.wrk_output_path", f"tmp/wrk_{exp_name}"
    )

    yaml.Dumper.ignore_aliases = lambda *_: True
    with open(f"{exp_name}.yaml", "w") as file:
        yaml.dump(config_yaml, file, default_flow_style=False)

    click.echo(
        f"Config file is saved at {exp_name}.yaml, you may need to change config file path in main.py."
    )
