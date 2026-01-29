# Terraform main configuration for Railway OS infrastructure
terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
  }
  
  backend "s3" {
    bucket         = "railway-os-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "railway-os-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "railway-os"
      ManagedBy   = "Terraform"
      CreatedAt   = formatdate("YYYY-MM-DD", timestamp())
    }
  }
}

provider "kubernetes" {
  host                   = aws_eks_cluster.main.endpoint
  cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.main.token
}

# Variables
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod"
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "availability_zones" {
  description = "Availability zones for multi-AZ deployment"
  type        = list(string)
}

variable "database_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.3"
}

variable "database_instance_class" {
  description = "RDS instance class"
  type        = string
}

variable "kubernetes_version" {
  description = "EKS cluster version"
  type        = string
  default     = "1.28"
}

# Locals for computed values
locals {
  cluster_name = "railway-os-${var.environment}"
  app_name     = "railway-os-api"
  
  environment_config = {
    dev = {
      replica_count    = 2
      db_multi_az      = false
      enable_monitoring = false
    }
    staging = {
      replica_count    = 3
      db_multi_az      = true
      enable_monitoring = true
    }
    prod = {
      replica_count    = 5
      db_multi_az      = true
      enable_monitoring = true
    }
  }
}

# VPC Configuration
module "vpc" {
  source = "./modules/networking"
  
  environment         = var.environment
  vpc_cidr            = var.vpc_cidr
  availability_zones  = var.availability_zones
  
  tags = {
    Name = "railway-os-vpc-${var.environment}"
  }
}

# RDS Database
module "database" {
  source = "./modules/database"
  
  environment              = var.environment
  vpc_security_group_ids   = [module.vpc.database_security_group_id]
  db_subnet_group_name     = module.vpc.db_subnet_group_name
  instance_class           = var.database_instance_class
  engine_version           = var.database_engine_version
  multi_az                 = local.environment_config[var.environment].db_multi_az
  allocated_storage        = var.environment == "prod" ? 100 : 50
  backup_retention_period  = var.environment == "prod" ? 30 : 7
  
  depends_on = [module.vpc]
}

# ElastiCache (Redis)
module "cache" {
  source = "./modules/cache"
  
  environment            = var.environment
  vpc_security_group_ids = [module.vpc.cache_security_group_id]
  subnet_group_name      = module.vpc.elasticache_subnet_group_name
  node_type             = var.environment == "prod" ? "cache.r7g.xlarge" : "cache.t4g.small"
  num_cache_nodes       = local.environment_config[var.environment].replica_count
  
  depends_on = [module.vpc]
}

# EKS Cluster
module "eks" {
  source = "./modules/kubernetes"
  
  cluster_name            = local.cluster_name
  kubernetes_version      = var.kubernetes_version
  vpc_id                  = module.vpc.vpc_id
  subnet_ids              = module.vpc.private_subnet_ids
  control_plane_subnet_ids = module.vpc.private_subnet_ids
  
  worker_node_config = {
    desired_size       = local.environment_config[var.environment].replica_count
    min_size          = local.environment_config[var.environment].replica_count
    max_size          = local.environment_config[var.environment].replica_count * 2
    instance_types    = ["t3.large"]
    volume_size       = 50
  }
  
  depends_on = [module.vpc]
}

# Secrets Manager (AWS Secrets Manager)
module "secrets" {
  source = "./modules/secrets"
  
  environment = var.environment
  
  secrets = {
    database_password = {
      type        = "database_password"
      length      = 32
      rotation_days = var.environment == "prod" ? 30 : 60
    }
    jwt_secret_key = {
      type        = "jwt_signing_key"
      length      = 64
      rotation_days = 90
    }
    api_key = {
      type        = "api_key"
      length      = 32
      rotation_days = var.environment == "prod" ? 60 : 90
    }
  }
}

# CloudWatch Monitoring
module "monitoring" {
  source = "./modules/monitoring"
  
  environment     = var.environment
  cluster_name    = local.cluster_name
  enable_detailed = local.environment_config[var.environment].enable_monitoring
  
  alarms = {
    error_rate_threshold     = 0.05  # 5%
    latency_p99_threshold_ms = 500
    availability_threshold   = 0.95   # 95%
  }
}

# Auto Scaling Groups
module "autoscaling" {
  source = "./modules/autoscaling"
  
  environment         = var.environment
  cluster_name        = local.cluster_name
  min_replicas        = local.environment_config[var.environment].replica_count
  max_replicas        = local.environment_config[var.environment].replica_count * 2
  target_cpu_percent  = 70
  target_memory_percent = 80
  
  depends_on = [module.eks]
}

# Outputs
output "eks_cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = local.cluster_name
}

output "rds_endpoint" {
  description = "RDS database endpoint"
  value       = module.database.db_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.cache.redis_endpoint
  sensitive   = true
}

output "secrets_manager_secret_arn" {
  description = "AWS Secrets Manager secret ARN"
  value       = module.secrets.secret_arn
}
