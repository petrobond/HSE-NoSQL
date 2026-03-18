# YC Infrastructure (Terraform)

This module creates:
- VPC network with two subnets in different zones
- security group for SSH and MongoDB inside VPC
- Managed MongoDB sharded cluster
- VM for Python CLI and load testing

## Prerequisites

- Terraform 1.6+
- Yandex Cloud CLI authenticated
- IAM token (`yc iam create-token`)

## Usage

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# fill values
terraform init
terraform plan
terraform apply
```

## Notes

- For production-like HA, increase host count per shard and add multiple mongoinfra hosts.
- Security group currently allows SSH and MongoDB only inside VPC ranges; adjust inbound access if needed.

