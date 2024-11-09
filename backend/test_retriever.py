import os
import pytest
from unittest.mock import patch, MagicMock
from retriever import Retriever

@pytest.fixture(autouse=True)
def setup_env():
    # This fixture ensures the environment variable is reset before each test
    if "EMBEDDINGS_MODEL" in os.environ:
        del os.environ["EMBEDDINGS_MODEL"]
    os.environ["AZURE_SEARCH_URI"] = "https://fake_search_uri"
    os.environ["AZURE_SEARCH_KEY"] = "fake_key"
    os.environ["DB_INDEX"] = "fake_index"

@patch("retriever.AzureOpenAIEmbeddings")
@patch("retriever.GoogleGenerativeAIEmbeddings")
@patch("retriever.AzureSearch")
def test_model_initialization_openai(mock_azure_search, mock_google_embeddings, mock_openai_embeddings, setup_env):
    # Test if OpenAI embeddings are used when EMBEDDINGS_MODEL is "openai"
    os.environ["EMBEDDINGS_MODEL"] = "openai"
    retriever = Retriever()
    
    mock_openai_embeddings.assert_called_once_with(model="ada-002", openai_api_version="2024-06-01")
    mock_google_embeddings.assert_not_called()

@patch("retriever.AzureOpenAIEmbeddings")
@patch("retriever.GoogleGenerativeAIEmbeddings")
@patch("retriever.AzureSearch")
def test_model_initialization_google(mock_azure_search, mock_google_embeddings, mock_openai_embeddings, setup_env):
    # Test if Google embeddings are used when EMBEDDINGS_MODEL is "google"
    os.environ["EMBEDDINGS_MODEL"] = "google"
    retriever = Retriever()
    
    mock_google_embeddings.assert_called_once_with(model="models/embedding-001")
    mock_openai_embeddings.assert_not_called()

@patch("retriever.AzureOpenAIEmbeddings")
@patch("retriever.AzureSearch")
def test_vector_store_initialization(mock_azure_search, mock_openai_embeddings, setup_env):
    # Test vector store initialization with environment variables
    os.environ["EMBEDDINGS_MODEL"] = "openai"

    retriever = Retriever()
    
    mock_azure_search.assert_called_once_with(
        azure_search_endpoint="https://fake_search_uri",
        azure_search_key="fake_key",
        index_name="fake_index",
        embedding_function=retriever.embeddings.embed_query
    )

@patch("retriever.AzureOpenAIEmbeddings")
@patch("retriever.AzureSearch")
def test_invoke_method(mock_azure_search, mock_openai_embeddings, setup_env):
    # Mock the similarity search response
    mock_docs = [MagicMock(page_content="Document 1"), MagicMock(page_content="Document 2"), MagicMock(page_content="Document 3")]
    mock_azure_search.return_value.similarity_search.return_value = mock_docs

    retriever = Retriever()
    query = {'input': 'sample query'}
    
    # Test invoke method
    result = retriever.invoke(query)
    
    mock_azure_search.return_value.similarity_search.assert_called_once_with('sample query', k=3)
    expected_result = "Document 1\n\nDocument 2\n\nDocument 3"
    assert result == expected_result
