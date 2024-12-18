import pytest
from unittest.mock import MagicMock, patch
from backend.main import generate_answer, store_feedback
from backend.modules.models import QuestionModel, AnswerModel, FeedbackModel


# Fixture to mock the setup function
@pytest.fixture(autouse=True)
def mock_setup():
    mock_setup = MagicMock()
    mock_setup["graph"] = MagicMock()
    mock_setup["feedback_table"] = MagicMock()
    mock_setup["history_table"] = MagicMock()
    return mock_setup

# Fixtures to moch the payloads
@pytest.fixture(autouse=True)
def mock_question():
    return QuestionModel(session_id="1234", question="What is the capital of France?")

@pytest.fixture(autouse=True)
def mock_answer():
    return AnswerModel(session_id="1234", question="What is the capital of France?", answer="Paris", agents={ "agent_1": "agent answer", "agent_2": "agent answer" })

@pytest.fixture(autouse=True)
def mock_feedback():
    return FeedbackModel(session_id="1234", question="What is the capital of France?", answer="Paris", like=True)

#def test_generate_answer(mock_setup):
#    mock_question = "What is the capital of France?"
#    mock_answer = "This is a test answer"
#    mock_graph = mock_setup["graph"]
#    mock_graph.invoke.return_value = { "question": mock_question, "answer": mock_answer, "agent_1": "agent answer", "agent_2": "agent answer"}
#
#    # Call the endpoint under test
#    response = generate_answer(body=QuestionModel(session_id="1234", question=mock_question), setup=mock_setup)
#
#    # Assert the the returned value has the final answer
#    assert "answer" in response
#    assert response["answer"] == mock_answer
#
#    # Assert that the returned value has the agents answer
#    assert "agents" in response
#    assert "agent_1" in response["agents"]
#    assert "agent_2" in response["agents"]

def test_store_feedback(mock_setup, mock_feedback):
    with patch('backend.main.uuid') as MockId:
        mock_feedback_table = mock_setup["feedback_table"]
        mock_entity = {
            "PartitionKey": "likes",
            "RowKey": "1234",
            "Question": mock_feedback.question,
            "Answer": mock_feedback.answer,
            "SessionId": mock_feedback.session_id
        }

        # Mock the row key generation
        MockId.uuid4.return_value = mock_entity["RowKey"]
                
        # Mock entity creation
        mock_feedback_table.create_entity.return_value = None

        # Call the endpoint under test
        response = store_feedback(body=mock_feedback, setup=mock_setup)

        # Assertions to verify expected behavior
        mock_feedback_table.create_entity.assert_called_once_with(entity=mock_entity)
        assert response == {"message": "Feedback stored successfully."}
