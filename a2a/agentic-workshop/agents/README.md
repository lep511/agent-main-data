### Posting Agent
```bash
export IMAGE_TAG="latest"
export AGENT_NAME="platform_mcp_client"
export IMAGE_NAME="posting-agent"
export IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${IMAGE_TAG}"
export SERVICE_NAME="posting-agent"
export PUBLIC_URL="https://${IMAGE_NAME}-${PROJECT_NUMBER}.${REGION}.run.app"
```

### Social Agent
```bash
export IMAGE_TAG="latest"
export AGENT_NAME="social"
export IMAGE_NAME="social-agent"
export IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${IMAGE_TAG}"
export SERVICE_NAME="social-agent"
export PUBLIC_URL="https://${IMAGE_NAME}-${PROJECT_NUMBER}.${REGION}.run.app"
```

### Comun commands

```bash
export MCP_SERVER_URL=$(gcloud run services list --platform=managed --region=us-central1 --format='value(URL)' | grep mcp-tool-server)/sse
```

```bash
gcloud builds submit . \
  --config=cloudbuild-expanded.yaml \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --substitutions=_AGENT_NAME="${AGENT_NAME}",\
_IMAGE_PATH="${IMAGE_PATH}",\
_PROJECT_ID="${PROJECT_ID}",\
_PROJECT_NUMBER="${PROJECT_NUMBER}",\
_REGION="${REGION}",\
_REPO_NAME="${REPO_NAME}",\
_SPANNER_INSTANCE_ID="${SPANNER_INSTANCE_ID}",\
_SPANNER_DATABASE_ID="${SPANNER_DATABASE_ID}",\
_MCP_SERVER_URL="${MCP_SERVER_URL}"
```

```bash
gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_PATH} \
  --platform=managed \
  --region=${REGION} \
  --set-env-vars="A2A_HOST=0.0.0.0" \
  --set-env-vars="A2A_PORT=8080" \
  --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE" \
  --set-env-vars="GOOGLE_CLOUD_LOCATION=${REGION}" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-env-vars="PUBLIC_URL=${PUBLIC_URL}" \
  --allow-unauthenticated \
  --project=${PROJECT_ID} \
  --min-instances=1
```