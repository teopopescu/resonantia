variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "resonantia"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "resonantia"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI / Anthropic API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "clerk_secret_key" {
  description = "Clerk secret key for authentication"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langfuse_public_key" {
  description = "Langfuse public key for observability"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langfuse_secret_key" {
  description = "Langfuse secret key for observability"
  type        = string
  sensitive   = true
  default     = ""
}

variable "domain_name" {
  description = "Domain name for the API"
  type        = string
  default     = "api.resonantia.io"
}

variable "container_cpu" {
  description = "CPU units for ECS tasks (1 vCPU = 1024)"
  type        = number
  default     = 512
}

variable "container_memory" {
  description = "Memory in MiB for ECS tasks"
  type        = number
  default     = 1024
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "acm_certificate_arn" {
  description = "ARN of an ACM certificate to use on the ALB HTTPS listener. Leave empty to provision one for var.domain_name via DNS validation (validation records must be created out-of-band)."
  type        = string
  default     = ""
}

variable "tf_state_bucket" {
  description = "S3 bucket holding Terraform remote state. Must be created out-of-band (chicken-and-egg). See infrastructure/README.md for the bootstrap step."
  type        = string
  default     = "resonantia-terraform-state"
}

variable "tf_state_lock_table" {
  description = "DynamoDB table for Terraform state locking. Must be created out-of-band. See infrastructure/README.md."
  type        = string
  default     = "resonantia-terraform-locks"
}
