#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Build, push, and deploy the Text Intelligence Agent to Cloud Run
# =============================================================================
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh
#
# Prerequisites:
#   - gcloud CLI installed and authenticated (`gcloud auth login`)
#   - Docker installed
#   - A GCP project with billing enabled
#   - APIs enabled: Cloud Run, Artifact Registry, IAM
# =============================================================================

set -euo pipefail

# ----------- Configuration (edit these) -----------
PROJECT_ID="$ adk-agent-492603"
REGION="${REGION:-us-central1}"
SERVICE_NAME="text-intelligence-agent"
REPO_NAME="adk-agents"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.0-flash}"
# --------------------------------------------------

echo "🚀  Deploying ${SERVICE_NAME} to Cloud Run"
echo "    Project : ${PROJECT_ID}"
echo "    Region  : ${REGION}"
echo "    Image   : ${IMAGE_NAME}"
echo ""

# 1. Set active project
gcloud config set project "${PROJECT_ID}"

# 2. Enable required APIs
echo "⚙️   Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  --project="${PROJECT_ID}"

# 3. Create Artifact Registry repository (idempotent)
echo "📦  Setting up Artifact Registry..."
gcloud artifacts repositories describe "${REPO_NAME}" \
  --location="${REGION}" --project="${PROJECT_ID}" 2>/dev/null \
|| gcloud artifacts repositories create "${REPO_NAME}" \
  --repository-format=docker \
  --location="${REGION}" \
  --description="ADK agent container images" \
  --project="${PROJECT_ID}"

# 4. Configure Docker auth
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# 5. Build and push image
echo "🐳  Building Docker image..."
docker build --platform linux/amd64 -t "${IMAGE_NAME}:latest" .

echo "⬆️   Pushing image to Artifact Registry..."
docker push "${IMAGE_NAME}:latest"

# 6. Create a dedicated service account for Cloud Run
SA_NAME="${SERVICE_NAME}-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🔐  Configuring service account ${SA_EMAIL}..."
gcloud iam service-accounts describe "${SA_EMAIL}" \
  --project="${PROJECT_ID}" 2>/dev/null \
|| gcloud iam service-accounts create "${SA_NAME}" \
  --display-name="Text Intelligence Agent SA" \
  --project="${PROJECT_ID}"

# Grant Vertex AI / Gemini access
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/aiplatform.user" \
  --condition=None --quiet

# 7. Deploy to Cloud Run
echo "☁️   Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE_NAME}:latest" \
  --region="${REGION}" \
  --platform=managed \
  --service-account="${SA_EMAIL}" \
  --set-env-vars="GEMINI_MODEL=${GEMINI_MODEL},GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --timeout=60 \
  --concurrency=80 \
  --no-allow-unauthenticated \
  --project="${PROJECT_ID}"

# 8. Retrieve the service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)")

echo ""
echo "✅  Deployment complete!"
echo "    Service URL : ${SERVICE_URL}"
echo ""
echo "📝  To call the agent (authenticated):"
echo ""
echo "    TOKEN=\$(gcloud auth print-identity-token)"
echo "    curl -X POST ${SERVICE_URL}/run \\"
echo "      -H \"Authorization: Bearer \$TOKEN\" \\"
echo "      -H \"Content-Type: application/json\" \\"
echo "      -d '{\"message\": \"Summarize in bullets: AI is transforming every industry...\"}'"
echo ""

# 9. (Optional) Allow public access — REMOVE for production
# gcloud run services add-iam-policy-binding "${SERVICE_NAME}" \
#   --region="${REGION}" \
#   --member="allUsers" \
#   --role="roles/run.invoker"
