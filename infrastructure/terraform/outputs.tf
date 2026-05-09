output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.main.endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint (with TLS + AUTH)"
  value       = "${aws_elasticache_replication_group.main.primary_endpoint_address}:${aws_elasticache_replication_group.main.port}"
}

output "kms_key_arn" {
  description = "Customer-managed KMS key used by RDS, S3, ElastiCache, Secrets Manager"
  value       = aws_kms_key.main.arn
}

output "acm_validation_records" {
  description = "DNS records to add to your DNS provider so the ACM certificate validates. Empty when you passed your own acm_certificate_arn."
  value = (
    length(aws_acm_certificate.main) > 0
    ? [for o in aws_acm_certificate.main[0].domain_validation_options : {
      name  = o.resource_record_name
      type  = o.resource_record_type
      value = o.resource_record_value
    }]
    : []
  )
}

output "secrets_arns" {
  description = "ARNs of every Secrets Manager entry referenced by ECS"
  value = {
    db_password         = aws_secretsmanager_secret.db_password.arn
    openai_api_key      = aws_secretsmanager_secret.openai_api_key.arn
    clerk_secret_key    = aws_secretsmanager_secret.clerk_secret_key.arn
    langfuse_public_key = aws_secretsmanager_secret.langfuse_public_key.arn
    langfuse_secret_key = aws_secretsmanager_secret.langfuse_secret_key.arn
    redis_auth          = aws_secretsmanager_secret.redis_auth.arn
  }
  sensitive = true
}

output "ecr_backend_url" {
  description = "ECR repository URL for backend image"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_worker_url" {
  description = "ECR repository URL for temporal worker image"
  value       = aws_ecr_repository.temporal_worker.repository_url
}

output "s3_bucket_name" {
  description = "S3 bucket name for file uploads"
  value       = aws_s3_bucket.uploads.id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}
