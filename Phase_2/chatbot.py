import os
from dotenv import load_dotenv
import chromadb
from openai import OpenAI
import sys
from pathlib import Path

# Add project root to sys.path for Security_Privacy imports
root_path = str(Path(__file__).parent.parent)
if root_path not in sys.path:
    sys.path.append(root_path)

from Security_Privacy.pii_handler import mask_pii
from Security_Privacy.sanitizer import sanitize_user_input, check_for_injection

# Load environment variables
load_dotenv()

def get_relevant_context(query):
    """Retrieve the most relevant fund data from ChromaDB."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None, "API Key not found."

    client = OpenAI(
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=api_key,
    )

    # Re-initialize ChromaDB
    persist_directory = os.path.join(os.path.dirname(__file__), "chroma_db")
    chroma_client = chromadb.PersistentClient(path=persist_directory)
    collection = chroma_client.get_or_create_collection(name="mutual_funds")

    try:
        # Generate query embedding
        response = client.embeddings.create(
            input=[query],
            model=os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-004")
        )
        query_embedding = response.data[0].embedding

        # Search for the top match
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=1 # Just the most relevant one for now
        )

        if results["documents"] and results["documents"][0]:
            return results["documents"][0][0], None
        return None, "No relevant data found."
    except Exception as e:
        return None, str(e)

def ask_chatbot(query):
    """Generate a RAG response for the query with security filtering."""
    
    # 1. Sanitize Input
    query = sanitize_user_input(query)
    
    # 2. Check for Injection
    if check_for_injection(query):
        return "I'm sorry, but I cannot process that request due to security constraints."
    
    # 3. Mask PII
    query = mask_pii(query)
    
    context, error = get_relevant_context(query)
    
    if error:
        print(f"Error retrieving context: {error}")
        return

    api_key = os.getenv("OPENROUTER_API_KEY")
    client = OpenAI(
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=api_key,
    )

    system_prompt = (
        "You are a Professional Mutual Fund Advisor assistant. Your goal is to answer user queries "
        "based strictly on the mutual fund context provided below. Be professional and accurate. "
        "CRITICAL REQUIREMENT: Every single statement or answer you provide about a mutual fund "
        "(including NAV, AUM, Risk level, Expense Ratio, Benchmark, etc.) MUST be followed by the "
        "phrase 'as of [As of Date]' based on the date provided in the context. "
        "This is non-negotiable and applies to every metric mentioned. "
        "Do not offer specific investment advice or buy/sell recommendations. If a user asks "
        "for personal information, user-specific data, or PII, explicitly state that it is "
        "out of scope. If the answer is not in the context, say 'I don't have that information'."
    )

    prompt = f"Context:\n{context}\n\nUser Question: {query}\n\nHelpful Response:"

    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://nextleap.app",
                "X-Title": "MF Chatbot Project",
            },
            model=os.getenv("MODEL_NAME", "google/gemini-2.5-flash"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {e}"

if __name__ == "__main__":
    print("--- MF Chatbot (RAG Phase 2) ---")
    while True:
        query = input("\nAsk about Kotak Mutual Funds (or 'quit' to exit): ").strip()
        if query.lower() in ("quit", "exit", "stop"):
            break
        if not query:
            continue
        
        print("Thinking...")
        response = ask_chatbot(query)
        print(f"\nResponse:\n{response}")
