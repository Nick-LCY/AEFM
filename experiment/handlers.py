from .events import register
from . import manager
from deployer import BaseDeployer, DeployerInterface
from workload_generator.wrk import (
    WrkConfig,
    WrkWorkloadGenerator,
    WorkloadGeneratorInterface,
)


@register(event="start_experiment")
def start_experiment_handler():
    configs = load_configs()
    manager.data.set("configs", configs)
    manager.components.set("deployer", BaseDeployer(configs))
    wrk_config = WrkConfig(configs)
    manager.components.set("workload_generator", WrkWorkloadGenerator(wrk_config))
    data_collector()
    inf_generator()
    configs()
    timer()
    file_preparation()


@register(event="init_environment")
def init_environment_handler():
    configs = manager.data.get("configs")
    deployer = manager.components.get("deployer")
    assert isinstance(deployer, DeployerInterface)
    deployer.restart(configs["app"], configs["port"])
    deployer.reload(configs["replicas"])


@register(event="generate_test_cases_handler")
def generate_test_cases_handler():
    manager.data.set("test_cases", generate_test_cases())


@register(event="start_single_test_case")
def start_single_test_case_handler():
    test_case = manager.data.get("current_test_case")
    workload_generator = manager.components.get("workload_generator")
    assert isinstance(workload_generator, WorkloadGeneratorInterface)
    workload_generator.run(test_case["workload"])


@register(event="start_data_collection")
def start_data_collection_handler():
    test_case = manager.data.get("current_test_case")
    collect_data(test_case)


@register(event="update_environment")
def update_environment_handler():
    generate_inf()
    deployer = manager.components.get("deployer")
    assert isinstance(deployer, DeployerInterface)
    deployer.reload(manager.data.get("configs")["replicas"])

@register(event="end_experiment")
def end_experiment_handler():
    save_file()
