#!/usr/bin/env bash
# Build, push to ECR, and force-redeploy the ECS service.
# Usage: ./deploy.sh
# Prerequisites: AWS CLI configured (profile prasad-okas), Docker running, terraform outputs applied.

set -euo pipefail

REGION="ap-south-1"
AWS_PROFILE="prasad-okas"
TF_DIR="$(cd "$(dirname "$0")/../okas/terraform" 2>/dev/null || cd "$(dirname "$0")/../../okas/terraform" 2>/dev/null || echo "")"

# Read ECR / cluster / service from Terraform outputs (or set manually)
if [[ -n "$TF_DIR" && -f "$TF_DIR/terraform.tfstate" ]]; then
  ECR_URL=$(cd "$TF_DIR" && terraform output -raw ecr_repository_url 2>/dev/null)
  CLUSTER=$(cd "$TF_DIR" && terraform output -raw ecs_cluster_name 2>/dev/null)
  SERVICE=$(cd "$TF_DIR" && terraform output -raw ecs_service_name 2>/dev/null)
else
  # Fallback: set manually
  ECR_URL="${ECR_URL:-367597043295.dkr.ecr.ap-south-1.amazonaws.com/okas-cloud-backend}"
  CLUSTER="${CLUSTER:-okas-dev-dev-cluster}"
  SERVICE="${SERVICE:-okas-dev-api}"
fi

echo "▸ ECR:     $ECR_URL"
echo "▸ Cluster: $CLUSTER"
echo "▸ Service: $SERVICE"

# 1. ECR login
aws ecr get-login-password --region "$REGION" --profile "$AWS_PROFILE" \
  | docker login --username AWS --password-stdin "$ECR_URL"

# 2. Build
docker build --platform linux/amd64 -t okas-cloud-backend:latest .

# 3. Tag + push
docker tag okas-cloud-backend:latest "$ECR_URL:latest"
docker push "$ECR_URL:latest"

# 4. Force new deployment (ECS pulls :latest)
aws ecs update-service \
  --cluster "$CLUSTER" \
  --service "$SERVICE" \
  --force-new-deployment \
  --region "$REGION" \
  --profile "$AWS_PROFILE" \
  --query 'service.deployments[0].status' \
  --output text

echo ""
echo "✓ Deployment triggered. Getting task public IP in ~30s..."
sleep 30

TASK_ARN=$(aws ecs list-tasks --cluster "$CLUSTER" --region "$REGION" --profile "$AWS_PROFILE" \
  --query 'taskArns[0]' --output text)

ENI=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK_ARN" \
  --region "$REGION" --profile "$AWS_PROFILE" \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
  --output text)

PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids "$ENI" \
  --region "$REGION" --profile "$AWS_PROFILE" \
  --query 'NetworkInterfaces[0].Association.PublicIp' --output text)

echo ""
echo "✓ API is live at: http://$PUBLIC_IP:3000"
echo "  Health check:   http://$PUBLIC_IP:3000/health"
