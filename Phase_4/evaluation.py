import os
from dotenv import load_dotenv
from advanced_rag import AdvancedMFRagBot
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from datasets import Dataset
import pandas as pd
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "Phase_2", ".env"))

def run_evaluation():
    bot = AdvancedMFRagBot()
    
    # Ensure environment is set for RAGAS
    if bot.api_key:
        os.environ["OPENAI_API_KEY"] = bot.api_key
        os.environ["OPENAI_API_BASE"] = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    # 1. Define Golden Dataset (Small Sample)
    dataset_dict = {
        "question": [
            "What is the NAV of Kotak Small Cap Fund?",
            "What is the risk level of Kotak Midcap Fund?",
            "What is the benchmark for Kotak Large Cap Fund?",
            "Is there a lock-in period for Kotak ELSS Tax Saver Scheme Fund?",
            "What is the expense ratio of Kotak Multicap Fund?"
        ],
        "ground_truth": [
            "₹263.99",
            "Very High Risk",
            "Nifty 100 TR INR",
            "3 Years",
            "0.45%"
        ]
    }

    # 2. Run the pipeline to get answers and contexts
    answers = []
    contexts = []
    
    print("Running pipeline for evaluation...")
    for query in dataset_dict["question"]:
        print(f"Querying: {query}")
        # Get context from hybrid search
        context = bot.hybrid_search(query)
        contexts.append([context])
        
        # Get answer
        answer = bot.ask(query)
        answers.append(answer)

    # Prepare dataset for RAGAS
    dataset_dict["answer"] = answers
    dataset_dict["contexts"] = contexts
    
    dataset = Dataset.from_dict(dataset_dict)

    # 3. Evaluate with RAGAS
    evaluator_llm = ChatOpenAI(
        model=bot.model_name,
        openai_api_key=bot.api_key,
        openai_api_base=os.environ["OPENAI_API_BASE"],
    )
    
    evaluator_embeddings = OpenAIEmbeddings(
        model=bot.embedding_model,
        openai_api_key=bot.api_key,
        openai_api_base=os.environ["OPENAI_API_BASE"],
    )

    print("\nStarting RAGAS evaluation...")
    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            # Removing Precision/Recall for now to simplify troubleshooting
        ],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
    )

    # 4. Report Results
    print("\n" + "="*30)
    print("RAGAS EVALUATION REPORT")
    print("="*30)
    df = result.to_pandas()
    print(df)
    
    # Save report
    report_path = os.path.join(os.path.dirname(__file__), "evaluation_report.csv")
    df.to_csv(report_path, index=False)
    print(f"\nReport saved to {report_path}")

if __name__ == "__main__":
    run_evaluation()
