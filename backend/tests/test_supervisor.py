import pytest
from unittest.mock import MagicMock, patch
from backend.modules.models import State
from backend.modules.supervisor import Supervisor

@pytest.fixture
def supervisor():
    with patch('backend.modules.supervisor.AzureChatOpenAI') as MockLLM:
        # Mock the LLM
        MockLLM.return_value = MagicMock()
        # Mock available agents
        agents = ["agent_1", "agent_2", "agent_3"]
        
        return Supervisor(agents)

def test_pick_next_agent(supervisor):   
    # Test picking the next agent
    state = {"question": "test_question"}
    result = supervisor.pick_next_agent(state)
    assert result == {"next": "agent_1"}

    state = {"agent_1": "response_1", "question": "test_question"}
    result = supervisor.pick_next_agent(state)
    assert result == {"next": "agent_2"}

    state = {"agent_1": "response_1", "agent_2": "response_2", "question": "test_question"}
    result = supervisor.pick_next_agent(state)
    assert result == {"next": "agent_3"}
    
    # Test when all agents have responded
    state = {"agent_1": "response_1", "agent_2": "response_2", "agent_3": "response_3", "question": "test_question"}
    result = supervisor.pick_next_agent(state)
    assert result == {"next": "FINISH"}

def test_summarize(supervisor):
    # Mock state
    mock_question = "This is a test question"
    mock_agent_1_output = "response_1"
    mock_agent_2_output = "response_2"
    mock_agent_3_output = "response_3"
    state = {"agent_1": mock_agent_1_output, "agent_2": mock_agent_2_output, "agent_3": mock_agent_3_output, "question": mock_question}

    # Mock LLM response
    mock_answer = "This is a test answer"
    supervisor.llm.return_value = mock_answer

    # Call the method under test
    response = supervisor.summarize(State(state))
    
    # Assert that the user question and each of the agents outputs were used when generating an answer
    assert mock_question in supervisor.llm.call_args[0][0].messages[1].content
    assert mock_agent_1_output in supervisor.llm.call_args[0][0].messages[0].content
    assert mock_agent_2_output in supervisor.llm.call_args[0][0].messages[0].content
    assert mock_agent_3_output in supervisor.llm.call_args[0][0].messages[0].content

    # Assert the final answer
    assert response == {"answer": mock_answer}