from chatbot import ask_chatbot
import os
from dotenv import load_dotenv

load_dotenv()

def test_query():
    query = "What is the NAV and Risk level of Kotak Small Cap Fund?"
    print(f"Testing Query: {query}")
    print("-" * 30)
    
    response = ask_chatbot(query)
    print(f"Response:\n{response}")
    with open("test_output.txt", "w", encoding="utf-8") as f:
        f.write(response)

if __name__ == "__main__":
    test_query()
