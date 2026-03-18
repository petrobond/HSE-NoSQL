locals {
  name_prefix = "hse-nosql"
}

resource "yandex_vpc_network" "main" {
  name = "${local.name_prefix}-network"
}

resource "yandex_vpc_subnet" "subnet_a" {
  name           = "${local.name_prefix}-subnet-a"
  zone           = var.default_zone
  network_id     = yandex_vpc_network.main.id
  v4_cidr_blocks = [var.network_cidr_a]
}

resource "yandex_vpc_subnet" "subnet_b" {
  name           = "${local.name_prefix}-subnet-b"
  zone           = var.secondary_zone
  network_id     = yandex_vpc_network.main.id
  v4_cidr_blocks = [var.network_cidr_b]
}

resource "yandex_vpc_security_group" "mongodb" {
  name       = "${local.name_prefix}-mongodb-sg"
  network_id = yandex_vpc_network.main.id

  ingress {
    protocol       = "TCP"
    description    = "MongoDB from VPC only"
    v4_cidr_blocks = [var.network_cidr_a, var.network_cidr_b]
    port           = 27017
  }

  ingress {
    protocol       = "TCP"
    description    = "SSH from VPC only"
    v4_cidr_blocks = [var.network_cidr_a, var.network_cidr_b]
    port           = 22
  }

  egress {
    protocol       = "ANY"
    description    = "Allow all egress"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port      = 0
    to_port        = 65535
  }
}

resource "yandex_mdb_mongodb_cluster" "university" {
  name                = "${local.name_prefix}-mongo"
  environment         = "PRODUCTION"
  network_id          = yandex_vpc_network.main.id
  security_group_ids  = [yandex_vpc_security_group.mongodb.id]
  version             = var.mongodb_version
  sharded             = true
  deletion_protection = false

  resources_mongod {
    resource_preset_id = "s2.micro"
    disk_type_id       = "network-ssd"
    disk_size          = 20
  }

  resources_mongoinfra {
    resource_preset_id = "s2.micro"
    disk_type_id       = "network-ssd"
    disk_size          = 20
  }

  host {
    zone_id   = var.default_zone
    subnet_id = yandex_vpc_subnet.subnet_a.id
    type      = "MONGOD"
    shard_name = "rs-shard-a"
  }

  host {
    zone_id   = var.secondary_zone
    subnet_id = yandex_vpc_subnet.subnet_b.id
    type      = "MONGOD"
    shard_name = "rs-shard-b"
  }

  host {
    zone_id   = var.default_zone
    subnet_id = yandex_vpc_subnet.subnet_a.id
    type      = "MONGOINFRA"
  }

  database {
    name = var.mongodb_db_name
  }

  user {
    name     = var.mongodb_username
    password = var.mongodb_password

    permission {
      database_name = var.mongodb_db_name
      roles         = ["readWrite", "dbAdmin"]
    }
  }
}

resource "yandex_compute_instance" "app_vm" {
  name        = "${local.name_prefix}-app-vm"
  zone        = var.default_zone
  platform_id = "standard-v3"

  resources {
    cores         = 2
    memory        = 4
    core_fraction = 100
  }

  boot_disk {
    initialize_params {
      image_family = "ubuntu-2204-lts"
      size          = 30
      type          = "network-ssd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.subnet_a.id
    security_group_ids = [yandex_vpc_security_group.mongodb.id]
    nat                = true
  }

  metadata = {
    ssh-keys = "${var.vm_user}:${file(var.ssh_public_key_path)}"
  }
}

