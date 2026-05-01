# ------------------------------------------------------------------------------
# ALB Security Group
# ------------------------------------------------------------------------------
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-alb-sg"
  description = "Allow HTTP/HTTPS traffic to ALB"
  vpc_id      = aws_vpc.main.id

  # HTTP open only so the listener can issue a 301 redirect to HTTPS.
  # Real application traffic flows on 443.
  ingress {
    description = "HTTP for redirect"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-alb-sg"
  }
}

# ------------------------------------------------------------------------------
# Application Load Balancer
# ------------------------------------------------------------------------------
resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = true
  drop_invalid_header_fields = true

  tags = {
    Name = "${var.project_name}-${var.environment}-alb"
  }
}

# ------------------------------------------------------------------------------
# Target Group
# ------------------------------------------------------------------------------
resource "aws_lb_target_group" "backend" {
  name        = "${var.project_name}-${var.environment}-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-tg"
  }
}

# ------------------------------------------------------------------------------
# ACM certificate (B2 in audit).
#
# Provisioned only when var.acm_certificate_arn is empty. If the user
# already has a cert (most common in real deployments — DNS validation
# is done in the user's Route53 / external DNS), they pass the ARN in
# and we skip ACM provisioning here.
# ------------------------------------------------------------------------------
resource "aws_acm_certificate" "main" {
  count = var.acm_certificate_arn == "" ? 1 : 0

  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cert"
  }
}

# A two-pass apply is required when this stack provisions the cert:
#   1. First apply creates aws_acm_certificate. The HTTPS listener is
#      gated on aws_acm_certificate_validation, which waits for DNS
#      records you must add manually (see the
#      `acm_validation_records` output). That apply will not create
#      the listener until validation passes, but everything else
#      (RDS, ECS, ALB itself) is independent and applies cleanly.
#   2. After adding the CNAMEs to your DNS provider and re-running
#      `terraform apply`, the validation completes and the HTTPS
#      listener is created.
# When the operator passes var.acm_certificate_arn (an already-validated
# cert ARN), this resource is skipped entirely and the listener comes
# up on the first apply.
resource "aws_acm_certificate_validation" "main" {
  count = var.acm_certificate_arn == "" ? 1 : 0

  certificate_arn = aws_acm_certificate.main[0].arn

  # Allow more time than the default since DNS propagation is manual.
  timeouts {
    create = "60m"
  }
}

locals {
  certificate_arn = var.acm_certificate_arn != "" ? var.acm_certificate_arn : (
    length(aws_acm_certificate_validation.main) > 0 ? aws_acm_certificate_validation.main[0].certificate_arn : ""
  )
}

# ------------------------------------------------------------------------------
# Listeners — HTTP redirects to HTTPS, HTTPS forwards to the target group.
# ------------------------------------------------------------------------------
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = local.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}
