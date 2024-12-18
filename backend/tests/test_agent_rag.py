import pytest
from unittest.mock import MagicMock, patch
from backend.modules.models import State
from backend.modules.agent_rag import AgentRag

@pytest.fixture
def config():
    return {
        "agent_name": "RAG Agent Test",
        "azure_search_endpoint": "https://mock-search-endpoint",
        "azure_search_key": "mock-key",
        "index_name": "mock-index",
        "embeddings": "openai"
    }

@pytest.fixture
def agent_rag(config):
    with patch('backend.modules.agent_rag.AzureOpenAIEmbeddings') as MockEmbeddings, \
         patch('backend.modules.agent_rag.AzureSearch') as MockAzureSearch, \
         patch('backend.modules.agent_rag.AzureChatOpenAI') as MockLLM:
        
        # Mock the embeddings, vector store, and LLM
        MockEmbeddings.return_value = MagicMock(embed_query=MagicMock())
        MockAzureSearch.return_value = MagicMock(similarity_search=MagicMock())
        MockLLM.return_value = MagicMock()
        
        return AgentRag(config)

def test_retrieve_context(agent_rag):
    mock_query = "Mock query"
    mock_docs = [MagicMock(page_content="Document 1"), MagicMock(page_content="Document 2")]
    
    # Mock similarity search results
    agent_rag.vstore.similarity_search.return_value = mock_docs

    # Call the method under test
    context = agent_rag.retrieve_context(mock_query)

    # Assertions to verify expected behavior
    agent_rag.vstore.similarity_search.assert_called_once_with(mock_query, k=3)
    assert context == "Document 1\n\nDocument 2"

def test_generate_answer(agent_rag):
    mock_question = "Mock question"
    mock_context = "Mock context"
    mock_answer = "Mock answer"
    mock_state = State({"question": mock_question})

    # Mock context retrieval and chain invocation
    agent_rag.retrieve_context = MagicMock(return_value=mock_context)
    agent_rag.rag_chain = MagicMock()
    agent_rag.rag_chain.invoke.return_value = mock_answer

    # Call the method under test
    response = agent_rag.generate_answer(mock_state)

    # Assertions to verify expected behavior
    agent_rag.retrieve_context.assert_called_once_with(mock_question)
    agent_rag.rag_chain.invoke.assert_called_once_with({"question": mock_question, "context": mock_context})
    assert response == {"agent_rag": mock_answer}

def test_initialization_with_config(config):
    # Test initialization with different embeddings configurations
    with patch('backend.modules.agent_rag.AzureOpenAIEmbeddings') as MockOpenAIEmbeddings, \
         patch('backend.modules.agent_rag.GoogleGenerativeAIEmbeddings') as MockGoogleEmbeddings, \
         patch('backend.modules.agent_rag.AzureSearch') as MockAzureSearch, \
         patch('backend.modules.agent_rag.AzureChatOpenAI') as MockLLM:
        
        # Test with OpenAI embeddings
        agent = AgentRag(config)
        MockOpenAIEmbeddings.assert_called_once_with(model="ada-002", openai_api_version="2024-06-01")
        assert isinstance(agent.embeddings, MagicMock)

        # Test with Google embeddings
        config["embeddings"] = "google"
        agent = AgentRag(config)
        MockGoogleEmbeddings.assert_called_once_with(model="models/embedding-001")
        assert isinstance(agent.embeddings, MagicMock)
