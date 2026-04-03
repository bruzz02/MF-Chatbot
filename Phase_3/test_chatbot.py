import pytest
from rag_logic import MFRagBot
import sys
import os

@pytest.fixture
def bot():
    """Returns an instance of the MF Chatbot."""
    try:
        return MFRagBot()
    except ValueError as e:
        pytest.fail(f"Initialization failed: {e}")

def test_bot_initialization(bot):
    """Verify that the bot initializes correctly with API keys and ChromaDB."""
    assert bot is not None
    assert bot.collection is not None
    assert bot.api_key is not None

def test_retrieval_success(bot):
    """Verify that the bot can retrieve context for a known fund."""
    query = "Kotak Small Cap Fund"
    context, error = bot.get_relevant_context(query)
    
    assert error is None
    assert context is not None
    assert "Kotak Small Cap Fund" in context
    assert "NAV" in context

def test_response_quality(bot):
    """Verify that the bot provides a factual answer for a specific query."""
    query = "What is the Risk level of Kotak Midcap Fund?"
    response = bot.ask(query)
    
    assert response is not None
    assert "Risk" in response
    # Based on our data, Kotak Midcap Fund is 'Very High Risk'
    assert "Very High" in response

def test_hallucination_prevention(bot):
    """Verify that the bot handles out-of-scope queries gracefully."""
    query = "Who is the Prime Minister of India?"
    response = bot.ask(query)
    
    # The system prompt instructs to say "I don't have that information" for missing context
    assert "don't have" in response.lower() or "not in the context" in response.lower() or "not find" in response.lower()

def test_hinglish_support(bot):
    """Verify that the bot can handle Hinglish queries."""
    query = "Kotak Large Cap Fund ka NAV kya hai?"
    response = bot.ask(query)
    
    assert response is not None
    assert "606.21" in response # Kotak Large Cap NAV is 606.21
