provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = "FleetPulse"
      ManagedBy = "Terraform"
    }
  }
}
