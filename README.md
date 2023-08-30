## Introduction
AEFM is an ***A***utomatic ***E***xperiment ***F***ramework for ***M***icroservice, it provides a basic configuration that helps you to profiling basic information of microservices, and also the programmable interface to extend its usage.

AEFM treat every experiment as a lifecycle, through the lifecycle, it will trigger different events. Users can customize different event handlers to achieve different objectives.

The basic events of a lifecycle are as follows:
* Start Experiment
* Init Environment
* Start Single Test Case
* Start Data Collection
* \[Customized Events to Handle Test Case Ends\]
* End Experiment

## Components
AEFM relies on different components to perform efficiently and correctly.

### Manager
Manager is the highest level component that used to manage whole experiment. It provides events handling, globally data accessing and component registration. You can customize your experiment workflow, register new events, or replace default components with the help of manager object. You can also extend the class and create your customized manager.

### Deployer
Deployer is used to manage kubernetes resources such as pod, deployments, etc. We manage theses resources based on YAML files, which can help users to detect which part is incorrect more efficient by directly look at YAML files.

### Workload Generator
Workload generator is used to provide pressure to applications. By default, we use [wrk](https://github.com/giltene/wrk2) as workload generator, which can generate HTTP requests. You can also use other workload generating tools, as they provides the required API.

### Data Collector
Data collector will collect data from different data sources, and save them as files. By default, we use Jaeger to collect traces data, Prometheus to collect hardware data and rely on output of wrk to collect throughput data. You can use other data sources by writing your own collectors, as they follow the collector interface, they can be set as component and let manager to involve it.

### Interference Generator
Interference generator generates CPU, memory capacity/bandwidth and network bandwidth interferences by default. User can also customized their own interference generator to generates other types of intererence.