import pytest
from unittest.mock import MagicMock, patch, call
from modules.models import State
from modules.graph import Graph

@pytest.fixture
def mock_supervisor():
    # Mock the supervisor with required methods
    supervisor = MagicMock()
    supervisor.pick_next_agent = MagicMock()
    supervisor.summarize = MagicMock()
    return supervisor

@pytest.fixture
def mock_agents():
    # Mock a list of agents
    MockAgent1 = MagicMock(generate_answer=MagicMock())
    MockAgent2 = MagicMock(generate_answer=MagicMock())
    agent_1 = MockAgent1.return_value
    agent_1.name = "agent1"
    agent_2 = MockAgent2.return_value
    agent_2.name = "agent2"   
    return [agent_1, agent_2]

def test_graph_initialization(mock_supervisor, mock_agents):
    with patch("modules.graph.StateGraph") as MockStateGraph, \
         patch("modules.graph.RunnableLambda") as MockRunnableLambda:
        
        MockStateGraph.return_value = MagicMock()

        # Create the Graph instance
        graph = Graph(mock_supervisor, mock_agents)
        
        # Verify StateGraph initialization
        MockStateGraph.assert_called_once_with(State)

        # Verify nodes are added
        calls_add_node = [
            call("supervisor_node", mock_supervisor.pick_next_agent),
            call("summarizer_node", mock_supervisor.summarize),
            call("agent1_node", mock_agents[0].generate_answer),
            call("agent2_node", mock_agents[1].generate_answer),
        ]
        MockStateGraph.return_value.add_node.assert_has_calls(calls_add_node, any_order=True)

        # Verify conditional edges
        MockStateGraph.return_value.add_conditional_edges.assert_called_once_with(
            "supervisor_node",
            MockRunnableLambda.return_value,
            {
                "agent1": "agent1_node",
                "agent2": "agent2_node",
                "FINISH": "summarizer_node",
            }
        )

        # Verify edges back to supervisor
        calls_add_edge = [
            call("agent1_node", "supervisor_node"),
            call("agent2_node", "supervisor_node"),
        ]
        MockStateGraph.return_value.add_edge.assert_has_calls(calls_add_edge, any_order=True)

        # Verify entry point and graph compilation
        MockStateGraph.return_value.set_entry_point.assert_called_once_with("supervisor_node")
        MockStateGraph.return_value.compile.assert_called_once()