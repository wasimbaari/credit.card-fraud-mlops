resource "aws_ecr_repository" "training_repo" {
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
