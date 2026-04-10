variable "cluster_name" {}
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
