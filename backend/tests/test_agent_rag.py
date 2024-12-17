import pytest
from unittest.mock import MagicMock, patch
from modules.models import State
from modules.agent_rag import AgentRag

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
    with patch('modules.agent_rag.AzureOpenAIEmbeddings') as MockEmbeddings, \
         patch('modules.agent_rag.AzureSearch') as MockAzureSearch, \
         patch('modules.agent_rag.AzureChatOpenAI') as MockLLM:
        
        # Mock the embeddings, vector store, and LLM
        MockEmbeddings.return_value = MagicMock(embed_query=MagicMock())
        MockAzureSearch.return_value = MagicMock(similarity_search=MagicMock())
        MockLLM.return_value = MagicMock()
        
        return AgentRag(config)

def test_retrieve_context(agent_rag):
    # Mock similarity search results
    mock_docs = [MagicMock(page_content="Document 1"), MagicMock(page_content="Document 2")]
    agent_rag.vstore.similarity_search.return_value = mock_docs

    mock_query = "Mock query"
    context = agent_rag.retrieve_context(mock_query)

    agent_rag.vstore.similarity_search.assert_called_once_with(mock_query, k=3)
    assert context == "Document 1\n\nDocument 2"

#def test_generate_answer(agent_rag):
#    mock_question = "Mock question"
#    mock_context = "Mock context"
#    mock_answer = "Mock answer"
#
#    # Mock context retrieval and chain invocation
#    agent_rag.retrieve_context = MagicMock(return_value=mock_context)
#    agent_rag.rag_chain.invoke = MagicMock(return_value=mock_answer)
#
#    state = State({"question": mock_question})
#    response = agent_rag.generate_answer(state)
#
#    agent_rag.retrieve_context.assert_called_once_with(mock_question)
#    agent_rag.rag_chain.invoke.assert_called_once_with({"question": mock_question, "context": mock_context})
#    assert response == {"agent_rag": mock_answer}

#def test_initialization_with_config(config):
#    # Test initialization with different embeddings configurations
#    with patch('langchain_openai.AzureOpenAIEmbeddings') as MockOpenAIEmbeddings, \
#         patch('langchain_google_genai.GoogleGenerativeAIEmbeddings') as MockGoogleEmbeddings, \
#         patch('langchain_community.vectorstores.azuresearch.AzureSearch') as MockAzureSearch:
#        
#        # Test with OpenAI embeddings
#        agent = AgentRag(config)
#        MockOpenAIEmbeddings.assert_called_once_with(model="ada-002", openai_api_version="2024-06-01")
#        assert isinstance(agent.embeddings, MagicMock)
#
#        # Test with Google embeddings
#        config["embeddings"] = "google"
#        agent = AgentRag(config)
#        MockGoogleEmbeddings.assert_called_once_with(model="ada-002", openai_api_version="2024-06-01")
