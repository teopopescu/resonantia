# ------------------------------------------------------------------------------
# ElastiCache Redis
# ------------------------------------------------------------------------------
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-redis-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-${var.environment}-redis-subnet"
  }
}

resource "aws_security_group" "redis" {
  name        = "${var.project_name}-${var.environment}-redis-sg"
  description = "Allow Redis access from ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Redis from ECS"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  # M3 in audit — scope egress to the VPC CIDR, not the world.
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-redis-sg"
  }
}

# ------------------------------------------------------------------------------
# ElastiCache replication group (replaces single-node aws_elasticache_cluster).
#
# Why replication group, not cluster:
#   - automatic_failover_enabled requires a replication group.
#   - at_rest_encryption_enabled + transit_encryption_enabled with
#     AUTH token requires a replication group.
#   - At-rest encryption is gated by the customer-managed KMS key (B4).
# (M12 in audit.)
# ------------------------------------------------------------------------------
resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "${var.project_name}-${var.environment}-redis"
  description          = "${var.project_name} ${var.environment} Redis"
  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.redis_node_type
  parameter_group_name = "default.redis7"
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  # Primary + 1 replica in a different AZ.
  num_cache_clusters         = 2
  automatic_failover_enabled = true
  multi_az_enabled           = true

  # Encryption at rest with our CMK + in transit with AUTH token.
  at_rest_encryption_enabled = true
  kms_key_id                 = aws_kms_key.main.arn
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_auth.result

  snapshot_retention_limit = 3

  # Don't fight rotation: AUTH token rotation is managed via Secrets
  # Manager rotation (followup PR) and ignored here.
  lifecycle {
    ignore_changes = [auth_token]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-redis"
  }
}
