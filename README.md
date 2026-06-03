# okas-cloud-backend

Python / FastAPI REST API for the OKAS platform. Deployed to AWS ECS Fargate behind an ALB.

## Stack

| Layer | Tech |
|-------|------|
| Runtime | Python 3.12 (slim-bookworm, non-root) |
| Framework | FastAPI + Uvicorn |
| DB driver | PyMySQL (MySQL 8, `okascloud`) |
| Container | Docker → AWS ECR → ECS Fargate |
| Load balancer | AWS ALB (stable DNS, no IP changes) |
| Infra | Terraform (`../okas/terraform/ecs.tf`) |

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive Swagger UI (FastAPI built-in) |
| `GET` | `/api/projects` | List all active projects |
| `POST` | `/api/projects` | Create a project + homeowner primary contact |
| `GET` | `/api/app-users` | SI staff list (manager dropdown) |
| `GET` | `/api/homeowners` | Homeowner list (owner dropdown) |
| `GET` | `/api/organizations` | Organization list |

### POST /api/projects — body

```json
{
  "name": "Project Name",
  "organization_id": 1,
  "serial_number": "202036",
  "project_type": "residential",
  "address": "123 Main Street",
  "city": "Delhi",
  "state": "Delhi",
  "pincode": "110001",
  "notes": "Near Palika Bazaar",
  "project_manager_id": 1,
  "primary_contact": {
    "full_name": "Owner Name",
    "email": "owner@example.com",
    "phone": "+91-9999999999"
  }
}
```

## Local development

```bash
# 1. Create virtualenv and install deps
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure env
cp .env.example .env
# Edit .env — set DB_PASSWORD to your okasdev password

# 3. Seed dev data (once, after schema.sql is loaded into local MySQL)
mysql -h 127.0.0.1 -P 3307 -u okasdev -p okascloud < db/seed.sql

# 4. Run with auto-reload
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` — interactive Swagger UI, test all endpoints from the browser.

## Deploy to ECS Fargate

### First-time setup (run once)

```bash
# 1. Store DB password in SSM
aws ssm put-parameter \
  --name /okas-dev/db/okasdev_password \
  --value "<okasdev_password>" \
  --type SecureString \
  --region ap-south-1 --profile prasad-okas

# 2. Apply Terraform (provisions ECR, ALB, ECS cluster + service)
cd ../okas/terraform
./run.sh apply

# 3. Note the stable ALB URL
terraform output api_base_url
# → http://okas-dev-api-alb-xxxx.ap-south-1.elb.amazonaws.com
```

### Deploy / redeploy

```bash
./deploy.sh
# Builds Docker image, pushes to ECR, force-redeploys ECS service.
# Prints stable ALB URL at the end — this URL never changes.
```

### Update Amplify frontend env var (one-time after first deploy)

```bash
ALB_DNS=$(cd ../okas/terraform && terraform output -raw alb_dns_name)
aws amplify update-branch \
  --app-id d2gb37zj8vn5sg --branch-name main \
  --environment-variables "REACT_APP_API_BASE_URL=http://$ALB_DNS" \
  --region ap-south-1 --profile prasad-okas
# Then trigger a build:
aws amplify start-job --app-id d2gb37zj8vn5sg --branch-name main \
  --job-type RELEASE --region ap-south-1 --profile prasad-okas
```

## Troubleshooting

| Issue | How to investigate |
|-------|--------------------|
| API returning 5xx | `aws logs tail /ecs/okas-dev/api --follow --region ap-south-1 --profile prasad-okas` |
| Task not starting | ECS console → cluster → service → Events tab |
| DB connection refused | Check bastion tunnel is up; verify okasdev password in SSM |
| Swagger UI | `http://<alb-dns>/docs` — test requests live from browser |

## Postman collections

Import `OKAS_API.postman_collection.json`. Set `base_url` to `http://localhost:8000` (local) or the ALB DNS (cloud).
