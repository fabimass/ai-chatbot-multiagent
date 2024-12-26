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

def test_get_relevant_agents(supervisor):
    # Mock LLM response
    supervisor.llm.return_value = "agent_1, agent_2"

    agents = supervisor.get_relevant_agents({"question": "test_question", "history": []})
    assert agents == { "relevant_agents": ["agent_1", "agent_2"] }

    # Assert that the user question and the list of agents were used when choosing relevant agents
    assert "test_question" in supervisor.llm.call_args[0][0].messages[1].content
    assert "agent_1" in supervisor.llm.call_args[0][0].messages[0].content
    assert "agent_2" in supervisor.llm.call_args[0][0].messages[0].content
    assert "agent_3" in supervisor.llm.call_args[0][0].messages[0].content

def test_generate_answer(supervisor):
    relevant_agents = ["agent_1", "agent_2", "agent_3"]   

    # Test picking the next agent
    state = {"question": "test_question", "relevant_agents": relevant_agents}
    result = supervisor.generate_answer(state)
    assert result == {"next": "agent_1"}

    state = {"agents": {"agent_1": "response_1"}, "question": "test_question", "relevant_agents": relevant_agents}
    result = supervisor.generate_answer(state)
    assert result == {"next": "agent_2"}

    state = {"agents": {"agent_1": "response_1", "agent_2": "response_2"}, "question": "test_question", "relevant_agents": relevant_agents}
    result = supervisor.generate_answer(state)
    assert result == {"next": "agent_3"}
    
    # Test when all agents have responded
    state = {"agents": {"agent_1": "response_1", "agent_2": "response_2", "agent_3": "response_3"}, "question": "test_question", "relevant_agents": relevant_agents}
    result = supervisor.generate_answer(state)
    assert result == {"next": "FINISH"}