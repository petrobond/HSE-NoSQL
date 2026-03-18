variable "yc_token" {
  description = "Yandex Cloud IAM token"
  type        = string
  sensitive   = true
}

variable "cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "folder_id" {
  description = "Yandex Folder ID"
  type        = string
}

variable "default_zone" {
  description = "Default availability zone"
  type        = string
  default     = "ru-central1-a"
}

variable "secondary_zone" {
  description = "Secondary availability zone"
  type        = string
  default     = "ru-central1-b"
}

variable "network_cidr_a" {
  description = "CIDR for subnet A"
  type        = string
  default     = "10.10.1.0/24"
}

variable "network_cidr_b" {
  description = "CIDR for subnet B"
  type        = string
  default     = "10.10.2.0/24"
}

variable "ssh_public_key_path" {
  description = "Path to public SSH key for VM access"
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "vm_user" {
  description = "Linux user for VM metadata"
  type        = string
  default     = "ubuntu"
}

variable "mongodb_version" {
  description = "MongoDB major version"
  type        = string
  default     = "6.0"
}

variable "mongodb_db_name" {
  description = "Main database name"
  type        = string
  default     = "university"
}

variable "mongodb_username" {
  description = "MongoDB username"
  type        = string
  default     = "app_user"
}

variable "mongodb_password" {
  description = "MongoDB user password"
  type        = string
  sensitive   = true
}

