#!/bin/sh
set -e

# Replace environment variables in the Nginx configuration
envsubst '${OLLAMA_API_KEY}' < /etc/nginx/conf.d/ollama.conf.template > /etc/nginx/conf.d/ollama.conf

# Execute the main container command
exec "$@" 