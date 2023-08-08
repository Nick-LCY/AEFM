class BaseExperiment:
    def __init__(self) -> None:
        pass

    def start_experiment(self):
        workload_generator()
        data_collector()
        inf_generator()
        deployer()
        configs()
        timer()
        file_preparation()

    def init_environment(self):
        full_init()
        init()

    def generate_test_cases(self):
        self.test_cases = configs().generate_test_cases()

    def start_single_test_case(self, test_case):
        generate_workload()

    def start_data_collection(self, test_case):
        collect_data()

    def update_environment(self):
        generate_inf()
        init()

    def end_experiment(self):
        save_file()

    def run(self):
        self.start_experiment()
        self.init_environment()
        self.generate_test_cases()
        for test_case in self.test_cases:
            self.start_single_test_case(test_case)
            self.start_data_collection(test_case)
            self.update_environment()
        self.end_experiment()
