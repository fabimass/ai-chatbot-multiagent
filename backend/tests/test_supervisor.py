import pytest
from unittest.mock import MagicMock, patch
from modules.supervisor import Supervisor

@pytest.fixture
def supervisor():
    with patch('modules.supervisor.AzureChatOpenAI') as MockLLM:
        # Mock the LLM
        MockLLM.return_value = MagicMock()
        # Mock available agents
        MockAgent1 = MagicMock()
        MockAgent2 = MagicMock()
        MockAgent3 = MagicMock()
        agent_1 = MockAgent1.return_value
        agent_1.name = "agent_1"
        agent_2 = MockAgent2.return_value
        agent_2.name = "agent_2"
        agent_3 = MockAgent3.return_value
        agent_3.name = "agent_3"
        agents = [agent_1, agent_2, agent_3]
        
        return Supervisor(agents)

def test_generate_answer(supervisor):   
    # Test picking the next agent
    state = {"question": "test_question"}
    result = supervisor.generate_answer(state)
    assert result == {"next": "agent_1"}

    state = {"agents": {"agent_1": "response_1"}, "question": "test_question"}
    result = supervisor.generate_answer(state)
    assert result == {"next": "agent_2"}

    state = {"agents": {"agent_1": "response_1", "agent_2": "response_2"}, "question": "test_question"}
    result = supervisor.generate_answer(state)
    assert result == {"next": "agent_3"}
    
    # Test when all agents have responded
    state = {"agents": {"agent_1": "response_1", "agent_2": "response_2", "agent_3": "response_3"}, "question": "test_question"}
    result = supervisor.generate_answer(state)
    assert result == {"next": "FINISH"}