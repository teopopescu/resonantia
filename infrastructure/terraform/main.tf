terraform {
  # Pin to the 1.5.x line — patch versions are fine, minor bumps need
  # an explicit decision (m3 in audit).
  required_version = "~> 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Remote backend (B6 in audit). Bucket + lock table are created by
  # `bootstrap/` first; see infrastructure/README.md.
  #
  # Backend config values cannot be variables, so the bucket / table /
  # region come in via -backend-config flags on `terraform init`. The
  # key is fixed per environment.
  backend "s3" {
    key     = "production/terraform.tfstate"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
