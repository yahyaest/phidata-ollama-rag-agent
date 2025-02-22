from phi.agent import Agent
from phi.model.ollama import Ollama
from phi.embedder.ollama import OllamaEmbedder
from phi.knowledge.text import TextKnowledgeBase
# from phi.storage.agent.postgres import PgAgentStorage
# from phi.vectordb.pgvector import PgVector, SearchType
from phi.vectordb.chroma import ChromaDb

# from phi.playground import Playground, serve_playground_app
import os
import uuid
import datetime
from io import StringIO
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
print(f"Using API key: {OLLAMA_API_KEY}...")
if not OLLAMA_API_KEY:
    raise ValueError("OLLAMA_API_KEY environment variable is not set")

# Database configuration


file_path = "/app/scripts/data/berryscheduler.internal_small.txt"

try:
    print("Initializing knowledge base...")
    # First, verify the file exists and is readable
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Log file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        print(f"Log file size: {os.path.getsize(file_path)} bytes")
        log_content = f.read()
        print(f"First line of log file: {log_content.splitlines()[0]}")
    
    # Initialize the vector database with Ollama embeddings
    embedder = OllamaEmbedder(
        model="nomic-embed-text",
        dimensions=768,  # Set dimensions for nomic-embed-text model
        host="http://ollama-nginx:11436",
        client_kwargs={
            "headers": {
                "Authorization": f"Bearer {OLLAMA_API_KEY}"
            }
        }
    )
    
    vector_db = ChromaDb(
                collection="txt_ollama",
                embedder=embedder
            )
    
    # vector_db = PgVector(
    #     table_name="txt_ollama",
    #     db_url=db_url,
    #     search_type=SearchType.hybrid,
    #     embedder=embedder,
    #     vector_score_weight=0.8,  # Increase weight for vector similarity
    #     prefix_match=True  # Enable prefix matching for better text search
    # )
    
    # Create knowledge base with the vector database
    knowledge_base = TextKnowledgeBase(
        path=file_path,
        vector_db=vector_db
    )

    # Load the knowledge base
    print("Loading knowledge base...")
    # knowledge_base.load(upsert=True, recreate=True)  # Use recreate=True to create table with correct dimensions
    knowledge_base.load(upsert=True)


    # Agentic RAG with Ollama
    print("##### Agentic RAG with Ollama #####")
    agent = Agent(
        model=Ollama(
            model="deepseek-r1:1.5b",
            host="http://ollama-nginx:11436",
            client_params={
                "headers": {
                    "Authorization": f"Bearer {OLLAMA_API_KEY}"
                }
            }
        ),
        knowledge_base=knowledge_base,
        add_context=True,
        search_knowledge=True,
        # read_chat_history=True,
        # use_tools=False,  # Disable tools to avoid the error
        instructions=[
            "You are analyzing a log file with entries in the format: [TIMESTAMP] [COMPONENT] LEVEL::(THREAD)::MODULE:LINE - MESSAGE",
            "Your task is to find and report ALL error messages in the log file, without exception.",
            "Search Strategy:",
            "1. Search for ALL chunks containing 'ERROR', 'CRITICAL', or 'WARNING' messages",
            "2. Process every single chunk to ensure no errors are missed",
            "3. Combine and deduplicate the results",
            "Analysis Priority Order:",
            "1. List ALL ERROR and CRITICAL messages chronologically (ensure completeness)",
            "2. Then list ALL WARNING messages chronologically",
            "3. Group similar errors together and identify patterns",
            "Format Requirements:",
            "- Use table format with columns: Timestamp | Level | Component | Message",
            "- Double-check that NO errors are omitted from the analysis",
            "- Provide error frequency statistics",
            "- End with a summary of the most critical issues found",
        ],
        markdown=True,
        save_response_to_file=f"app/output/log_analysis_ollama_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
    )
    
    # Also print to console
    print("\nAnalysis output:")
    print("---")
    agent.print_response(
        f"""Analyze the log file {file_path} and find ALL error messages. Follow these steps:
        1. Search through ALL chunks in the vector database
        2. Extract EVERY single ERROR and CRITICAL message first
        3. Then extract ALL WARNING messages
        4. Ensure NO error messages are missed
        5. Present them chronologically in a table format
        6. Group similar issues and provide statistics
        Do not summarize or skip any errors - I need to see ALL of them.""",
        stream=True
    )

except Exception as e:
    print(f"Error: {str(e)}") 