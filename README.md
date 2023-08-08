## Introduction
AEFM is an ***A***utomatic ***E***xperiment ***F***ramework for ***M***icroservice, it provides a basic configuration that helps you to profiling basic information of microservices, and also the programmable interface to extend its usage.

AEFM treat every experiment as a lifecycle, through the lifecycle, it will trigger different events. Users can customize different event handlers to achieve different objectives.

The basic events of a lifecycle are as follows:
* Start Experiment
* Init Environment
* Generate Test Cases
* Start Single Test Case
* Start Data Collection
* Update Evironment
* End Experiment