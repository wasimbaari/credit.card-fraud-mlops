import os
from pathlib import Path

def automate_infra():
    print("🚀 Initiating Cloud Infrastructure Automation (Terraform)...")
    base_dir = Path("fraud-mlops-project")
    tf_dir = base_dir / "infra" / "terraform"
    
    # 1. Create Module Directories
    modules = ["vpc", "eks", "ecr", "iam"]
    for mod in modules:
        (tf_dir / mod).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created Terraform module directory: infra/terraform/{mod}")

    # ==========================================
    # TERRAFORM FILE CONTENTS
    # ==========================================

    # 1. Root variables.tf
    variables_tf = """variable "region" {
  description = "AWS Region"
  type        = string
  default     = "ap-south-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "fraud-mlops-cluster"
}
"""

    # 2. Root main.tf
    main_tf = """terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

module "vpc" {
  source = "./vpc"
}

module "eks" {
  source          = "./eks"
  cluster_name    = var.cluster_name
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
}

module "ecr" {
  source = "./ecr"
}
"""

    # 3. VPC Module (vpc/main.tf)
    vpc_tf = """module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "fraud-mlops-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["ap-south-1a", "ap-south-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true

  public_subnet_tags = {
    "kubernetes.io/cluster/fraud-mlops-cluster" = "shared"
    "kubernetes.io/role/elb"                      = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/cluster/fraud-mlops-cluster" = "shared"
    "kubernetes.io/role/internal-elb"             = "1"
  }
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "private_subnets" {
  value = module.vpc.private_subnets
}
"""

    # 4. EKS Module (eks/main.tf)
    # Using t3.large instances because Kubeflow and ML workloads require decent memory
    eks_tf = """variable "cluster_name" {}
variable "vpc_id" {}
variable "private_subnets" { type = list(string) }

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.29"

  vpc_id                         = var.vpc_id
  subnet_ids                     = var.private_subnets
  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    ml_nodes = {
      min_size     = 2
      max_size     = 5
      desired_size = 2

      instance_types = ["t3.large"]
      capacity_type  = "ON_DEMAND"
      
      labels = {
        workload = "mlops"
      }
    }
  }
}
"""

    # 5. ECR Module (ecr/main.tf)
    ecr_tf = """resource "aws_ecr_repository" "training_repo" {
  name                 = "fraud-training"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "inference_repo" {
  name                 = "fraud-inference"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

output "training_repository_url" {
  value = aws_ecr_repository.training_repo.repository_url
}

output "inference_repository_url" {
  value = aws_ecr_repository.inference_repo.repository_url
}
"""

    # ==========================================
    # WRITE FILES
    # ==========================================
    files_to_write = {
        tf_dir / "variables.tf": variables_tf,
        tf_dir / "main.tf": main_tf,
        tf_dir / "vpc" / "main.tf": vpc_tf,
        tf_dir / "eks" / "main.tf": eks_tf,
        tf_dir / "ecr" / "main.tf": ecr_tf,
    }

    for filepath, content in files_to_write.items():
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Generated Terraform file: {filepath}")

    print("\n🎉 Infrastructure Automation Complete!")
    print("Next steps:")
    print("1. cd fraud-mlops-project/infra/terraform")
    print("2. terraform init")
    print("3. terraform apply -auto-approve")

if __name__ == "__main__":
    automate_infra()