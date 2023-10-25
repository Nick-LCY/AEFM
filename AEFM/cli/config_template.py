HOTEL_TEMPLATE = """
file_paths:
  yaml_repo: $MODULE_DEFAULT/hotel
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
  - round
  - mem_capacity
  - cpu
  round:
    min: 1
    max: 3
    step: 1
  workload:
    configs:
      threads: 5
      connections: 10
      rate: 20
      script: $MODULE_DEFAULT/hotel/search.lua
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
  yaml_repo: $MODULE_DEFAULT/social
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
  - round
  - mem_capacity
  - cpu
  round:
    min: 1
    max: 3
    step: 1
  workload:
    configs:
      threads: 5
      connections: 10
      rate: 20
      script: $MODULE_DEFAULT/social/read-home-timeline.lua
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
MEDIA_TEMPLATE = """
file_paths:
  yaml_repo: $MODULE_DEFAULT/media
app: media
port: 30092
replicas:
  nginx-web-server: 5
  compose-review-service: 4
  movie-id-service: 2
namespace: media-microsvc
app_img: nicklin9907/aefm:media-1.0
duration: 40
jaeger_host: http://localhost:30093
jaeger_entrance: nginx
nodes:
pod_spec:
  cpu_size: 0.1
  mem_size: 100Mi
test_cases:
  orders:
  - workload
  - round
  - mem_capacity
  - cpu
  round:
    min: 1
    max: 3
    step: 1
  workload:
    configs:
      threads: 5
      connections: 10
      rate: 20
      script: $MODULE_DEFAULT/media/compose-review.lua
      url: http://localhost:30092
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
TRAIN_TEMPLATE = """
file_paths:
  yaml_repo: $MODULE_DEFAULT/train
app: train
port: 0
replicas:
  ts-travel-service: 3
  ts-config-service: 2
  ts-basic-service: 2
  ts-station-service: 2
namespace: train-ticket
app_img: nicklin9907/aefm:train-1.0
duration: 40
jaeger_host: http://localhost:32688
jaeger_entrance: ts-basic-service
nodes:
pod_spec:
  cpu_size: 0.2
  mem_size: 1024Mi
test_cases:
  orders:
  - workload
  - round
  - mem_capacity
  - cpu
  round:
    min: 1
    max: 3
    step: 1
  workload:
    configs:
      threads: 5
      connections: 10
      rate: 20
      script: $MODULE_DEFAULT/train/query.lua
      url: http://localhost:32677
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
