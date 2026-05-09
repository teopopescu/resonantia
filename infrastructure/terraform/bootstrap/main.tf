# ------------------------------------------------------------------------------
# Bootstrap stack — creates the S3 bucket + DynamoDB table that hold the
# main stack's remote state (B6 in docs/aws-prod-readiness-audit.md).
#
# This stack uses a *local* backend on purpose: you cannot use a
# remote backend to create the resources that house the remote
# backend (chicken-and-egg). After the first apply, commit
# `bootstrap/terraform.tfstate` and treat the bucket/table as fixed
# infrastructure.
#
# Workflow:
#   cd infrastructure/terraform/bootstrap
#   terraform init
#   terraform apply -var "project_name=resonantia"
#   # ...then in the parent stack:
#   cd ..
#   terraform init -backend-config="bucket=resonantia-terraform-state" \
#                  -backend-config="dynamodb_table=resonantia-terraform-locks" \
#                  -backend-config="region=us-east-1" \
#                  -backend-config="key=production/terraform.tfstate" \
#                  -backend-config="encrypt=true"
# ------------------------------------------------------------------------------

terraform {
  required_version = "~> 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "project_name" {
  type    = string
  default = "resonantia"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

resource "aws_kms_key" "tf_state" {
  description             = "Terraform state encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "aws_kms_alias" "tf_state" {
  name          = "alias/${var.project_name}-tf-state"
  target_key_id = aws_kms_key.tf_state.key_id
}

resource "aws_s3_bucket" "tf_state" {
  bucket        = "${var.project_name}-terraform-state"
  force_destroy = false

  tags = {
    Name      = "${var.project_name}-terraform-state"
    ManagedBy = "terraform-bootstrap"
  }
}

resource "aws_s3_bucket_versioning" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.tf_state.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "tf_state" {
  bucket                  = aws_s3_bucket.tf_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "tf_state_lock" {
  name         = "${var.project_name}-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.tf_state.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name      = "${var.project_name}-terraform-locks"
    ManagedBy = "terraform-bootstrap"
  }
}

output "state_bucket" {
  value = aws_s3_bucket.tf_state.id
}

output "state_lock_table" {
  value = aws_dynamodb_table.tf_state_lock.id
}
