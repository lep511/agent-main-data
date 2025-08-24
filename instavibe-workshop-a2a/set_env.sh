#!/bin/bash

# This script sets various Google Cloud related environment variables.
# It must be SOURCED to make the variables available in your current shell.
# Example: source ./set_gcp_env.sh

# --- Configuration ---
PROJECT_FILE="~/project_id.txt"
SPANNER_INSTANCE_ID="instavibe-graph-instance"
SPANNER_DATABASE_ID="graphdb"
GOOGLE_CLOUD_LOCATION="us-central1"
REPO_NAME="introveally-repo"
MAPKEY_FILE="~/mapkey.txt"
# ---------------------

# --- Docker Configuration ---
DOCKER_IMAGE_NAME="a2a-inspector"
DOCKER_CONTAINER_NAME="a2a-inspector" # Usually the same as the image name
GIT_REPO_URL="https://github.com/weimeilin79/a2a-inspector.git"
# Define the local directory for the clone. Using $HOME is safer in scripts.
GIT_REPO_DIR="$HOME/a2a-inspector"
# ---------------------

echo "--- Setting Google Cloud Environment Variables ---"

# --- Authentication Check ---
echo "Checking gcloud authentication status..."
# Run a command that requires authentication (like listing accounts or printing a token)
# Redirect stdout and stderr to /dev/null so we don't see output unless there's a real error
if gcloud auth print-access-token > /dev/null 2>&1; then
  echo "gcloud is authenticated."
else
  echo "Error: gcloud is not authenticated."
  echo "Please log in by running: gcloud auth login"
  # Use 'return 1' instead of 'exit 1' because the script is meant to be sourced.
  # 'exit 1' would close your current terminal session.
  return 1
fi
# --- --- --- --- --- ---


# 1. Check if project file exists
PROJECT_FILE_PATH=$(eval echo $PROJECT_FILE) # Expand potential ~
if [ ! -f "$PROJECT_FILE_PATH" ]; then
  echo "Error: Project file not found at $PROJECT_FILE_PATH"
  echo "Please create $PROJECT_FILE_PATH containing your Google Cloud project ID."
  return 1 # Return 1 as we are sourcing
fi

# 2. Set the default gcloud project configuration
PROJECT_ID_FROM_FILE=$(cat "$PROJECT_FILE_PATH")
echo "Setting gcloud config project to: $PROJECT_ID_FROM_FILE"
# Adding --quiet; set -e will handle failure if the project doesn't exist or access is denied
gcloud config set project "$PROJECT_ID_FROM_FILE" --quiet

# 3. Export PROJECT_ID (Get from config to confirm it was set correctly)
export PROJECT_ID=$(gcloud config get project)
echo "Exported PROJECT_ID=$PROJECT_ID"

# 4. Export PROJECT_NUMBER
# Using --format to extract just the projectNumber value
export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
echo "Exported PROJECT_NUMBER=$PROJECT_NUMBER"

# 5. Export SERVICE_ACCOUNT_NAME (Default Compute Service Account)
export SERVICE_ACCOUNT_NAME=$(gcloud compute project-info describe --format="value(defaultServiceAccount)")
echo "Exported SERVICE_ACCOUNT_NAME=$SERVICE_ACCOUNT_NAME"

# 6. Export SPANNER_INSTANCE_ID
# Use the variable defined in the configuration section
export SPANNER_INSTANCE_ID="$SPANNER_INSTANCE_ID"
echo "Exported SPANNER_INSTANCE_ID=$SPANNER_INSTANCE_ID"

# 7. Export SPANNER_DATABASE_ID
# Use the variable defined in the configuration section
export SPANNER_DATABASE_ID="$SPANNER_DATABASE_ID"
echo "Exported SPANNER_DATABASE_ID=$SPANNER_DATABASE_ID"

# 8. Export GOOGLE_CLOUD_PROJECT (Often used by client libraries)
# This is usually the same as PROJECT_ID
export GOOGLE_CLOUD_PROJECT="$PROJECT_ID"
echo "Exported GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT"

# 9. Export GOOGLE_GENAI_USE_VERTEXAI
export GOOGLE_GENAI_USE_VERTEXAI="TRUE"
echo "Exported GOOGLE_GENAI_USE_VERTEXAI=$GOOGLE_GENAI_USE_VERTEXAI"

# 10. Export GOOGLE_CLOUD_LOCATION
export GOOGLE_CLOUD_LOCATION="$GOOGLE_CLOUD_LOCATION"
echo "Exported GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION"

# 11. Export REPO_NAME
export REPO_NAME="$REPO_NAME"
echo "Exported REPO_NAME=$REPO_NAME"

# 12. Export REGION
export REGION="$GOOGLE_CLOUD_LOCATION"
echo "Exported REGION=$GOOGLE_CLOUD_LOCATION"

# 13. Check for and set GOOGLE_MAPS_API_KEY from mapkey.txt
MAPKEY_FILE_PATH=$(eval echo $MAPKEY_FILE)
if [ -f "$MAPKEY_FILE_PATH" ]; then
  # File exists
  if [ -s "$MAPKEY_FILE_PATH" ]; then
    # File is not empty
    export GOOGLE_MAPS_API_KEY=$(cat "$MAPKEY_FILE_PATH")
    echo "Exported GOOGLE_MAPS_API_KEY from $MAPKEY_FILE_PATH"
  else
    # File is empty
    echo "WARNING!!WARNING!!WARNING!!WARNING!!WARNING!!WARNING!!WARNING!!WARNING!!"
    echo "------------------GOOGLE_MAPS_API_KEY will not be set.-------------------"
    echo "-------------------------------------------------------------------------"
    echo ""
    echo "Check your key name must be \"Maps Platform API Key\" and rerun 1st section of step 5."
    echo ""
    echo "-------------------------------------------------------------------------"
    echo "WARNING!!WARNING!!WARNING!!WARNING!!WARNING!!WARNING!!WARNING!!WARNING!!"
  fi
fi

echo ""
echo "--- Docker Environment Check & Setup ---"

# --- Prerequisite checks for Docker ---
echo "Checking for required tools (git, docker)..."
if ! command -v git &> /dev/null; then
  echo "Error: git is not installed. Please install git."
  return 1
fi
# Check if docker command exists AND the daemon is responsive
if ! command -v docker &> /dev/null || ! docker info >/dev/null 2>&1; then
  echo "Error: Docker is not installed or the Docker daemon is not running."
  return 1
fi
echo "All required tools are present."

# --- Main Docker Logic ---
# Check if the container is already running. Using ^ and $ for an exact name match.
if [ "$(docker ps -q -f name=^/${DOCKER_CONTAINER_NAME}$)" ]; then
    echo "Docker container '$DOCKER_CONTAINER_NAME' is already running. No action needed."
else
    echo "Container '$DOCKER_CONTAINER_NAME' is not running. Proceeding with setup..."

    # Check if the image exists. If not, build it.
    if [[ -z "$(docker images -q ${DOCKER_IMAGE_NAME} 2> /dev/null)" ]]; then
        echo "Docker image '$DOCKER_IMAGE_NAME' not found. Cloning repo and building..."

        # Use a subshell to avoid changing the user's current directory
        (
            set -e # Exit subshell immediately if a command fails
            echo "Changing to home directory: $HOME"
            cd "$HOME"
            if [ -d "$GIT_REPO_DIR" ]; then
                echo "Removing existing repository directory for a fresh clone."
                rm -rf "$GIT_REPO_DIR"
            fi
            echo "Cloning repository from $GIT_REPO_URL..."
            git clone "$GIT_REPO_URL" "$GIT_REPO_DIR"
            cd "$GIT_REPO_DIR"
            echo "Building Docker image '$DOCKER_IMAGE_NAME'..."
            docker build -t "$DOCKER_IMAGE_NAME" .
        )

        # Check the exit code of the subshell
        if [ $? -ne 0 ]; then
            echo "Error: Failed to clone repository or build the Docker image."
            return 1
        fi
        echo "Docker image built successfully."
    else
        echo "Docker image '$DOCKER_IMAGE_NAME' already exists."
    fi

    # At this point, the image is guaranteed to exist. Now, run the container.

    # Remove any stopped container with the same name to avoid conflicts
    if [ "$(docker ps -aq -f status=exited -f name=^/${DOCKER_CONTAINER_NAME}$)" ]; then
        echo "Removing stopped container with the same name..."
        docker rm "$DOCKER_CONTAINER_NAME"
    fi

    echo "Starting container '$DOCKER_CONTAINER_NAME'..."
    docker run -d -p 8081:8080 --name "$DOCKER_CONTAINER_NAME" "$DOCKER_IMAGE_NAME"

    if [ $? -ne 0 ]; then
        echo "Error: Failed to start the Docker container."
        return 1
    fi
    echo "Container started successfully."
    echo "You can access the application on this machine at: http://localhost:8081"
fi


echo ""
echo "--- Environment setup complete ---"