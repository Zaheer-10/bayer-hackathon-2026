#!/usr/bin/env bash
# Push Docker image to AWS ECR
# Usage: ./scripts/push-ecr.sh [AWS_REGION] [ECR_REPO_NAME]
# Example: ./scripts/push-ecr.sh us-east-1 bayer-hackathon-2026

set -e

AWS_REGION="${1:-us-east-1}"
REPO_NAME="${2:-bayer-hackathon-2026}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}"

echo "Creating ECR repository (if not exists)..."
aws ecr describe-repositories --repository-names "${REPO_NAME}" --region "${AWS_REGION}" 2>/dev/null \
  || aws ecr create-repository --repository-name "${REPO_NAME}" --region "${AWS_REGION}"

echo "Logging Docker into ECR..."
aws ecr get-login-password --region "${AWS_REGION}" | \
  docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Building image..."
docker build -t "${REPO_NAME}:${IMAGE_TAG}" .

echo "Tagging image for ECR..."
docker tag "${REPO_NAME}:${IMAGE_TAG}" "${ECR_URI}:${IMAGE_TAG}"

echo "Pushing to ECR..."
docker push "${ECR_URI}:${IMAGE_TAG}"

echo "Done. Image: ${ECR_URI}:${IMAGE_TAG}"
