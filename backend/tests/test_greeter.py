import pytest
from unittest.mock import MagicMock, patch
from modules.greeter import Greeter

@pytest.fixture
def greeter():
    with patch('modules.greeter.AzureChatOpenAI') as MockLLM:
        # Mock the LLM
        MockLLM.return_value = MagicMock()
        # Mock available agents
        MockAgent1 = MagicMock()
        MockAgent2 = MagicMock()
        agent_1 = MockAgent1.return_value
        agent_1.skills = "Agent 1 skills"
        agent_2 = MockAgent2.return_value
        agent_2.skills = "Agent 2 skills"
        agents = [agent_1, agent_2]

        return Greeter(agents)

def test_generate_answer(greeter):
    # Mock LLM response
    mock_answer = "This is a test answer"
    greeter.llm.return_value = mock_answer

    # Call the method under test
    response = greeter.generate_answer()
    
    # Assert that the skills of each agent were used when generating an answer
    assert "Agent 1 skills" in greeter.llm.call_args[0][0].messages[0].content
    assert "Agent 2 skills" in greeter.llm.call_args[0][0].messages[0].content

    # Assert the final answer
    assert response == {"answer": mock_answer}