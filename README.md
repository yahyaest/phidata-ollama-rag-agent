# AI Server

This project provides a containerized environment for running Ollama models with a user-friendly Streamlit UI.

## Overview

The AI Server consists of the following components:

- **Ollama-UI**: A Streamlit interface for interacting with Ollama models
- **Nginx**: Acts as a proxy and handles API key authentication
- **Ollama**: Optional self-hosted LLM server (currently commented out in docker-compose.yml)

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repository-url>
cd ai_server
```

### 2. Configure Environment Variables

Create a `.env` file based on the provided example:

```bash
# Copy the example file
cp .env.example .env

# Generate a secure API key
API_KEY=$(openssl rand -base64 32 | tr '+/' '-_' | tr -d '=' | sed 's/^/sk_ollama_/')
echo "OLLAMA_API_KEY=$API_KEY" > .env
```

Edit the .env file if needed to customize your configuration.

### 3. Set up Docker Network (Optional)

If you want to connect this stack to other Docker services:

```bash
docker network create ollama-network
```

### 4. Start the Services

Launch the entire stack with Docker Compose:

```bash
docker-compose up -d
```

## Accessing the Services

- **Ollama UI**: http://localhost:8505
- **Ollama API**: http://localhost:11436

## Available Models

The default configuration includes the following models:
- deepseek-r1:1.5b
- llama3.1
- nomic-embed-text

## Customization

### Adding Custom Models

Edit the `entrypoint.sh` file to pull additional models during initialization.

### Connecting to External Ollama Instance

By default, the configuration assumes you're using an external Ollama instance. If you want to use the built-in Ollama service, uncomment the relevant sections in the `docker-compose.yml` file.

## Troubleshooting

If you encounter any issues:

1. Check logs with `docker-compose logs`
2. Ensure all environment variables are properly set
3. Verify that the Docker network is created correctly

## License

[Include license information here] 