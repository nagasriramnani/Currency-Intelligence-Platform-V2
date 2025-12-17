# Cloud Deployment Guide

## Currency Intelligence Platform — Cloud Run + Vercel Deployment

This guide provides **copy-paste ready** commands and configurations for deploying the Currency Intelligence Platform to production.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: GCP Project Setup](#phase-1-gcp-project-setup)
4. [Phase 2: Upload Models to GCS](#phase-2-upload-models-to-gcs)
5. [Phase 3: Build and Deploy Backend](#phase-3-build-and-deploy-backend)
6. [Phase 4: Deploy Frontend to Vercel](#phase-4-deploy-frontend-to-vercel)
7. [Environment Variables Checklist](#environment-variables-checklist)
8. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┴────────────────────┐
         │                                        │
         ▼                                        ▼
┌─────────────────┐                    ┌─────────────────────┐
│     VERCEL      │                    │    CLOUD RUN        │
│   (Next.js)     │ ───HTTPS API───▶   │    (FastAPI)        │
│                 │                    │                     │
│ Domain:         │                    │ URL:                │
│ currency.app    │                    │ *.run.app           │
└─────────────────┘                    └──────────┬──────────┘
                                                  │
                 ┌────────────────────────────────┼────────────────────────────────┐
                 │                                │                                │
                 ▼                                ▼                                ▼
        ┌────────────────┐              ┌────────────────┐              ┌────────────────┐
        │  GCS BUCKET    │              │ SECRET MANAGER │              │   SUPABASE     │
        │  (Models)      │              │  (API Keys)    │              │   (Database)   │
        │                │              │                │              │                │
        │ trained_models/│              │ SLACK_WEBHOOK  │              │ fx_rates       │
        │ *.pkl          │              │ FMP_API_KEY    │              │ forecasts      │
        │ registry.json  │              │ SUPABASE_*     │              │ alerts         │
        └────────────────┘              └────────────────┘              └────────────────┘
```

---

## Prerequisites

- Google Cloud SDK installed (`gcloud`)
- Docker installed
- Vercel CLI installed (`npm i -g vercel`)
- Trained models in `backend/trained_models/` directory
- Supabase project created

---

## Phase 1: GCP Project Setup

### Step 1.1: Login and Set Project

```bash
# Login to GCP
gcloud auth login

# Set your project (replace with your project ID)
export PROJECT_ID="currency-intelligence-prod"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    storage.googleapis.com
```

### Step 1.2: Create Service Account

```bash
# Create service account for Cloud Run
gcloud iam service-accounts create currency-api-sa \
    --display-name="Currency API Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:currency-api-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:currency-api-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 1.3: Create Artifact Registry

```bash
# Create Docker repository
gcloud artifacts repositories create currency-api \
    --repository-format=docker \
    --location=us-central1 \
    --description="Currency Intelligence Platform API images"

# Configure Docker to use Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### Step 1.4: Create GCS Bucket for Models

```bash
# Create bucket
export BUCKET_NAME="${PROJECT_ID}-models"
gsutil mb -l us-central1 gs://$BUCKET_NAME

# Set bucket to uniform access
gsutil uniformbucketlevelaccess set on gs://$BUCKET_NAME
```

### Step 1.5: Create Secrets in Secret Manager

```bash
# Create secrets (replace with actual values)
echo -n "your-slack-webhook-url" | gcloud secrets create SLACK_WEBHOOK_URL --data-file=-
echo -n "your-fmp-api-key" | gcloud secrets create FMP_API_KEY --data-file=-
echo -n "https://your-project.supabase.co" | gcloud secrets create SUPABASE_URL --data-file=-
echo -n "your-supabase-key" | gcloud secrets create SUPABASE_KEY --data-file=-

# Grant access to service account
for SECRET in SLACK_WEBHOOK_URL FMP_API_KEY SUPABASE_URL SUPABASE_KEY; do
    gcloud secrets add-iam-policy-binding $SECRET \
        --member="serviceAccount:currency-api-sa@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
done
```

---

## Phase 2: Upload Models to GCS

### Step 2.1: Upload Trained Models

```bash
# From project root
cd backend

# Upload all model files
gsutil -m cp trained_models/*.pkl gs://$BUCKET_NAME/trained_models/
gsutil -m cp trained_models/model_registry.json gs://$BUCKET_NAME/trained_models/

# Verify upload
gsutil ls gs://$BUCKET_NAME/trained_models/
```

Expected output:
```
gs://currency-intelligence-prod-models/trained_models/model_registry.json
gs://currency-intelligence-prod-models/trained_models/prophet_EUR_20251217_*.pkl
gs://currency-intelligence-prod-models/trained_models/xgboost_EUR_20251217_*.pkl
...
```

---

## Phase 3: Build and Deploy Backend

### Step 3.1: Build Docker Image

```bash
# From backend directory
cd backend

# Build for Cloud Run (linux/amd64 required)
docker build --platform linux/amd64 -t currency-api:latest .

# Tag for Artifact Registry
docker tag currency-api:latest \
    us-central1-docker.pkg.dev/$PROJECT_ID/currency-api/api:latest
```

### Step 3.2: Push to Artifact Registry

```bash
# Push image
docker push us-central1-docker.pkg.dev/$PROJECT_ID/currency-api/api:latest
```

### Step 3.3: Deploy to Cloud Run

```bash
# Deploy with all settings
gcloud run deploy currency-api \
    --image=us-central1-docker.pkg.dev/$PROJECT_ID/currency-api/api:latest \
    --region=us-central1 \
    --platform=managed \
    --allow-unauthenticated \
    --service-account=currency-api-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --memory=2Gi \
    --cpu=2 \
    --min-instances=1 \
    --max-instances=10 \
    --concurrency=80 \
    --timeout=300s \
    --set-env-vars="MODEL_BUCKET=$BUCKET_NAME,MODEL_PREFIX=trained_models/,ALLOWED_ORIGINS=https://currency-intelligence.vercel.app" \
    --set-secrets="SLACK_WEBHOOK_URL=SLACK_WEBHOOK_URL:latest,FMP_API_KEY=FMP_API_KEY:latest,SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_KEY=SUPABASE_KEY:latest"
```

### Step 3.4: Verify Deployment

```bash
# Get service URL
CLOUD_RUN_URL=$(gcloud run services describe currency-api --region=us-central1 --format='value(status.url)')
echo "Cloud Run URL: $CLOUD_RUN_URL"

# Test health endpoint
curl "$CLOUD_RUN_URL/health"
```

Expected response:
```json
{
  "status": "healthy",
  "initialized": true,
  "models_loaded": true,
  "model_count": 15,
  "model_source": "gcs",
  "cloud_run": true
}
```

---

## Phase 4: Deploy Frontend to Vercel

### Step 4.1: Configure Environment

Create `frontend/.env.production`:

```bash
NEXT_PUBLIC_API_BASE_URL=https://currency-api-XXXXX-uc.a.run.app
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### Step 4.2: Deploy to Vercel

```bash
cd frontend

# Login to Vercel
vercel login

# Deploy to production
vercel --prod

# Or link to existing project
vercel link
vercel --prod
```

### Step 4.3: Set Environment Variables in Vercel Dashboard

1. Go to [vercel.com](https://vercel.com) → Your Project → Settings → Environment Variables
2. Add:
   - `NEXT_PUBLIC_API_BASE_URL` = Your Cloud Run URL
   - `NEXT_PUBLIC_SUPABASE_URL` = Your Supabase URL
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` = Your Supabase anon key

### Step 4.4: Update Cloud Run CORS

After getting your Vercel domain:

```bash
# Update ALLOWED_ORIGINS with your actual Vercel domain
gcloud run services update currency-api \
    --region=us-central1 \
    --update-env-vars="ALLOWED_ORIGINS=https://your-app.vercel.app,https://currency-intelligence.vercel.app"
```

---

## Environment Variables Checklist

### Backend (Cloud Run)

| Variable | Description | Source |
|----------|-------------|--------|
| `PORT` | Server port | Auto-set by Cloud Run |
| `MODEL_BUCKET` | GCS bucket name | Environment variable |
| `MODEL_PREFIX` | Path in bucket | Environment variable |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | Environment variable |
| `SUPABASE_URL` | Database URL | Secret Manager |
| `SUPABASE_KEY` | Database key | Secret Manager |
| `FMP_API_KEY` | Financial Modeling Prep API | Secret Manager |
| `SLACK_WEBHOOK_URL` | Slack notifications | Secret Manager |

### Frontend (Vercel)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | Cloud Run service URL |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |

---

## Troubleshooting

### Cold Start Issues

**Symptom:** First request takes 10-30 seconds

**Solutions:**
```bash
# Set minimum instances to 1 (already done in deploy command)
gcloud run services update currency-api \
    --region=us-central1 \
    --min-instances=1
```

### 502 Bad Gateway

**Symptom:** Immediate 502 errors

**Causes & Solutions:**
1. **Container fails to start** - Check logs:
   ```bash
   gcloud run services logs read currency-api --region=us-central1 --limit=50
   ```

2. **Models missing** - Verify models in GCS:
   ```bash
   gsutil ls gs://$BUCKET_NAME/trained_models/
   ```

3. **Health check failing** - Test locally:
   ```bash
   docker run -p 8080:8080 -e PORT=8080 currency-api:latest
   curl http://localhost:8080/health
   ```

### GCS Permission Denied

**Symptom:** "403 Forbidden" when loading models

**Solution:**
```bash
# Verify service account has access
gsutil iam get gs://$BUCKET_NAME

# Grant access
gsutil iam ch \
    serviceAccount:currency-api-sa@$PROJECT_ID.iam.gserviceaccount.com:objectViewer \
    gs://$BUCKET_NAME
```

### CORS Errors

**Symptom:** "Access-Control-Allow-Origin" errors in browser

**Solution:**
```bash
# Update ALLOWED_ORIGINS with your Vercel domain
gcloud run services update currency-api \
    --region=us-central1 \
    --update-env-vars="ALLOWED_ORIGINS=https://your-app.vercel.app"
```

### Timeout on Forecasts

**Symptom:** 503 errors on forecast endpoints

**Solution:**
```bash
# Increase timeout (already set to 300s)
gcloud run services update currency-api \
    --region=us-central1 \
    --timeout=300s
```

### Missing Secrets

**Symptom:** "Secret not found" errors

**Solution:**
```bash
# List secrets
gcloud secrets list

# Verify secret version
gcloud secrets versions list SLACK_WEBHOOK_URL

# Create if missing
echo -n "value" | gcloud secrets create SECRET_NAME --data-file=-
```

### Artifact Registry Auth

**Symptom:** "unauthorized" when pushing images

**Solution:**
```bash
# Re-authenticate
gcloud auth configure-docker us-central1-docker.pkg.dev

# Verify repository exists
gcloud artifacts repositories list --location=us-central1
```

---

## Quick Reference Commands

### View Logs
```bash
gcloud run services logs read currency-api --region=us-central1 --limit=50
```

### Update Environment Variable
```bash
gcloud run services update currency-api \
    --region=us-central1 \
    --update-env-vars="KEY=value"
```

### Redeploy with New Image
```bash
docker build --platform linux/amd64 -t currency-api:latest .
docker tag currency-api:latest us-central1-docker.pkg.dev/$PROJECT_ID/currency-api/api:latest
docker push us-central1-docker.pkg.dev/$PROJECT_ID/currency-api/api:latest
gcloud run deploy currency-api --image=us-central1-docker.pkg.dev/$PROJECT_ID/currency-api/api:latest --region=us-central1
```

### Upload New Models
```bash
gsutil -m cp trained_models/*.pkl gs://$BUCKET_NAME/trained_models/
gsutil -m cp trained_models/model_registry.json gs://$BUCKET_NAME/trained_models/

# Force Cloud Run to restart and download new models
gcloud run services update currency-api --region=us-central1 --update-env-vars="MODEL_VERSION=$(date +%s)"
```

---

## Final Checklist

- [ ] GCP Project created and configured
- [ ] APIs enabled (Cloud Run, Artifact Registry, Secret Manager, Storage)
- [ ] Service account created with permissions
- [ ] GCS bucket created
- [ ] Models uploaded to GCS
- [ ] Secrets created in Secret Manager
- [ ] Docker image built and pushed
- [ ] Cloud Run service deployed
- [ ] Health endpoint returns healthy
- [ ] Vercel project configured
- [ ] Frontend environment variables set
- [ ] CORS configured for Vercel domain
- [ ] End-to-end test passed

---

*Last updated: December 2025*
