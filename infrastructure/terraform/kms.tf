# ------------------------------------------------------------------------------
# Customer-managed KMS key (B4 in docs/aws-prod-readiness-audit.md)
#
# Used by:
#   - Secrets Manager (envelope-encrypts every Secret value)
#   - RDS (storage encryption)
#   - S3 (SSE-KMS on the uploads bucket)
#   - ElastiCache (at-rest + AUTH token encryption)
#   - CloudWatch log groups
#
# Why a CMK and not an AWS-managed key:
#   - We control the key policy; we can revoke access.
#   - Rotation is in our control (annual rotation enabled below).
#   - SOC 2 / pharma customer conversations require "we hold the key".
# ------------------------------------------------------------------------------

resource "aws_kms_key" "main" {
  description             = "${var.project_name}-${var.environment} customer-managed key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  multi_region            = false

  # Key policy intentionally narrow:
  #   - Root has full management (the standard pattern).
  #   - CloudWatch Logs needs an explicit policy entry (it is the one
  #     service AWS does not automatically create grants for); scoped
  #     by `kms:EncryptionContext:aws:logs:arn` to our two log groups
  #     so a different log group in the account cannot use this key.
  #   - RDS, S3, Secrets Manager, ElastiCache: NOT in the key policy.
  #     Each resource is created with `kms_key_id = aws_kms_key.main.arn`
  #     which causes the AWS service to create a single-purpose KMS
  #     grant scoped to that resource — confused-deputy-safe.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EnableRootAccountManagement"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "AllowCloudWatchLogsForOurLogGroupsOnly"
        Effect = "Allow"
        Principal = {
          Service = "logs.${var.aws_region}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey",
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/ecs/${var.project_name}-${var.environment}/*"
          }
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-cmk"
  }
}

resource "aws_kms_alias" "main" {
  name          = "alias/${var.project_name}-${var.environment}"
  target_key_id = aws_kms_key.main.key_id
}

data "aws_caller_identity" "current" {}
