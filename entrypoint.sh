#!/bin/bash

# Start Ollama in the background.
/bin/ollama serve &
# Record Process ID.
pid=$!

# Pause for Ollama to start.
sleep 5

echo "🔴 Retrieve DeepSeek-R1 1.5B model..."
ollama run deepseek-r1:1.5b
echo "🟢 Done!"

echo "🔴 Retrieve LLAMA3.1 model..."
ollama pull llama3.1
echo "🟢 Done!"

echo "🔴 Retrieve nomic-embed-text model..."
ollama pull nomic-embed-text
echo "🟢 Done!"

echo "List of available models:"
ollama list

# Wait for Ollama process to finish.
wait $pid