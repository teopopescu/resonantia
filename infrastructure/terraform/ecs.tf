# ------------------------------------------------------------------------------
# ECS Cluster
# ------------------------------------------------------------------------------
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cluster"
  }
}

# ------------------------------------------------------------------------------
# Security Group for ECS Tasks
# ------------------------------------------------------------------------------
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-${var.environment}-ecs-tasks-sg"
  description = "Allow traffic for ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-tasks-sg"
  }
}

# ------------------------------------------------------------------------------
# CloudWatch Log Groups
# ------------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project_name}-${var.environment}/backend"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.main.arn

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-logs"
  }
}

resource "aws_cloudwatch_log_group" "temporal_worker" {
  name              = "/ecs/${var.project_name}-${var.environment}/temporal-worker"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.main.arn

  tags = {
    Name = "${var.project_name}-${var.environment}-temporal-worker-logs"
  }
}

# ------------------------------------------------------------------------------
# Task Definition — Backend
# ------------------------------------------------------------------------------
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-${var.environment}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.container_cpu
  memory                   = var.container_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = "${aws_ecr_repository.backend.repository_url}:latest"
      essential = true

      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]

      # Non-sensitive configuration only. Every credential is loaded
      # from Secrets Manager via the `secrets` block below (B1 in audit).
      environment = [
        { name = "DB_HOST", value = aws_db_instance.main.address },
        { name = "DB_PORT", value = tostring(aws_db_instance.main.port) },
        { name = "DB_NAME", value = aws_db_instance.main.db_name },
        { name = "DB_USERNAME", value = var.db_username },
        { name = "REDIS_HOST", value = aws_elasticache_replication_group.main.primary_endpoint_address },
        { name = "REDIS_PORT", value = tostring(aws_elasticache_replication_group.main.port) },
        { name = "TEMPORAL_HOST", value = "temporal.${var.project_name}.local:7233" },
        { name = "S3_BUCKET_NAME", value = aws_s3_bucket.uploads.id },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "ENVIRONMENT", value = var.environment },
      ]

      secrets = [
        { name = "DB_PASSWORD", valueFrom = aws_secretsmanager_secret.db_password.arn },
        { name = "OPENAI_API_KEY", valueFrom = aws_secretsmanager_secret.openai_api_key.arn },
        { name = "CLERK_SECRET_KEY", valueFrom = aws_secretsmanager_secret.clerk_secret_key.arn },
        { name = "LANGFUSE_PUBLIC_KEY", valueFrom = aws_secretsmanager_secret.langfuse_public_key.arn },
        { name = "LANGFUSE_SECRET_KEY", valueFrom = aws_secretsmanager_secret.langfuse_secret_key.arn },
        { name = "REDIS_AUTH_TOKEN", valueFrom = aws_secretsmanager_secret.redis_auth.arn },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.backend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "backend"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-task"
  }
}

# ------------------------------------------------------------------------------
# Task Definition — Temporal Worker
# ------------------------------------------------------------------------------
resource "aws_ecs_task_definition" "temporal_worker" {
  family                   = "${var.project_name}-${var.environment}-temporal-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.container_cpu
  memory                   = var.container_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "temporal-worker"
      image     = "${aws_ecr_repository.temporal_worker.repository_url}:latest"
      essential = true

      environment = [
        { name = "DB_HOST", value = aws_db_instance.main.address },
        { name = "DB_PORT", value = tostring(aws_db_instance.main.port) },
        { name = "DB_NAME", value = aws_db_instance.main.db_name },
        { name = "DB_USERNAME", value = var.db_username },
        { name = "REDIS_HOST", value = aws_elasticache_replication_group.main.primary_endpoint_address },
        { name = "REDIS_PORT", value = tostring(aws_elasticache_replication_group.main.port) },
        { name = "TEMPORAL_HOST", value = "temporal.${var.project_name}.local:7233" },
        { name = "S3_BUCKET_NAME", value = aws_s3_bucket.uploads.id },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "ENVIRONMENT", value = var.environment },
      ]

      secrets = [
        { name = "DB_PASSWORD", valueFrom = aws_secretsmanager_secret.db_password.arn },
        { name = "OPENAI_API_KEY", valueFrom = aws_secretsmanager_secret.openai_api_key.arn },
        { name = "CLERK_SECRET_KEY", valueFrom = aws_secretsmanager_secret.clerk_secret_key.arn },
        { name = "LANGFUSE_PUBLIC_KEY", valueFrom = aws_secretsmanager_secret.langfuse_public_key.arn },
        { name = "LANGFUSE_SECRET_KEY", valueFrom = aws_secretsmanager_secret.langfuse_secret_key.arn },
        { name = "REDIS_AUTH_TOKEN", valueFrom = aws_secretsmanager_secret.redis_auth.arn },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.temporal_worker.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "temporal-worker"
        }
      }
    }
  ])

  tags = {
    Name = "${var.project_name}-${var.environment}-temporal-worker-task"
  }
}

# ------------------------------------------------------------------------------
# ECS Service — Backend
# ------------------------------------------------------------------------------
resource "aws_ecs_service" "backend" {
  name            = "${var.project_name}-${var.environment}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  # Two minimum so a single AZ outage or rolling deploy does not zero
  # the service (M23 in audit). Auto-scaling on top of this is a
  # separate Wave-2 add via aws_appautoscaling_target.
  desired_count = 2
  launch_type   = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  # Wait for the HTTPS listener to exist before placing tasks behind
  # it (the HTTP listener now only redirects).
  depends_on = [aws_lb_listener.https]

  lifecycle {
    ignore_changes = [desired_count]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-service"
  }
}

# ------------------------------------------------------------------------------
# ECS Service — Temporal Worker
# ------------------------------------------------------------------------------
resource "aws_ecs_service" "temporal_worker" {
  name            = "${var.project_name}-${var.environment}-temporal-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.temporal_worker.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  lifecycle {
    ignore_changes = [desired_count]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-temporal-worker-service"
  }
}
