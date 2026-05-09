# ------------------------------------------------------------------------------
# AWS Secrets Manager — replaces the plaintext environment variables in
# ECS task definitions (B1 in docs/aws-prod-readiness-audit.md).
#
# Each secret is KMS-encrypted with the customer-managed key from kms.tf.
# Tasks reference them via the `secrets` block of the container
# definition (see ecs.tf), which means:
#   - Values never appear in `aws ecs describe-task-definition`.
#   - Values never appear in CloudWatch task events.
#   - Rotation is per-secret, no task-definition revision required.
#
# Bootstrapping: the Terraform variable inputs (var.db_password,
# var.openai_api_key, etc.) seed each secret on first apply. After
# that, rotate via the Secrets Manager console or RotateSecret API and
# DO NOT update terraform.tfvars — Terraform's lifecycle below ignores
# subsequent value changes so it doesn't fight rotation.
# ------------------------------------------------------------------------------

locals {
  secrets_prefix = "${var.project_name}/${var.environment}"
}

# --- DB password ---------------------------------------------------------
resource "aws_secretsmanager_secret" "db_password" {
  name        = "${local.secrets_prefix}/db_password"
  description = "RDS master password"
  kms_key_id  = aws_kms_key.main.arn

  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# --- OpenAI / Anthropic API key ------------------------------------------
resource "aws_secretsmanager_secret" "openai_api_key" {
  name        = "${local.secrets_prefix}/openai_api_key"
  description = "LLM provider API key"
  kms_key_id  = aws_kms_key.main.arn

  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# --- Clerk secret key ----------------------------------------------------
resource "aws_secretsmanager_secret" "clerk_secret_key" {
  name        = "${local.secrets_prefix}/clerk_secret_key"
  description = "Clerk auth provider secret"
  kms_key_id  = aws_kms_key.main.arn

  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "clerk_secret_key" {
  secret_id     = aws_secretsmanager_secret.clerk_secret_key.id
  secret_string = var.clerk_secret_key

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# --- Langfuse keys -------------------------------------------------------
resource "aws_secretsmanager_secret" "langfuse_public_key" {
  name        = "${local.secrets_prefix}/langfuse_public_key"
  description = "Langfuse observability public key"
  kms_key_id  = aws_kms_key.main.arn

  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "langfuse_public_key" {
  secret_id     = aws_secretsmanager_secret.langfuse_public_key.id
  secret_string = var.langfuse_public_key

  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret" "langfuse_secret_key" {
  name        = "${local.secrets_prefix}/langfuse_secret_key"
  description = "Langfuse observability secret key"
  kms_key_id  = aws_kms_key.main.arn

  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "langfuse_secret_key" {
  secret_id     = aws_secretsmanager_secret.langfuse_secret_key.id
  secret_string = var.langfuse_secret_key

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# --- ElastiCache AUTH token ----------------------------------------------
# Generated server-side rather than via tfvars: rotation should not require
# a tfvars change. The first-apply value is created here and the secret
# row is the source of truth for ElastiCache after that.
resource "random_password" "redis_auth" {
  length  = 64
  special = false
}

resource "aws_secretsmanager_secret" "redis_auth" {
  name        = "${local.secrets_prefix}/redis_auth"
  description = "ElastiCache Redis AUTH token"
  kms_key_id  = aws_kms_key.main.arn

  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "redis_auth" {
  secret_id     = aws_secretsmanager_secret.redis_auth.id
  secret_string = random_password.redis_auth.result

  lifecycle {
    ignore_changes = [secret_string]
  }
}
