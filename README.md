# 🤖 Text Intelligence Agent — ADK + Gemini on Cloud Run

A production-ready AI agent built with **Google ADK** and **Gemini**, deployed as a serverless container on **Cloud Run**. The agent performs two clearly defined tasks:

1. **Text Summarization** — concise, detailed, or bullet-point summaries
2. **Sentiment Classification** — positive / negative / neutral with explanation

---

## Project Structure

```
adk-agent/
├── agent.py          # ADK Agent definition with tools
├── main.py           # FastAPI HTTP server (Cloud Run entry point)
├── requirements.txt  # Python dependencies
├── Dockerfile        # Multi-stage container build
├── deploy.sh         # One-command Cloud Run deployment
└── README.md
```

---

## Architecture

```
Client (HTTP POST)
      │
      ▼
 Cloud Run Service
 ┌─────────────────────────────────┐
 │  FastAPI  (main.py)             │
 │  POST /run                      │
 │       │                         │
 │       ▼                         │
 │  ADK Runner                     │
 │  ┌──────────────────────────┐   │
 │  │  root_agent  (agent.py)  │   │
 │  │  model: gemini-2.0-flash │   │
 │  │  tools:                  │   │
 │  │   • summarize_text()     │   │
 │  │   • classify_sentiment() │   │
 │  └──────────┬───────────────┘   │
 └─────────────┼───────────────────┘
               │ Gemini API
               ▼
        Google AI / Vertex AI
```

---

## Quick Start (Local)

```bash
# 1. Clone / navigate to project folder
cd adk-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export GOOGLE_API_KEY="your-gemini-api-key"         # or use Vertex AI ADC
export GEMINI_MODEL="gemini-2.0-flash"

# 4. Run locally
uvicorn main:app --reload --port 8080

# 5. Test
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"message": "Summarize in bullets: The James Webb Space Telescope has revolutionized our understanding of the early universe, capturing images of galaxies that formed just hundreds of millions of years after the Big Bang."}'
```

---

## Deploy to Cloud Run

```bash
# Set your project
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"

# Deploy (builds image, pushes to Artifact Registry, deploys Cloud Run)
chmod +x deploy.sh
./deploy.sh
```

The script will:
- Enable required GCP APIs
- Create an Artifact Registry repo
- Build and push a multi-arch Docker image
- Create a dedicated service account with least-privilege IAM
- Deploy to Cloud Run with secure (no public unauthenticated) access

---

## API Reference

### `POST /run`

**Request:**
```json
{
  "message": "Summarize this in bullet points: ...",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "session_id": "optional-session-id",
  "response": "• Key point one\n• Key point two\n...",
  "status": "success"
}
```

### `GET /health`
Returns `{"status": "ok"}` — used by Cloud Run health checks.

---

## Example Requests

**Summarization (bullets):**
```bash
curl -X POST $SERVICE_URL/run \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"message": "Summarize in bullet points: Climate change refers to long-term shifts in temperatures and weather patterns..."}'
```

**Sentiment Analysis:**
```bash
curl -X POST $SERVICE_URL/run \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the sentiment of this review: The product exceeded all my expectations. Absolutely love it!"}'
```

**Detailed Summary:**
```bash
curl -X POST $SERVICE_URL/run \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"message": "Give me a detailed summary: [paste your article here]"}'
```

---

## Cleanup (Avoid Charges)

```bash
# Delete Cloud Run service
gcloud run services delete text-intelligence-agent --region=us-central1

# Delete Artifact Registry repo
gcloud artifacts repositories delete adk-agents --location=us-central1

# Delete service account
gcloud iam service-accounts delete text-intelligence-agent-sa@$PROJECT_ID.iam.gserviceaccount.com
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8080` | HTTP port (injected by Cloud Run) |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model to use |
| `GOOGLE_CLOUD_PROJECT` | — | GCP project ID |
| `GOOGLE_API_KEY` | — | Gemini API key (local dev only) |
