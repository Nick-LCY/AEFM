from .events import register
from . import manager
from deployer import DeployerInterface
from deployer.base import BaseDeployer
from workload_generator.wrk import (
    WrkConfig,
    WrkWorkloadGenerator,
    WorkloadGeneratorInterface,
)
from data_collector import DataCollectorInterface
from data_collector.base import BaseDataCollector
from utils.jaeger_fetcher import JaegerFetcher
from data_collector.jaeger_trace_collector import JaegerTraceCollector
from data_collector.wrk_throughput_collector import WrkThroughputCollector, WrkFetcher
from utils.prom_fetcher import PromFetcher
from data_collector.prom_hardware_collector import PromHardwareCollector


@register(event="start_experiment")
def start_experiment_handler():
    configs = load_configs()
    manager.data.set("configs", configs)
    manager.components.set("deployer", BaseDeployer(configs))
    wrk_config = WrkConfig(configs)
    manager.components.set("workload_generator", WrkWorkloadGenerator(wrk_config))
    jaeger_fetcher = JaegerFetcher(configs)
    jaeger_collector = JaegerTraceCollector(jaeger_fetcher)
    wrk_fetcher = WrkFetcher(configs)
    wrk_collector = WrkThroughputCollector(wrk_fetcher)
    prom_fetcher = PromFetcher(configs)
    prom_collector = PromHardwareCollector(prom_fetcher)
    data_collector = BaseDataCollector(
        configs, jaeger_collector, prom_collector, wrk_collector
    )
    manager.components.set("data_collector", data_collector)
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
    data_collector = manager.components.get("data_collector")
    assert isinstance(data_collector, DataCollectorInterface)
    data_collector.collect_async(test_case)


@register(event="update_environment")
def update_environment_handler():
    generate_inf()
    deployer = manager.components.get("deployer")
    assert isinstance(deployer, DeployerInterface)
    deployer.reload(manager.data.get("configs")["replicas"])


@register(event="end_experiment")
def end_experiment_handler():
    save_file()
