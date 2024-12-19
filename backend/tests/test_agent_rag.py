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
def test_variables():
    return {
        "mock_question": "What is the capital of France?",
        "mock_relevant_docs": [MagicMock(metadata={'source': 'visit-france.pdf', 'page': 1}, page_content='France is a country in Europe. Paris is its capital.'), MagicMock(metadata={'source': 'visit-france.pdf', 'page': 3}, page_content='Paris, the beautiful french capital, is known for the Eiffel Tower and Notre Dame cathedral.')],
        "mock_context": "France is a country in Europe. Paris is its capital.\n\nParis, the beautiful french capital, is known for the Eiffel Tower and Notre Dame cathedral.",
        "mock_answer": "The capital of France is Paris"
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

def test_retrieve_context(agent_rag, test_variables):    
    # Mock similarity search results
    agent_rag.vstore.similarity_search.return_value = test_variables["mock_relevant_docs"]

    # Call the method under test
    context = agent_rag.retrieve_context(test_variables["mock_question"])

    # Assert similarity search was called with the correct parameters
    agent_rag.vstore.similarity_search.assert_called_once_with(test_variables["mock_question"], k=3)

    # Assert constructed context
    assert context == test_variables["mock_context"]

def test_generate_answer(agent_rag, test_variables):
    # Mock context retrieval and LLM invocation
    agent_rag.retrieve_context = MagicMock(return_value=test_variables["mock_context"])
    agent_rag.llm.return_value = test_variables["mock_answer"]

    # Call the method under test
    response = agent_rag.generate_answer(State({"question": test_variables["mock_question"]}))

    # Assert that a call to retrieve context was done
    agent_rag.retrieve_context.assert_called_once_with(test_variables["mock_question"])
    
    # Assert that the user question and the context were used when generating an answer
    assert test_variables["mock_question"] in agent_rag.llm.call_args[0][0].messages[1].content
    assert test_variables["mock_context"] in agent_rag.llm.call_args[0][0].messages[0].content

    # Assert the final answer
    assert response == {"agent_rag": test_variables["mock_answer"]}

def test_embeddings_initialization(config):
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
