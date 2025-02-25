import pytest
from unittest.mock import MagicMock, patch
from modules.models import State
from modules.summarizer import Summarizer

@pytest.fixture
def summarizer():
    with patch('modules.summarizer.AzureChatOpenAI') as MockLLM:
        # Mock the LLM
        MockLLM.return_value = MagicMock()
        return Summarizer()

def test_generate_answer(summarizer):
    # Mock state
    mock_question = "This is a test question"
    mock_agent_1_output = "response_1"
    mock_agent_2_output = "response_2"
    mock_agent_3_output = "response_3"
    state = {"agents": {"agent_1": mock_agent_1_output, "agent_2": mock_agent_2_output, "agent_3": mock_agent_3_output}, "question": mock_question }

    # Mock LLM response
    mock_answer = "This is a test answer"
    summarizer.llm.return_value = mock_answer

    # Call the method under test
    response = summarizer.generate_answer(State(state))
    
    # Assert that the user question and each of the agents outputs were used when generating an answer
    assert mock_question in summarizer.llm.call_args[0][0].messages[1].content
    assert mock_agent_1_output in summarizer.llm.call_args[0][0].messages[0].content
    assert mock_agent_2_output in summarizer.llm.call_args[0][0].messages[0].content
    assert mock_agent_3_output in summarizer.llm.call_args[0][0].messages[0].content

    # Assert the final answer
    assert response == {"answer": mock_answer}