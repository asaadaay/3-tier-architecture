vpc_config = {
    "cidr": "10.0.0.0/20"
}


subnets_config = [
    {"name": "public", "type": "PUBLIC"},
    {"name": "app-private", "type": "PRIVATE_WITH_NAT"},
    {"name": "data-private", "type": "PRIVATE_ISOLATED"},
]

rds_config = {
    "allocated-storage": 100,
    "instance-type": "db.t4g.micro",
    "delete-automated-backups": True
}

ecs_task_def_config = {
    "cpu": 256,
    "memory_limit_mib": 512,
    "container-port": 80,
    "image-registry": "public.ecr.aws/docker/library/httpd:latest"
}
