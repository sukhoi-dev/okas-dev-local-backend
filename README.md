# okas-cloud-backend

Node.js / Express REST API for the OKAS platform. Deployed to AWS ECS Fargate (`okas-dev-cluster`).

## Stack

| Layer | Tech |
|-------|------|
| Runtime | Node.js 18 |
| Framework | Express 4 |
| DB | MySQL 8 (AWS RDS, `okascloud`) |
| Container | Docker → AWS ECR → ECS Fargate |
| Infra | Terraform (see `../okas/terraform/ecs.tf`) |

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/projects` | List all active projects (with owner, manager, subscription) |
| `POST` | `/api/projects` | Create a new project + homeowner primary contact |
| `GET` | `/api/app-users` | List SI staff (for manager dropdown) |
| `GET` | `/api/homeowners` | List homeowners (for owner dropdown) |
| `GET` | `/api/organizations` | List organizations |

### POST /api/projects — request body

```json
{
  "name": "Project Name",
  "serial_number": "202036",
  "project_type": "residential",
  "address": "123 Main Street",
  "city": "Delhi",
  "state": "Delhi",
  "pincode": "110001",
  "notes": "Landmark",
  "organization_id": 1,
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
# 1. Install deps
npm install

# 2. Copy env
cp .env.example .env
# Edit .env — set DB_PASSWORD to okasdev password

# 3. Seed dev data (once, after schema.sql is loaded)
mysql -h 127.0.0.1 -P 3307 -u okasdev -p okascloud < db/seed.sql

# 4. Start server
npm run dev    # nodemon — auto-restarts on changes
# or
npm start
```

Server runs at `http://localhost:3000`.

## Deploy to ECS Fargate

### First-time setup (run once)

```bash
# 1. Store DB password in SSM
aws ssm put-parameter \
  --name /okas-dev/db/okasdev_password \
  --value "<okasdev_password>" \
  --type SecureString \
  --region ap-south-1 \
  --profile prasad-okas

# 2. Apply Terraform (adds ECR + ECS to the existing infra)
cd ../okas/terraform
./run.sh apply

# 3. Note the ECR URL from output
terraform output ecr_repository_url
```

### Deploy / redeploy

```bash
./deploy.sh
```

This builds the Docker image, pushes to ECR, and force-redeploys the ECS service. Prints the live public IP at the end.

### Get current API public IP

```bash
# From terraform/ directory
terraform output get_api_url_command
# Then run the printed command, or:
./deploy.sh  # prints IP after deploy
```

> **Note:** The ECS task public IP changes on task restart (no ALB in dev). Update `REACT_APP_API_BASE_URL` in the frontend `.env.production` and redeploy Amplify when the IP changes.

## Postman collection

Import `OKAS_API.postman_collection.json`. Set the `base_url` variable to `http://localhost:3000` for local or `http://<task-ip>:3000` for cloud.
