import json
import os
from dotenv import load_dotenv
import chromadb
from openai import OpenAI

# Load environment variables
load_dotenv()

def get_config(key, default=None):
    """Fetch configuration from environment variables or Streamlit secrets."""
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        # Directly access st.secrets within try block to handle StreamlitSecretNotFoundError
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        # Catch all secrets errors locally (this handles the StreamlitSecretNotFoundError)
        pass
    return default

def pre_process_fund_data(data_path):
    """Load and format fund data for embedding."""
    with open(data_path, "r", encoding="utf-8") as f:
        funds = json.load(f)
    
    formatted_data = []
    for fund in funds:
        # Create a detailed natural language description of the fund
        description = (
            f"Fund Name: {fund.get('Fund Name')}. "
            f"As of Date: {fund.get('NAV_Date', 'N/A')}. "
            f"Net Asset Value (NAV): {fund.get('NAV')}. "
            f"Expense Ratio: {fund.get('Expense ratio')}. "
            f"Assets Under Management (AUM): {fund.get('AUM')}. "
            f"Minimum Lumpsum/SIP: {fund.get('Min Lumpsum/SIP')}. "
            f"Lock-in Period: {fund.get('Lock In')}. "
            f"Risk Level: {fund.get('Risk')}. "
            f"Benchmark: {fund.get('Benchmark')}. "
            f"Inception Date: {fund.get('Inception Date')}. "
            f"Exit Load: {fund.get('Exit Load')}."
        )
        formatted_data.append({
            "id": fund.get("Fund Name").replace(" ", "_").lower(),
            "text": description,
            "metadata": fund
        })
    return formatted_data

def ingest_data():
    api_key = get_config("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found in environment or secrets.")
        return

    # Initialize OpenRouter Client for Embeddings
    client = OpenAI(
        base_url=get_config("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=api_key,
    )

    data_path = os.path.join(os.path.dirname(__file__), "fund_data.json")
    formatted_funds = pre_process_fund_data(data_path)

    # Initialize ChromaDB
    persist_directory = os.path.join(os.path.dirname(__file__), "chroma_db")
    chroma_client = chromadb.PersistentClient(path=persist_directory)
    collection = chroma_client.get_or_create_collection(name="mutual_funds")

    print(f"Ingesting {len(formatted_funds)} funds into ChromaDB...")

    for fund in formatted_funds:
        print(f"Generating embedding for {fund['metadata']['Fund Name']}...")
        
        # Note: OpenRouter might not support all embedding models.
        # If this fails, consider using a local model like sentence-transformers.
        try:
            response = client.embeddings.create(
                input=[fund["text"]],
                model=get_config("EMBEDDING_MODEL_NAME", "openai/text-embedding-3-small")
            )
            embedding = response.data[0].embedding

            collection.upsert(
                ids=[fund["id"]],
                embeddings=[embedding],
                documents=[fund["text"]],
                metadatas=[fund["metadata"]]
            )
        except Exception as e:
            print(f"Failed to ingest {fund['metadata']['Fund Name']}: {e}")

    print("Data ingestion complete.")

if __name__ == "__main__":
    ingest_data()
