import os
from pathlib import Path

def automate_phase_4():
    print("🚀 Initiating Phase 4: CI Pipeline & OIDC Security...")
    base_dir = Path("fraud-mlops-project")
    github_dir = base_dir / ".github" / "workflows"
    github_dir.mkdir(parents=True, exist_ok=True)

    # 1. Define the CI/CD Pipeline YAML
    # This workflow builds the image and pushes to ECR using OIDC
    ci_yaml_content = """name: CI/CD Pipeline

on:
  push:
    branches: [ master, main ]
  pull_request:
    branches: [ master, main ]

permissions:
  id-token: write   # Required for requesting the JWT for OIDC
  contents: read    # Required for actions/checkout

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Configure AWS Credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ap-south-1

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build, Tag, and Push Training Image to ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: fraud-training
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -f docker/training.Dockerfile -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG -t $ECR_REGISTRY/$ECR_REPOSITORY:latest .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY --all-tags
"""

    # 2. Define the IAM Trust Policy for OIDC (For your reference)
    # You will need this to create the IAM role in AWS Console or Terraform
    iam_trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Federated": "arn:aws:iam::<YOUR_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": "repo:<YOUR_GITHUB_USER>/fraud-mlops-project:*"
                    }
                }
            }
        ]
    }

    # 3. Write files
    with open(github_dir / "ci.yaml", "w", encoding="utf-8") as f:
        f.write(ci_yaml_content)
    
    print(f"✅ Created: {github_dir}/ci.yaml")
    print("\n🎉 Phase 4 Automation Complete!")
    print("Next steps (Once Terraform finishes):")
    print("1. Create an IAM Role named 'GitHubAction-FraudMLOps' with the Trust Policy provided.")
    print("2. Attach 'AmazonEC2ContainerRegistryFullAccess' to that role.")
    print("3. Add the Role ARN to GitHub Secrets as 'AWS_ROLE_ARN'.")

if __name__ == "__main__":
    automate_phase_4()