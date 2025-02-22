import streamlit as st
import requests
import json
import os
import time
import tempfile
from datetime import datetime
from rich.console import Console
from dotenv import load_dotenv
from phi.embedder.ollama import OllamaEmbedder
from phi.knowledge.text import TextKnowledgeBase
from phi.knowledge.pdf import PDFKnowledgeBase
from phi.agent import Agent
from phi.model.ollama import Ollama
from phi.vectordb.chroma import ChromaDb
from chromadb.config import Settings

# Load environment variables
load_dotenv()

# Constants
OLLAMA_API_URL = "http://ollama-nginx:11436"
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Configure Streamlit page
st.set_page_config(
    page_title="Ollama Chat UI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_model" not in st.session_state:
    st.session_state.current_model = None
# if "chroma_client" not in st.session_state:
#     st.session_state.chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))

def get_models():
    """Fetch available models from Ollama API"""
    try:
        headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}"}
        response = requests.get(f"{OLLAMA_API_URL}/api/tags", headers=headers)
        response.raise_for_status()
        models = response.json().get("models", [])
        # Filter out embedding models
        return [model["name"] for model in models if "-embed" not in model["name"]]
    except Exception as e:
        st.error(f"Error fetching models: {str(e)}")
        return []

def format_time(seconds):
    """Format time duration in a readable format"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes}m {seconds:.1f}s"

def stream_response(prompt, model, context=None):
    """Stream response from Ollama API"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OLLAMA_API_KEY}"
    }
    
    # Prepare prompt with context if available
    if context:
        system_prompt = f"""Use the following context to answer the question. If the context doesn't help, just say so.

Context:
{context}

Question: {prompt}"""
    else:
        system_prompt = prompt
    
    data = {
        "model": model,
        "prompt": system_prompt,
        "stream": True
    }
    
    try:
        with requests.post(f"{OLLAMA_API_URL}/api/generate", json=data, headers=headers, stream=True) as response:
            response.raise_for_status()
            
            # Create a placeholder for the streaming response
            message_placeholder = st.empty()
            full_response = ""
            
            # Stream the response
            for line in response.iter_lines():
                if line:
                    json_response = json.loads(line)
                    response_part = json_response.get("response", "")
                    full_response += response_part
                    # Update the placeholder with the accumulated response
                    message_placeholder.markdown(full_response + "▌")
            
            # Final update without the cursor
            message_placeholder.markdown(full_response)
            return full_response
            
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return None

def process_file(uploaded_file):
    """Process uploaded file and create knowledge base"""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{uploaded_file.type.split("/")[1]}') as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file.seek(0)
            
            # Create embedder
            embedder = OllamaEmbedder(
                model="nomic-embed-text",
                dimensions=768,
                host=OLLAMA_API_URL,
                client_kwargs={
                    "headers": {
                        "Authorization": f"Bearer {OLLAMA_API_KEY}"
                    }
                }
            )
            
            # Create vector store
            collection_name = f"collection_{int(time.time())}"
            vector_db = ChromaDb(
                collection=collection_name,
                embedder=embedder            
            )
            
            # Create knowledge base with vector database
            if uploaded_file.type == "application/pdf":
                knowledge_base = PDFKnowledgeBase(
                    path=temp_file.name,
                    vector_db=vector_db,
                )
            else:  # text/plain
                knowledge_base = TextKnowledgeBase(
                    path=temp_file.name,
                    vector_db=vector_db,
                )
            
            # Load the knowledge base
            knowledge_base.load(upsert=True)
            
            # Clean up temporary file
            os.unlink(temp_file.name)
            return knowledge_base
            
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None

def create_agent(model_name, knowledge_base):
    """Create an agent with the selected model and knowledge base"""
    return Agent(
        model=Ollama(
            model=model_name,
            host=OLLAMA_API_URL,
            client_params={
                "headers": {
                    "Authorization": f"Bearer {OLLAMA_API_KEY}"
                }
            }
        ),
        knowledge_base=knowledge_base,
        # show_tool_calls=True,
        add_context=True,
        search_knowledge=True,
        read_chat_history=True,
        instructions=[
            "You are a helpful assistant with access to a knowledge base.",
            "When asked questions, provide detailed responses based on the available context.",
            "If the context doesn't help answer a question, clearly state that.",
            "Format your responses in a clear, professional manner using markdown.",
            "Be precise and accurate with any information from the knowledge base.",
        ],
        markdown=True
    )

# Sidebar
with st.sidebar:
    st.title("🤖 Ollama Chat")
    
    # Model selection
    models = get_models()
    if models:
        selected_model = st.selectbox("Select Model", models)
        
        # Clear chat if model changes
        if st.session_state.current_model != selected_model:
            st.session_state.messages = []
            st.session_state.current_model = selected_model
    else:
        st.error("No models available")
        st.stop()
    
    # File upload section
    st.markdown("### 📄 Upload Context")
    uploaded_file = st.file_uploader("Choose a PDF or TXT file", type=["pdf", "txt"])
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.experimental_rerun()

# Main chat interface
st.markdown("### Chat with Ollama")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        start_time = time.time()
        
        if uploaded_file:
            # Step 1: Process the context file
            with st.spinner(f"Step 1: Processing {uploaded_file.name}..."):
                knowledge_base = process_file(uploaded_file)
            
            if knowledge_base:
                # Step 2: Generate response with context
                with st.spinner("Step 2: Generating response..."):
                    agent = create_agent(selected_model, knowledge_base)
                    message_placeholder = st.empty()
                    # response = agent.print_response(prompt)
                    response = agent.run(prompt, stream=False)
            else:
                response = "Failed to process the context file. Please try again or check if the file is valid."
        else:
            # Generate response without context
            with st.spinner("Generating response..."):
                response = stream_response(prompt, selected_model)
        
        if response:
            duration = time.time() - start_time
            # Extract the actual content from the response if it's a RunResponse object
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = response
                
            final_response = f"{response_text}\n\n---\n*Model: `{selected_model}` • Response time: `{format_time(duration)}`*"
            st.markdown(final_response)
            st.session_state.messages.append({"role": "assistant", "content": final_response}) 