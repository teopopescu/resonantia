# ------------------------------------------------------------------------------
# RDS PostgreSQL
# ------------------------------------------------------------------------------
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-${var.environment}-db-subnet"
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "Allow PostgreSQL access from ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL from ECS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  # RDS does not initiate egress in normal operation (M2 in audit) —
  # but the AWS docs recommend leaving an egress rule for engine ops
  # like enhanced-monitoring to CloudWatch. Scope to the VPC CIDR
  # rather than the world.
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-rds-sg"
  }
}

resource "aws_db_instance" "main" {
  identifier     = "${var.project_name}-${var.environment}-db"
  engine         = "postgres"
  engine_version = "16"
  instance_class = var.db_instance_class

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true
  # Customer-managed KMS key for storage at rest (B4 in audit).
  kms_key_id = aws_kms_key.main.arn

  db_name  = "resonantia"
  username = var.db_username
  # Bootstrap-only: Terraform sets the password from the variable on
  # creation; rotation thereafter happens through Secrets Manager and
  # the `manage_master_user_password` flow (followup PR). The current
  # `password` setter is the one place tfvars still touches the DB.
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  # Multi-AZ standby in a different AZ — automatic failover (B3 in audit).
  multi_az            = true
  publicly_accessible = false

  # 30-day retention (M10 in audit) — was 7.
  backup_retention_period = 30
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"
  # Performance Insights is the cheapest observability win (M11/M20).
  performance_insights_enabled    = true
  performance_insights_kms_key_id = aws_kms_key.main.arn

  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.project_name}-${var.environment}-final-snapshot"

  deletion_protection = true

  # The `password` value is bootstrap-only — Secrets Manager is the
  # source of truth thereafter. Ignoring changes here prevents
  # `terraform plan` from showing drift after a SM rotation. Followup
  # PR: switch to `manage_master_user_password = true` so RDS rotates
  # natively and `password` can be removed entirely.
  lifecycle {
    ignore_changes = [password]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-db"
  }
}
