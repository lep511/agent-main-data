# InstaVibe: AI-Powered Social Planning Platform

Streamlining social event planning through intelligent multi-agent automation

## Overview

InstaVibe is an innovative social event platform that leverages AI-powered agents to help users, particularly those who find event planning challenging, discover and organize social activities with their friends. Our multi-agent system automates the traditionally time-consuming tasks of interest discovery, activity research, and initial coordination.

## 🚀 Key Features

- **Intelligent Social Profiling**: Analyzes user connections and interactions to identify shared interests
- **Automated Event Discovery**: Searches and suggests relevant activities based on user preferences
- **Seamless Platform Integration**: Creates event posts directly within the InstaVibe platform
- **Multi-Agent Orchestration**: Coordinates multiple specialized agents for comprehensive event planning

## 🏗️ Architecture

Our system employs a sophisticated multi-agent architecture powered by Google Cloud Platform:

### Core Agents

1. **Social Profiling Agent**
   - Employs social listening techniques to analyze user connections
   - Identifies shared interests and activity preferences
   - Determines suitable characteristics (e.g., group size preferences, activity types)

2. **Event Planning Agent**
   - Searches online resources for specific events and venues
   - Aligns suggestions with identified criteria (location, interests, timing)
   - Provides detailed activity recommendations

3. **Platform Interaction Agent**
   - Utilizes Model Context Protocol (MCP) for platform integration
   - Drafts event suggestions and creates platform posts
   - Manages direct interaction with InstaVibe's APIs

4. **Orchestrator Agent**
   - Central coordinator managing the entire workflow
   - Delegates tasks to specialized agents in logical sequence
   - Ensures seamless information flow between agents

## 🛠️ Technology Stack

### Google Cloud Platform Services

- **Vertex AI**: 
  - Gemini Models for advanced reasoning and decision-making
  - Agent Engine for deploying and scaling the orchestrator agent
- **Cloud Run**: Serverless deployment for microservices and web application
- **Spanner**: Graph database for modeling complex social relationships
- **Artifact Registry**: Container image management
- **Cloud Build**: Automated container image building
- **Cloud Storage**: Build artifacts and operational data storage

### Core Frameworks & Protocols

- **Google Agent Development Kit (ADK)**: Primary framework for agent development
- **Agent-to-Agent (A2A) Protocol**: Enables standardized inter-agent communication
- **Model Context Protocol (MCP)**: Facilitates agent-tool integration
- **A2A Python Library**: Server-side A2A protocol implementation

### AI Models

- **Google Gemini 2.0 Flash**: Optimized for performance and cost-effectiveness
- Advanced reasoning and instruction following capabilities
- Sophisticated tool use and function calling features

## 🔧 Development Tools

### A2A Inspector
Web-based debugging tool for agent development:
- **Agent Card Viewer**: Validate agent capabilities
- **Live Chat Interface**: Direct agent testing
- **Debug Console**: Raw JSON-RPC message inspection

## 🚦 Getting Started

### Prerequisites

- Google Cloud Platform account with billing enabled
- Docker installed for containerization
- Python 3.9+ for agent development
- Access to Vertex AI and required GCP services

### First step

```bash
# Clone the repository
git clone https://github.com/instavibe/ai-social-planning.git
cd ai-social-planning

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure Google Cloud credentials
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Configuration

1. **Set up GCP services**:
   ```bash
   # Enable required APIs
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable spanner.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```

2. **Configure environment variables**:
   ```bash
   export GOOGLE_CLOUD_PROJECT=your-project-id
   export SPANNER_INSTANCE=your-spanner-instance
   export SPANNER_DATABASE=your-database
   ```

3. **Deploy agents**:
   ```bash
   # Build and deploy individual agents
   ./scripts/deploy-agents.sh
   ```
