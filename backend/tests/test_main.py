import pytest
from unittest.mock import MagicMock, patch, call
from backend.main import generate_answer, store_feedback, get_feedback_count
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

def test_get_feedback_count(mock_setup):
    mock_feedback_table = mock_setup["feedback_table"]
    
    # Mock query_entities to return a fake history
    mock_feedback_table.query_entities.return_value = [
        {"PartitionKey": "123", "RowKey": "1"},
        {"PartitionKey": "123", "RowKey": "2"},
        {"PartitionKey": "123", "RowKey": "3"}
    ]

    # Call the endpoint under test
    response = get_feedback_count(setup=mock_setup)
    
    # Assertions to verify expected behavior
    mock_feedback_table.query_entities.assert_has_calls([call(query_filter="PartitionKey eq 'likes'"), call(query_filter="PartitionKey eq 'hates'")])
    assert "likes" in response
    assert response["likes"] == 3
    assert "hates" in response
    assert response["hates"] == 3

#def test_get_chat_history(mock_setup):
#    mock_history_table = mock_setup["history_table"]
#    
#    # Mock query_entities to return a fake history
#    mock_history_table.query_entities.return_value = [
#        {"PartitionKey": "123", "RowKey": "1", "role": "user", "content": "What is the capital of France?"},
#        {"PartitionKey": "123", "RowKey": "2", "role": "bot", "content": "Paris"}
#    ]
#
#    response = client.get("/api/history/123")
#
#    assert len(response) == 2
#    assert response[0]["role"] == "user"
#    assert response[1]["role"] == "bot"
#
#
## Test for /api/history endpoint
#def test_add_to_chat_history(mock_setup):
#    mock_history_table = mock_setup["history_table"]
#    
#    # Mock create_entity to do nothing (successful)
#    mock_history_table.create_entity.return_value = None
#
#    body = {
#        "session_id": "123",
#        "question": "What is the capital of France?",
#        "answer": "Paris"
#    }
#    response = client.post("/api/history", json=body)
#
#    assert response.status_code == 200
#    assert response.json()["message"] == "Chat history updated successfully."
#
#
## Test for /api/history/{session_id} delete endpoint
#def test_delete_chat_history(mock_setup):
#    mock_history_table = mock_setup["history_table"]
#    
#    # Mock query_entities and delete_entity
#    mock_history_table.query_entities.return_value = [
#        {"PartitionKey": "123", "RowKey": "1", "role": "user", "content": "What is the capital of France?"},
#        {"PartitionKey": "123", "RowKey": "2", "role": "bot", "content": "Paris"}
#    ]
#    mock_history_table.delete_entity.return_value = None
#
#    response = client.delete("/api/history/123")
#
#    assert response.status_code == 200
#    assert response.json()["message"] == "Deleted 2 records successfully."