import json
import os
from dotenv import load_dotenv
import chromadb
from openai import OpenAI

# Load environment variables
load_dotenv()

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
    api_key = os.getenv("OPENROUTER_API_KEY")
    # Fallback to streamlit secrets if os.getenv fails (for deployment)
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets["OPENROUTER_API_KEY"]
        except (ImportError, KeyError):
            pass

    # Initialize OpenRouter Client for Embeddings
    client = OpenAI(
        base_url=os.getenv("OPENROUTER_BASE_URL", st.secrets.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1") if 'st' in locals() else "https://openrouter.ai/api/v1"),
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
                model=os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-004")
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
