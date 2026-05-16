# ------------------------------------------------------------------------------
# S3 Bucket for File Uploads
# ------------------------------------------------------------------------------
resource "aws_s3_bucket" "uploads" {
  bucket = "${var.project_name}-uploads-${var.environment}"

  tags = {
    Name = "${var.project_name}-uploads-${var.environment}"
  }
}

resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    apply_server_side_encryption_by_default {
      # SSE-KMS with the customer-managed key (B4 in audit). The
      # bucket key on the next line keeps per-request KMS calls down
      # so the cost stays nominal at scale.
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.main.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowECSTaskAccess"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.ecs_task.arn
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.uploads.arn,
          "${aws_s3_bucket.uploads.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_s3_bucket_cors_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = ["https://resonantia.io", "https://www.resonantia.io", "http://localhost:3000"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    id     = "expire-voice-input-audio"
    status = "Enabled"

    filter {
      prefix = "resonantia/voice/input/"
    }

    expiration {
      days = var.voice_input_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = var.voice_input_retention_days
    }
  }

  rule {
    id     = "expire-voice-output-audio"
    status = "Enabled"

    filter {
      prefix = "resonantia/voice/output/"
    }

    expiration {
      days = var.voice_output_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = var.voice_output_retention_days
    }
  }
}
