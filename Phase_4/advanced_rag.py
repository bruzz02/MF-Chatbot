import os
import json
from dotenv import load_dotenv
import chromadb
from openai import OpenAI
from rank_bm25 import BM25Okapi
import numpy as np

# Load environment variables from Root .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

class AdvancedMFRagBot:
    def __init__(self):
        # Allow passing custom paths for integration
        self.project_root = os.path.dirname(os.path.dirname(__file__))
        
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables.")

        # Set environment variable for libraries that expect OPENAI_API_KEY
        os.environ["OPENAI_API_KEY"] = self.api_key
        
        self.model_name = os.getenv("MODEL_NAME", "google/gemini-2.5-flash")
        self.embedding_model = os.getenv("EMBEDDING_MODEL_NAME", "openai/text-embedding-3-small")
        
        self.client = OpenAI(
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=self.api_key,
        )

        # Initialize ChromaDB - pointing to Phase_2's database via project root
        self.persist_directory = os.path.join(self.project_root, "Phase_2", "chroma_db")
        self.chroma_client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.chroma_client.get_or_create_collection(name="mutual_funds")

        # Initialize BM25 for Keyword Search
        self._setup_bm25()

    def _setup_bm25(self):
        """Prepare BM25 index from funds data."""
        data_path = os.path.join(self.project_root, "Phase_1", "fund_data.json")
        if not os.path.exists(data_path):
            # Try Phase_2 if Phase_1 is missing
            data_path = os.path.join(self.project_root, "Phase_2", "fund_data.json")
            
        if not os.path.exists(data_path):
            print(f"Warning: Fund data not found at {data_path}")
            self.funds = []
            self.bm25 = None
            return

        with open(data_path, "r", encoding="utf-8") as f:
            self.funds = json.load(f)
        
        # Tokenize descriptions for BM25
        self.corpus = []
        for fund in self.funds:
            text = f"{fund.get('Fund Name', '')} {fund.get('NAV', '')} {fund.get('Risk', '')} {fund.get('Benchmark', '')}"
            self.corpus.append(text.lower().split())
        
        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)
        else:
            self.bm25 = None

    def hybrid_search(self, query, top_k=2):
        """Perform Hybrid Search: Vector + BM25."""
        # 1. Vector Search
        try:
            response = self.client.embeddings.create(
                input=[query],
                model=self.embedding_model
            )
            query_embedding = response.data[0].embedding
            vector_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
        except Exception as e:
            print(f"Vector search failed: {e}")
            vector_results = {"ids": [], "documents": []}
        
        # 2. Keyword Search (BM25)
        bm25_indices = []
        if self.bm25:
            tokenized_query = query.lower().split()
            bm25_scores = self.bm25.get_scores(tokenized_query)
            bm25_indices = np.argsort(bm25_scores)[-top_k:][::-1]
        
        # 3. Hybrid Fusion
        combined_context = []
        seen_ids = set()
        
        # Add vector results first
        if vector_results.get("ids") and vector_results["ids"][0]:
            for i, doc_id in enumerate(vector_results["ids"][0]):
                if doc_id not in seen_ids:
                    combined_context.append(vector_results["documents"][0][i])
                    seen_ids.add(doc_id)
        
        # Add BM25 results if they add something new
        for idx in bm25_indices:
            if idx < len(self.funds):
                fund = self.funds[idx]
                fund_id = fund.get("Fund Name", "").replace(" ", "_").lower()
                if fund_id not in seen_ids:
                    doc = f"Fund Name: {fund.get('Fund Name')}. NAV: {fund.get('NAV')}. Risk: {fund.get('Risk')}."
                    combined_context.append(doc)
                    seen_ids.add(fund_id)
                
        return "\n\n".join(combined_context[:top_k])

    def ask(self, query):
        """Generate response using Hybrid Search context."""
        context = self.hybrid_search(query)
        
        if not context:
            return "I don't have that information in common fund data."

        system_prompt = (
            "You are a Professional Mutual Fund Advisor assistant. Your goal is to answer user queries "
            "based strictly on the mutual fund context provided below. Be professional and accurate. "
            "If the answer is not in the context, say 'I don't have that information'."
        )
        prompt = f"Context:\n{context}\n\nQuestion: {query}"

        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Generation Error: {e}"

if __name__ == "__main__":
    bot = AdvancedMFRagBot()
    print("Testing Integrated Hybrid Search...")
    print(bot.ask("What is the NAV of Kotak Gold Fund?"))

