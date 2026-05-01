# Resonantia Infrastructure

Terraform configuration for deploying the Resonantia backend on AWS.

The frontend deploys separately on Vercel and is not managed by this Terraform configuration.

## Architecture

- **VPC** with public/private subnets across 2 AZs
- **ECS Fargate** running backend API and Temporal worker containers
- **ALB** for load balancing and SSL termination
- **RDS PostgreSQL 16** for persistent storage
- **ElastiCache Redis 7** for caching
- **ECR** for Docker image storage
- **S3** for file uploads (microscopy images, plate data, etc.)

## Prerequisites

1. [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5.0
2. AWS CLI configured with credentials (`aws configure`)
3. Docker for building container images

## Deployment

```bash
cd infrastructure/terraform

# 1. Copy and fill in secrets
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your actual values

# 2. Initialize Terraform
terraform init

# 3. Review the plan
terraform plan

# 4. Apply
terraform apply
```

## Pushing Docker Images to ECR

After `terraform apply`, get the ECR URLs from the outputs:

```bash
# Authenticate Docker with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(terraform output -raw ecr_backend_url | cut -d'/' -f1)

# Build and push backend
cd ../../backend
docker build -t resonantia-backend .
docker tag resonantia-backend:latest $(terraform output -raw ecr_backend_url):latest
docker push $(terraform output -raw ecr_backend_url):latest

# Build and push temporal worker
docker build -f Dockerfile.worker -t resonantia-temporal-worker .
docker tag resonantia-temporal-worker:latest $(terraform output -raw ecr_worker_url):latest
docker push $(terraform output -raw ecr_worker_url):latest
```

ECS services will automatically pick up new images on the next deployment or when force-updated.

## Enabling HTTPS

1. Uncomment the ACM certificate resource in `alb.tf`
2. Run `terraform apply` to create the certificate
3. Add the DNS validation CNAME record to your domain
4. Once validated, uncomment the HTTPS listener and switch the HTTP listener to redirect
5. Run `terraform apply` again

## Enabling Remote State

1. Create an S3 bucket and DynamoDB table for state locking
2. Uncomment the `backend "s3"` block in `main.tf`
3. Run `terraform init` to migrate state

## Costs

With the default configuration (db.t3.micro, cache.t3.micro, single Fargate task), expect roughly $50-80/month. The NAT gateway adds ~$32/month. For development, consider using a VPC endpoint or deploying in public subnets instead.
