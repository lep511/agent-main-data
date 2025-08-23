#!/bin/bash

# ==============================================================================
#
# InstaVibe Bootstrap - Consolidated Setup Script for InstaVibe app and DB
#
# ==============================================================================

# --- Script Configuration ---
# Stop script on any error
set -e
# Treat unset variables as an error
set -u
# Pipefail
set -o pipefail


# This function will be called when the script exits on an error.
error_handler() {
  local exit_code=$?
  echo ""
  echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  echo "❌ SCRIPT FAILED with exit code $exit_code at line: $BASH_LINENO"
  echo "The command that failed was: '$BASH_COMMAND'"
  echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  echo ""
  echo "The terminal will now pause. Press [Ctrl+C] to terminate."
  read
}
# We 'trap' the ERR signal and call our error_handler function.
trap 'error_handler' ERR
# ------------------------------------

# --- User-configurable variables ---
REPO_URL="https://github.com/GoogleCloudPlatform/instavibe-bootstrap.git"
REPO_DIR_NAME="instavibe-bootstrap"
SPANNER_INSTANCE_ID="instavibe-graph-instance"
SPANNER_DATABASE_ID="graphdb"
ARTIFACT_REPO_NAME="introveally-repo"
GOOGLE_CLOUD_LOCATION="us-central1"
MAPS_API_KEY_DISPLAY_NAME="Maps Platform API Key - InstaVibe"
IMAGE_NAME="instavibe-webapp"
SERVICE_NAME="instavibe"

# --- Helper Functions ---
log() {
  echo "✅  $1"
}

check_command() {
  if ! command -v "$1" &>/dev/null; then
    echo "❌ Error: Command not found: '$1'. Please install it and make sure it's in your PATH."
    exit 1 # This will trigger the error trap
  fi
}

# --- Pre-flight Checks ---
log "Running pre-flight checks..."
check_command "gcloud"
check_command "git"
check_command "python"
check_command "pip"
check_command "jq"
check_command "curl" # Added for downloading files
log "All required tools are installed."

log "Checking gcloud authentication status..."
if ! gcloud auth print-access-token -q &>/dev/null; then
  echo "❌ Error: You are not authenticated with gcloud. Please run 'gcloud auth login' and 'gcloud auth application-default login'."
  exit 1
fi
log "gcloud is authenticated."


# --- Step 1: Clone Source Repository ---
log "--- Step 1: Cloning source repository ---"
# Use ~ to ensure we are in the home directory before creating/checking the repo dir
REPO_FULL_PATH="$HOME/$REPO_DIR_NAME"
if [ -d "$REPO_FULL_PATH" ]; then
    log "Repository directory '$REPO_FULL_PATH' already exists. Skipping clone."
else
    log "Cloning $REPO_URL into $REPO_FULL_PATH..."
    git clone "$REPO_URL" "$REPO_FULL_PATH"
    log "Repository cloned successfully."
fi


# --- Step 2: Set Google Cloud Project ID ---
log "--- Step 2: Setting Google Cloud Project ID ---"
PROJECT_FILE="$HOME/project_id.txt"

if [ -f "$PROJECT_FILE" ]; then
    PROJECT_ID=$(cat "$PROJECT_FILE")
    log "Found existing project ID in $PROJECT_FILE: $PROJECT_ID"
    read -p "Do you want to use this project ID? (y/n): " use_existing
    if [[ "$use_existing" != "y" ]]; then
        read -p "Please enter your new Google Cloud project ID: " PROJECT_ID
    fi
else
    read -p "Please enter your Google Cloud project ID: " PROJECT_ID
fi

if [[ -z "$PROJECT_ID" ]]; then
  echo "❌ Error: No project ID was entered."
  exit 1
fi

echo "$PROJECT_ID" > "$PROJECT_FILE"
log "Successfully saved project ID '$PROJECT_ID' to $PROJECT_FILE"
gcloud config set project "$PROJECT_ID" --quiet
log "Set gcloud active project to '$PROJECT_ID'."



# --- Step 3: Discovering and setting environment variables ---
log "--- Step 3: Discovering and setting environment variables ---"
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
SERVICE_ACCOUNT_NAME=$(gcloud compute project-info describe --format="value(defaultServiceAccount)")
log "Project ID and Service Account discovered."


# --- Step 4: Enable Google Cloud APIs ---
log "--- Step 4: Enabling required Google Cloud APIs (this may take a few minutes) ---"
gcloud services enable  run.googleapis.com \
                        cloudfunctions.googleapis.com \
                        cloudbuild.googleapis.com \
                        artifactregistry.googleapis.com \
                        spanner.googleapis.com \
                        apikeys.googleapis.com \
                        iam.googleapis.com \
                        compute.googleapis.com \
                        aiplatform.googleapis.com \
                        cloudresourcemanager.googleapis.com \
                        maps-backend.googleapis.com
log "All necessary APIs enabled."


# --- Step 5: Grant IAM Permissions ---
log "--- Step 5: Granting IAM Roles to Service Account: $SERVICE_ACCOUNT_NAME ---"
declare -a ROLES=(
  "roles/spanner.admin" "roles/spanner.databaseUser" "roles/artifactregistry.admin"
  "roles/run.admin" "roles/iam.serviceAccountUser" "roles/serviceusage.serviceUsageAdmin"
  "roles/aiplatform.user" "roles/logging.logWriter" "roles/logging.viewer"
)

for ROLE in "${ROLES[@]}"; do
  log "Assigning role: $ROLE"
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME" \
    --role="$ROLE" \
    --condition=None > /dev/null
done
log "All project-level IAM roles have been assigned."


# --- Step 6: Create Artifact Registry Repository ---
log "--- Step 6: Creating Artifact Registry Repository: $ARTIFACT_REPO_NAME ---"
if gcloud artifacts repositories describe "$ARTIFACT_REPO_NAME" --location="$GOOGLE_CLOUD_LOCATION" &>/dev/null; then
  log "Artifact Registry repository '$ARTIFACT_REPO_NAME' already exists. Skipping."
else
  gcloud artifacts repositories create "$ARTIFACT_REPO_NAME" \
    --repository-format=docker \
    --location="$GOOGLE_CLOUD_LOCATION" \
    --description="Docker repository for InstaVibe workshop"
  log "Successfully created Artifact Registry repository."
fi


# --- Step 7: Create Spanner Instance and Database ---
log "--- Step 7: Creating Spanner Instance & Database ---"
if gcloud spanner instances describe "$SPANNER_INSTANCE_ID" &>/dev/null; then
  log "Spanner instance '$SPANNER_INSTANCE_ID' already exists. Skipping."
else
  gcloud spanner instances create "$SPANNER_INSTANCE_ID" \
    --config=regional-us-central1 \
    --description="GraphDB Instance InstaVibe" \
    --processing-units=100 \
    --edition=ENTERPRISE
  log "Successfully created Spanner instance."
fi

if gcloud spanner databases describe "$SPANNER_DATABASE_ID" --instance="$SPANNER_INSTANCE_ID" &>/dev/null; then
  log "Spanner database '$SPANNER_DATABASE_ID' already exists. Skipping."
else
  gcloud spanner databases create "$SPANNER_DATABASE_ID" \
    --instance="$SPANNER_INSTANCE_ID" \
    --database-dialect=GOOGLE_STANDARD_SQL
  log "Successfully created Spanner database."
fi


# --- Step 8: Grant Database-Level IAM Role ---
log "--- Step 8: Granting Spanner database access to the service account ---"
gcloud spanner databases add-iam-policy-binding "$SPANNER_DATABASE_ID" \
  --instance="$SPANNER_INSTANCE_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT_NAME" \
  --role="roles/spanner.databaseUser" \
  --project="$PROJECT_ID"
log "Successfully granted database-level access."


# --- Step 9: Create and Restrict Google Maps API Key ---
log "--- Step 9: Creating and Restricting Google Maps API Key ---"
EXISTING_KEY_NAME=$(gcloud services api-keys list --filter="displayName='$MAPS_API_KEY_DISPLAY_NAME'" --format="value(name)")

if [ ! -z "$EXISTING_KEY_NAME" ]; then
    log "An API key named '$MAPS_API_KEY_DISPLAY_NAME' already exists. Deleting it to create a new one."
    gcloud services api-keys delete "$EXISTING_KEY_NAME" --quiet
    log "Old key deleted."
fi

log "Creating a new API key named '$MAPS_API_KEY_DISPLAY_NAME'..."
API_OPERATION_JSON=$(gcloud services api-keys create \
  --display-name="$MAPS_API_KEY_DISPLAY_NAME" \
  --format=json)

KEY_NAME=$(echo "$API_OPERATION_JSON" | jq -r '.response.name')
GOOGLE_MAPS_API_KEY=$(echo "$API_OPERATION_JSON" | jq -r '.response.keyString') # This is the variable we need later

if [ -z "$KEY_NAME" ] || [ "$KEY_NAME" == "null" ] || [ -z "$GOOGLE_MAPS_API_KEY" ] || [ "$GOOGLE_MAPS_API_KEY" == "null" ]; then
    echo "❌ ERROR: Failed to parse key details from gcloud output."
    exit 1
fi
log "Successfully created key. Now applying restrictions..."
gcloud services api-keys update "$KEY_NAME" --clear-restrictions
gcloud services api-keys update "$KEY_NAME" --api-target="service=maps-javascript.googleapis.com" > /dev/null
log "API Key has been created and restricted to the Maps JavaScript API."


# --- Step 10: Setup Python Environment & Application Data ---
log "--- Step 10: Setting up Python environment and populating database ---"
cd "$REPO_FULL_PATH"
VENV_PATH="env"
if [ -d "$VENV_PATH" ]; then
    log "Python virtual environment 'env' already exists. Re-activating it."
else
    python -m venv "$VENV_PATH"
    log "Created Python virtual environment."
fi

log "Activating virtual environment and installing dependencies..."
source "$REPO_FULL_PATH/$VENV_PATH/bin/activate"
pip install --upgrade pip
pip install -r "$REPO_FULL_PATH/requirements.txt"
log "Python dependencies installed."

log "Running application setup script to populate database..."
cd "$REPO_FULL_PATH/instavibe"
python setup.py
cd ..
log "Application setup complete."


# --- Step 11: Download Additional Agent Files ---
log "--- Step 11: Downloading additional agent files ---"

# The current directory is ~/$REPO_DIR_NAME
log "Creating destination directories..."


log "Downloading agent.py for planner..."
curl -L --fail -o $REPO_FULL_PATH/agents/planner/agent.py \
  "https://raw.githubusercontent.com/weimeilin79/instavibe-adk/refs/heads/adk-1.2.1/agents/planner/agent.py"

log "Downloading instavibe.py tool..."
curl -L --fail -o $REPO_FULL_PATH/tools/instavibe/instavibe.py \
  "https://raw.githubusercontent.com/weimeilin79/instavibe-adk/refs/heads/adk-1.2.1/tools/instavibe/instavibe.py"

log "Downloading mcp_server.py tool..."
curl -L --fail -o $REPO_FULL_PATH//tools/instavibe/mcp_server.py \
  "https://raw.githubusercontent.com/weimeilin79/instavibe-adk/refs/heads/adk-1.2.1/tools/instavibe/mcp_server.py"

log "Downloading agent.py for platform_mcp_client..."
curl -L --fail -o $REPO_FULL_PATH/agents/platform_mcp_client/agent.py \
  "https://raw.githubusercontent.com/weimeilin79/instavibe-adk/refs/heads/adk-1.2.1/agents/platform_mcp_client/agent.py"

log "Additional files downloaded successfully."


# --- Step 12: Build Application Container with Cloud Build ---
log "--- Step 12: Building the application container ---"
IMAGE_PATH="${GOOGLE_CLOUD_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO_NAME}/${IMAGE_NAME}:latest"

cd "$REPO_FULL_PATH/instavibe"
gcloud builds submit . --tag="${IMAGE_PATH}" --project="${PROJECT_ID}"
cd ..
log "Container image successfully built and pushed to Artifact Registry."


# --- Step 13: Deploy Application to Cloud Run ---
log "--- Step 13: Deploying the application to Cloud Run ---"
gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE_PATH}" \
  --platform=managed \
  --region="${GOOGLE_CLOUD_LOCATION}" \
  --allow-unauthenticated \
  --set-env-vars="SPANNER_INSTANCE_ID=${SPANNER_INSTANCE_ID}" \
  --set-env-vars="SPANNER_DATABASE_ID=${SPANNER_DATABASE_ID}" \
  --set-env-vars="APP_HOST=0.0.0.0" \
  --set-env-vars="APP_PORT=8080" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-env-vars="GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}" \
  --project="${PROJECT_ID}" \
  --min-instances=1
log "Application successfully deployed to Cloud Run."


# --- Step 14: Build and Deploy the MCP Tool Server ---
log "--- Step 14: Building and Deploying the MCP Tool Server ---"
MCP_SERVICE_NAME="mcp-tool-server"
MCP_IMAGE_NAME="mcp-tool-server"
MCP_IMAGE_PATH="${GOOGLE_CLOUD_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO_NAME}/${MCP_IMAGE_NAME}:latest"

log "Building the MCP tool server container..."
cd "$REPO_FULL_PATH/tools/instavibe"
gcloud builds submit . \
  --tag="${MCP_IMAGE_PATH}" \
  --project="${PROJECT_ID}"
cd ..
log "MCP tool server container built successfully."

# Get the base URL of the main InstaVibe service, which is a dependency
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform=managed --region=${GOOGLE_CLOUD_LOCATION} --format='value(status.url)')
INSTAVIBE_BASE_URL="${SERVICE_URL}/api"
log "Using InstaVibe base URL for MCP server: $INSTAVIBE_BASE_URL"

# Deploy the MCP tool server to Cloud Run
log "Deploying the MCP tool server to Cloud Run..."
gcloud run deploy "${MCP_SERVICE_NAME}" \
  --image="${MCP_IMAGE_PATH}" \
  --platform=managed \
  --region="${GOOGLE_CLOUD_LOCATION}" \
  --allow-unauthenticated \
  --set-env-vars="INSTAVIBE_BASE_URL=${INSTAVIBE_BASE_URL}" \
  --set-env-vars="APP_HOST=0.0.0.0" \
  --set-env-vars="APP_PORT=8080" \
  --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE" \
  --set-env-vars="GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION}" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --project="${PROJECT_ID}" \
  --min-instances=1
log "MCP tool server successfully deployed."


# --- Unset the trap if we reach the end successfully ---
trap - ERR

# --- Final Success Message ---
# SERVICE_URL is already fetched. Now get the MCP server URL.
MCP_SERVICE_URL=$(gcloud run services describe ${MCP_SERVICE_NAME} --platform=managed --region=${GOOGLE_CLOUD_LOCATION} --format='value(status.url)')

echo ""
echo "==========================================================================="
echo "🚀 InstaVibe Bootstrap Setup is Complete! 🚀"
echo "==========================================================================="
echo ""
echo "All cloud resources have been provisioned and the applications are DEPLOYED."
echo ""
echo "✅ Your InstaVibe web application is available at:"
echo "   ${SERVICE_URL}"
echo ""
echo "✅ Your MCP Tool Server is available at:"
echo "   ${MCP_SERVICE_URL}"
echo ""
echo "👉 You are ready to start working on building your first agent!! "
echo "   https://codelabs.devsite.corp.google.com/instavibe-adk-multi-agents/instructions#8 "
echo ""
echo "==========================================================================="