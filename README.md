## Introduction
AEFM is an ***A***utomatic ***E***xperiment ***F***ramework for ***M***icroservice, it provides a basic configuration that helps you to profiling basic information of microservices, and also the programmable interface to extend its usage.

AEFM treat every experiment as a lifecycle, through the lifecycle, it will trigger different events. Users can customize different event handlers to achieve different objectives.

The basic events of a lifecycle are as follows:
* Start Experiment (`start_experiment`)
  * Registration of components / data
* Init Environment (`init_environment`)
  * Initialization of MS application
* \[Customized Events to Handle Test Case Starts \] (`start_$TEST_CASE_NAME`)
  * **Notes**: Before any test case handler events, `curretn_test_case` is set to `manager.data`
* Start Single Test Case (`start_single_test_case`)
  * Workload should be generated here
* Start Data Collection (`start_data_collection`)
  * Collect data asynchronously
* End Experiment (`end_experiment`)
  * Waiting for data collector
  * Remove interference

## Out-of-box usage
AEFM provides out-of-box commands, you only need a little of configuration.

### Prerequisite
* Kubernetes cluster: At least 4 nodes (1 master + 3 slave), each of slave nodes has at least 8 CPU Cores + 32 GB RAM, slave nodes should be homogeneous.
* Prometheus: We recommand installing prometheus from helm with the following command:
  ```bash
  helm install monitor prometheus-community/kube-prometheus-stack --version 39.11.0 -n monitor
  ```
  The corresponding service of prometheus should be set as `NodePort`, the AEFM uses it to fetch hardware data.
* wrk2: Check [here](https://github.com/giltene/wrk2)
* Some other dependencies (required by [DeathStarBench](https://github.com/delimitrou/DeathStarBench/blob/master/socialNetwork/README.md)):
  ```bash
  apt-get install -y libssl-dev libz-dev luarocks
  luarocks install luasocket
  ```
* If you are using the default image of AEFM, you also need to put config files on all of worker nodes, check *Commands* > *download* part for more information.

### Init app
By running the following command, AEFM will create init files in current directory.
```bash
python -m AEFM init
```

You can also init into another directory with following command:
```bash
python -m AEFM init -d my_first_app
```

After initialization, the target directory will contain following files:
```
target_dir
├─handlers.py
├─main.py
└─sample_configs.yaml
```
* `handlers.py` provides default handlers, you may edit them to match your requirement.
* `main.py` is the entrance file of experiment, to run the experiment, use:
  ```bash
  python main.py
  ```
  By editing the `configs.CONFIG_FILE_PATH`, you can use different config file.
* `sample_configs.yaml` is an sample config file. Please read comments inside to understand usage of each value.

### Auto configuration

AEFM provides a command that can help you quickly generate configuration file, try the following command:
```bash
python -m AEFM auto-config
```

The program will check specification of your cluster and help you to set config file.

## Components
AEFM relies on different components to perform efficiently and correctly.

### Manager
Manager is the highest level component that used to manage whole experiment. It provides events handling, globally data accessing and component registration. You can customize your experiment workflow, register new events, or replace default components with the help of manager object. You can also extend the class and create your customized manager.

### Deployer
Deployer is used to manage kubernetes resources such as pod, deployments, etc. We manage theses resources based on YAML files, which can help users to detect which part is incorrect more efficient by directly look at YAML files.

### Workload Generator
Workload generator is used to provide pressure to applications. By default, we use [wrk](https://github.com/giltene/wrk2) as workload generator, which can generate HTTP requests. You can also use other workload generating tools, as they provides the required API.

By default, the workload generator provides test scripts of all applications & services, they are listed below, change `test_cases.workload.script` to use them:
* Social Network:
  * Compose Post: `$MODULE_DEFAULT/hotel/compose-post.lua`
  * ReadHomeTimeline: `$MODULE_DEFAULT/hotel/read-home-timeline.lua`
  * ReadUserTimeline: `$MODULE_DEFAULT/hotel/read-user-timeline.lua`
  * Mixed Workload: `$MODULE_DEFAULT/hotel/mixed-workload.lua`
* Hotel Reservation:
  * Login: `$MODULE_DEFAULT/hotel/login.lua`
  * Recommendation: `$MODULE_DEFAULT/hotel/recommendation.lua`
  * Search: `$MODULE_DEFAULT/hotel/search.lua`
  * Reservation: `$MODULE_DEFAULT/hotel/reserve.lua`
  * Mixed Workload: `$MODULE_DEFAULT/hotel/mixed-workload_type_1.lua`
* Media Microservices:
  * Compose Review: `$MODULE_DEFAULT/media/compose-review.lua`
* Train Ticket:
  * Query: `$MODULE_DEFAULT/train/query.lua`

### Data Collector
Data collector will collect data from different data sources, and save them as files. By default, we use Jaeger to collect traces data, Prometheus to collect hardware data and rely on output of wrk to collect throughput data. You can use other data sources by writing your own collectors, as they follow the collector interface, they can be set as component and let manager to involve it.

### Interference Generator
Interference generator generates CPU, memory capacity/bandwidth and network bandwidth interferences by default. User can also customized their own interference generator to generates other types of intererence. For CPU and memory capacity/bandwidth interference, we use a [modified version](https://github.com/Nick-LCY/iBench) of [iBench](https://github.com/stanford-mast/iBench). For network bandwidth interference, we use [IPerf3](https://hub.docker.com/r/networkstatic/iperf3) to generate.

## Commands
Below listed out the available commands of the AEFM, try them by typing:
```bash
python -m AEFM ${command}
```
### init
```bash
python -m AEFM init
```
Initialize the application. Generates minimum required files to run the experiment.

### download
```bash
python -m AEFM get-file
```
Get files, including:
* DeathStarBench Configs: Config files that needed to be mount on DeathStarBench applications. By default, it should be unzipped and placed at `/root/social` and `/root/media`.

* Deployment YAMLs: YAML files that used to deploy DeathStarBench and TrainTicket applications. If you need to modify them, download them, modify them and then change the path of `file_paths.yaml_repo` to them.

### auto-config
```bash
python -m AEFM auto-config
```
Automatically detect your kubernetes environment and specification of physical machines, suggest a basic config file.