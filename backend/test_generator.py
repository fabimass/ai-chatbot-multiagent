import pytest
from unittest.mock import MagicMock, patch
from generator import Generator

@pytest.fixture
def mock_retriever():
    # Mock the retriever that will provide context
    retriever = MagicMock()
    retriever.invoke.return_value = "This is a mock context."
    return retriever

@pytest.fixture
@patch("generator.AzureChatOpenAI")
@patch("generator.ChatPromptTemplate")
@patch("generator.StrOutputParser")
@patch("generator.RunnablePassthrough")
def generator_with_mocks(mock_runnable, mock_parser, mock_prompt_template, mock_azure_chat, mock_retriever):
    # Set up mocks for each of the LLM, prompt template, parser, and passthrough
    mock_prompt_template.from_messages.return_value = mock_prompt_template
    mock_parser.return_value.parse.return_value = "Parsed answer"
    mock_azure_chat.return_value = mock_azure_chat
    mock_runnable.return_value = mock_runnable

    # Instantiate Generator with a mock retriever
    return Generator(mock_retriever)

def test_generator_initialization(generator_with_mocks):
    # Test that all components are properly instantiated
    generator = generator_with_mocks

    # Check if the LLM, prompt, parser, and chain are initialized
    assert generator.llm is not None
    assert generator.prompt is not None
    assert generator.parser is not None
    assert generator.rag_chain is not None

def test_generator_invoke(generator_with_mocks, mock_retriever):
    # Given a user question, test if invoke calls the chain and returns the expected answer
    generator = generator_with_mocks
    user_question = "What is the final project about?"
    
    # Mock the rag_chain's invoke method to return a simulated response
    generator.rag_chain.invoke = MagicMock(return_value="Mocked LLM response")
    
    # Call invoke with the user question
    response = generator.invoke(user_question)
    
    # Check that the invoke method in rag_chain was called with the correct input
    generator.rag_chain.invoke.assert_called_once_with({"input": user_question})
    
    # Verify the output
    assert response == "Mocked LLM response"
