HOTEL_TEMPLATE = """
file_paths:
  collector_data: data/hotel
  log: log/hotel.log
  yaml_repo: $MODULE_DEFAULT/hotel_reservation
  wrk_output_path: tmp/wrk
app: hotel
port: 0
replicas:
  frontend: 4
  reservation: 4
  search: 3
  rate: 2
  profile: 2
  geo: 2
namespace: hotel-reserv
app_img: nicklin9907/aefm:hotel-1.0
duration: 40
jaeger_host: http://localhost:30095
jaeger_entrance: frontend
nodes:
pod_spec:
  cpu_size: 0.1
  mem_size: 100Mi
test_cases:
  orders:
  - workload
  - rounds
  - mem_capacity
  - cpu
  rounds:
    min: 1
    max: 3
    step: 1
  workload:
    configs:
      threads: 5
      connections: 10
      rate: 20
      script: $MODULE_DEFAULT/hotel-reservation/search.lua
      url: http://localhost:30096
    range:
      min: 20
      max: 200
      step: 20
  interferences:
    mem_capacity:
      configs:
        cpu_size: 0.01
        mem_size: 4Gi
      range:
    cpu:
      configs:
        cpu_size: 1
        mem_size: 200Mi
      range:
"""
SOCIAL_TEMPLATE = """
file_paths:
  collector_data: data/social
  log: log/social.log
  yaml_repo: $MODULE_DEFAULT/social_network
  wrk_output_path: tmp/wrk
app: social
port: 30628
replicas:
  user-timeline-service: 4
  home-timeline-service: 4
  post-storage-service: 4
namespace: social-network
app_img: nicklin9907/aefm:social-1.1
duration: 40
jaeger_host: http://localhost:30094
jaeger_entrance: nginx-web-server
nodes:
pod_spec:
  cpu_size: 0.1
  mem_size: 100Mi
test_cases:
  orders:
  - workload
  - rounds
  - mem_capacity
  - cpu
  rounds:
    min: 1
    max: 3
    step: 1
  workload:
    configs:
      threads: 5
      connections: 10
      rate: 20
      script: $MODULE_DEFAULT/social-network/read-home-timeline.lua
      url: http://localhost:30628
    range:
      min: 20
      max: 200
      step: 20
  interferences:
    mem_capacity:
      configs:
        cpu_size: 0.01
        mem_size: 4Gi
      range:
    cpu:
      configs:
        cpu_size: 1
        mem_size: 200Mi
      range:
"""