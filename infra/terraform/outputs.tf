output "network_id" {
  value       = yandex_vpc_network.main.id
  description = "VPC network ID"
}

output "app_vm_external_ip" {
  value       = yandex_compute_instance.app_vm.network_interface[0].nat_ip_address
  description = "Public IP of application/load test VM"
}

output "mongodb_cluster_id" {
  value       = yandex_mdb_mongodb_cluster.university.id
  description = "Managed MongoDB cluster ID"
}

