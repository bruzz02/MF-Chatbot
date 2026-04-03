import os
from dotenv import load_dotenv
import chromadb
from openai import OpenAI

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "Phase_2", ".env"))

class MFRagBot:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.model_name = os.getenv("MODEL_NAME", "google/gemini-2.5-flash")
        self.embedding_model = os.getenv("EMBEDDING_MODEL_NAME", "openai/text-embedding-3-small")
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables.")

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

        # Initialize ChromaDB - pointing to Phase_2's database
        self.persist_directory = os.path.join(os.path.dirname(__file__), "..", "Phase_2", "chroma_db")
        self.chroma_client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.chroma_client.get_or_create_collection(name="mutual_funds")

    def get_relevant_context(self, query):
        """Retrieve the most relevant fund data from ChromaDB."""
        try:
            # Generate query embedding
            response = self.client.embeddings.create(
                input=[query],
                model=self.embedding_model
            )
            query_embedding = response.data[0].embedding

            # Search for the top match
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=1
            )

            if results["documents"] and results["documents"][0]:
                return results["documents"][0][0], None
            return None, "No relevant data found."
        except Exception as e:
            return None, f"Retrieval Error: {str(e)}"

    def ask(self, query):
        """Generate a RAG response for the query."""
        context, error = self.get_relevant_context(query)
        
        if error:
            return f"Context Retrieval Error: {error}"

        system_prompt = (
            "You are a Professional Mutual Fund Advisor assistant. Your goal is to answer user queries "
            "based strictly on the mutual fund context provided below. Be professional and accurate. "
            "Do not offer specific investment advice or buy/sell recommendations. If the answer is not "
            "in the context, say 'I don't have that information'."
        )

        prompt = f"Context:\n{context}\n\nUser Question: {query}\n\nHelpful Response:"

        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://nextleap.app",
                    "X-Title": "MF Chatbot Phase 3",
                },
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Generation Error: {str(e)}"

if __name__ == "__main__":
    # Quick test
    bot = MFRagBot()
    print(bot.ask("What is the NAV of Kotak Midcap Fund?"))
