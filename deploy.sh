#!/usr/bin/env bash
# Build, push to ECR, and force-redeploy the ECS service.
# Usage: ./deploy.sh
# Prerequisites: AWS CLI (profile prasad-okas), Docker running, Terraform applied.

set -euo pipefail

REGION="ap-south-1"
AWS_PROFILE="prasad-okas"

# Resolve Terraform outputs
TF_DIR="$(dirname "$0")/../okas/terraform"
if [[ -f "$TF_DIR/terraform.tfstate" ]]; then
  ECR_URL=$(cd "$TF_DIR" && terraform output -raw ecr_repository_url 2>/dev/null)
  CLUSTER=$(cd "$TF_DIR" && terraform output -raw ecs_cluster_name 2>/dev/null)
  SERVICE=$(cd "$TF_DIR" && terraform output -raw ecs_service_name 2>/dev/null)
  ALB_DNS=$(cd "$TF_DIR" && terraform output -raw alb_dns_name 2>/dev/null)
else
  ECR_URL="${ECR_URL:-367597043295.dkr.ecr.ap-south-1.amazonaws.com/okas-cloud-backend}"
  CLUSTER="${CLUSTER:-okas-dev-dev-cluster}"
  SERVICE="${SERVICE:-okas-dev-api}"
  ALB_DNS=""
fi

echo "▸ ECR:     $ECR_URL"
echo "▸ Cluster: $CLUSTER / $SERVICE"

aws ecr get-login-password --region "$REGION" --profile "$AWS_PROFILE" \
  | docker login --username AWS --password-stdin "$ECR_URL"

docker build --platform linux/amd64 -t okas-cloud-backend:latest .

docker tag okas-cloud-backend:latest "$ECR_URL:latest"
docker push "$ECR_URL:latest"

aws ecs update-service \
  --cluster "$CLUSTER" \
  --service  "$SERVICE" \
  --force-new-deployment \
  --region   "$REGION" \
  --profile  "$AWS_PROFILE" \
  --query    'service.deployments[0].status' \
  --output   text

echo ""
if [[ -n "$ALB_DNS" ]]; then
  echo "✓ Deployment triggered."
  echo "  API base URL : http://$ALB_DNS"
  echo "  Health check : http://$ALB_DNS/health"
  echo "  Swagger docs : http://$ALB_DNS/docs"
  echo ""
  echo "  Set in Amplify console:"
  echo "  REACT_APP_API_BASE_URL=http://$ALB_DNS"
fi
