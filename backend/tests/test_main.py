import pytest
from unittest.mock import MagicMock, patch, call
from main import generate_answer, store_feedback, get_feedback_count, get_chat_history, add_to_chat_history, delete_chat_history, ping_agents
from modules.models import QuestionModel, AnswerModel, FeedbackModel
from datetime import datetime


# Fixture to mock the setup function
@pytest.fixture(autouse=True)
def mock_setup():
    mock_setup = {}
    mock_setup["graph"] = MagicMock()
    mock_setup["feedback_table"] = MagicMock()
    mock_setup["history_table"] = MagicMock()
    MockAgent1 = MagicMock(check_connection=MagicMock())
    MockAgent2 = MagicMock(check_connection=MagicMock())
    agent_1 = MockAgent1.return_value
    agent_1.name = "agent1"
    agent_1.check_connection.return_value = {"healthy": True, "info": ""}
    agent_2 = MockAgent2.return_value
    agent_2.name = "agent2"
    agent_2.check_connection.return_value = {"healthy": False, "info": ""} 
    mock_setup["agents"] = [agent_1, agent_2]
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

class MockEntity(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

def test_ping_agents(mock_setup):
    response = ping_agents(setup=mock_setup)
    assert len(response) == 2
    assert response[0] == {"agent": "agent1", "healthy": True}
    assert response[1] == {"agent": "agent2", "healthy": False}

def test_generate_answer(mock_setup):
    mock_question = "What is the capital of France?"
    mock_answer = "This is a test answer"
    mock_history = [{"role": "user", "content": "hi!"}, {"role": "bot", "content": "hi! how can I help you?"}]
    mock_session_id = "1234"
    mock_graph = mock_setup["graph"]
    mock_graph.invoke.return_value = { "question": mock_question, "answer": mock_answer, "agents": {"agent_1": "agent answer", "agent_2": "agent answer"} }
    
    # Mock the interactions with the chat history
    with patch('main.get_chat_history') as MockGetChatHistory, \
         patch('main.add_to_chat_history') as MockAddToChatHistory:
        MockGetChatHistory.return_value = mock_history
        MockAddToChatHistory.return_value = None

        # Call the endpoint under test
        response = generate_answer(body=QuestionModel(session_id=mock_session_id, question=mock_question), setup=mock_setup)

        # Assert that the returned value has the final answer
        assert "answer" in response
        assert response["answer"] == mock_answer

        # Assert that the returned value has each of the agents answer
        assert "agents" in response
        assert "agent_1" in response["agents"]
        assert "agent_2" in response["agents"]

        # Assert that a call to retrieve the chat history was made
        MockGetChatHistory.assert_called_once()

        # Assert that a call to store the new chat in the history was made
        MockAddToChatHistory.assert_called_once()        

def test_store_feedback(mock_setup, mock_feedback):
    with patch('main.uuid') as MockId:
        mock_feedback_table = mock_setup["feedback_table"]
        mock_entity = MockEntity(PartitionKey="likes", RowKey="1", Question=mock_feedback.question, Answer=mock_feedback.answer, SessionId=mock_feedback.session_id)

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
        MockEntity(PartitionKey="likes", RowKey="1"),
        MockEntity(PartitionKey="likes", RowKey="2"),
        MockEntity(PartitionKey="hates", RowKey="3")
    ]

    # Call the endpoint under test
    response = get_feedback_count(setup=mock_setup)
    
    # Assertions to verify expected behavior
    mock_feedback_table.query_entities.assert_called_once_with(query_filter="PartitionKey eq 'likes' or PartitionKey eq 'hates'")
    assert "likes" in response
    assert response["likes"] == 2
    assert "hates" in response
    assert response["hates"] == 1

def test_get_chat_history(mock_setup):
    mock_history_table = mock_setup["history_table"]
    mock_session_id = "123"
    
    # Check results are sorted by timestamp
    mock_history_table.query_entities.return_value = [
        MockEntity(PartitionKey=mock_session_id, RowKey="2", role="bot", content="Paris", metadata={"timestamp": datetime(2024, 12, 18, 12, 0, 1)}),
        MockEntity(PartitionKey=mock_session_id, RowKey="4", role="bot", content="No", metadata={"timestamp": datetime(2024, 12, 18, 12, 0, 3)}),
        MockEntity(PartitionKey=mock_session_id, RowKey="1", role="user", content="What is the capital of France?", metadata={"timestamp": datetime(2024, 12, 18, 12, 0, 0)}),
        MockEntity(PartitionKey=mock_session_id, RowKey="3", role="user", content="Have you ever been to Paris?", metadata={"timestamp": datetime(2024, 12, 18, 12, 0, 2)}),
    ]
    response = get_chat_history(mock_session_id, setup=mock_setup)
    assert len(response) == 4
    assert response[0]["content"] == "What is the capital of France?"
    assert response[1]["content"] == "Paris"
    assert response[2]["content"] == "Have you ever been to Paris?"
    assert response[3]["content"] == "No"

    # Check session id was used to query the table
    mock_history_table.query_entities.assert_called_once_with(query_filter=f"PartitionKey eq '{mock_session_id}'")

    # Check results are limited to 4
    mock_history_table.query_entities.return_value = [
        MockEntity(PartitionKey=mock_session_id, RowKey="2", role="bot", content="Paris", metadata={"timestamp": datetime(2024, 12, 18, 12, 0, 1)}),
        MockEntity(PartitionKey=mock_session_id, RowKey="4", role="bot", content="No", metadata={"timestamp": datetime(2024, 12, 18, 12, 0, 3)}),
        MockEntity(PartitionKey=mock_session_id, RowKey="1", role="user", content="What is the capital of France?", metadata={"timestamp": datetime(2024, 12, 18, 12, 0, 0)}),
        MockEntity(PartitionKey=mock_session_id, RowKey="3", role="user", content="Have you ever been to Paris?", metadata={"timestamp": datetime(2024, 12, 18, 12, 0, 2)}),
        MockEntity(PartitionKey=mock_session_id, RowKey="6", role="bot", content="Yes", metadata={"timestamp": datetime(2024, 12, 18, 12, 0, 5)}),
        MockEntity(PartitionKey=mock_session_id, RowKey="5", role="user", content="Would you like to go there?", metadata={"timestamp": datetime(2024, 12, 18, 12, 0, 4)}),
    ]
    response = get_chat_history(mock_session_id, setup=mock_setup)
    assert len(response) == 4
    assert response[0]["content"] == "Have you ever been to Paris?"
    assert response[1]["content"] == "No"
    assert response[2]["content"] == "Would you like to go there?"
    assert response[3]["content"] == "Yes"

    # Check all the results are returned if they are less than 4
    mock_history_table.query_entities.return_value = [
        MockEntity(PartitionKey=mock_session_id, RowKey="2", role="bot", content="Paris", metadata={"timestamp": datetime(2024, 12, 18, 12, 0, 1)}),
        MockEntity(PartitionKey=mock_session_id, RowKey="1", role="user", content="What is the capital of France?", metadata={"timestamp": datetime(2024, 12, 18, 12, 0, 0)}),
    ]
    response = get_chat_history(mock_session_id, setup=mock_setup)
    assert len(response) == 2
    assert response[0]["content"] == "What is the capital of France?"
    assert response[1]["content"] == "Paris"

    # Check an empty list is returned if there is no history for the session id provided
    mock_history_table.query_entities.return_value = []
    response = get_chat_history(mock_session_id, setup=mock_setup)
    assert len(response) == 0

def test_add_to_chat_history(mock_setup, mock_answer):
    with patch('main.uuid') as MockId:  
        mock_history_table = mock_setup["history_table"]
        mock_user = MockEntity(PartitionKey=mock_answer.session_id, RowKey="123", role="user", content=mock_answer.question)
        mock_bot = MockEntity(PartitionKey=mock_answer.session_id, RowKey="123", role="bot", content=mock_answer.answer, agent_1="agent answer", agent_2="agent answer")
        MockId.uuid4.return_value = "123"
        
        # Mock create_entity to do nothing
        mock_history_table.create_entity.return_value = None
        
        # Call the endpoint under test
        response = add_to_chat_history(body=mock_answer, setup=mock_setup)

        # Assertions to verify expected behavior
        mock_history_table.create_entity.assert_has_calls([call(entity=mock_user), call(entity=mock_bot)])
        assert response == {"message": "Chat history updated successfully."}

def test_delete_chat_history(mock_setup):
    mock_history_table = mock_setup["history_table"]
    mock_session_id = "123"
    
    # Mock query_entities and delete_entity
    mock_history_table.query_entities.return_value = [
        MockEntity(PartitionKey=mock_session_id, RowKey="2", role="bot", content="Paris", metadata={"timestamp": datetime(2024, 12, 18, 12, 0, 1)}),
        MockEntity(PartitionKey=mock_session_id, RowKey="1", role="user", content="What is the capital of France?", metadata={"timestamp": datetime(2024, 12, 18, 12, 0, 0)}),
    ]
    mock_history_table.delete_entity.return_value = None

    # Call the endpoint under test
    response = delete_chat_history(mock_session_id, setup=mock_setup)

    # Assertions to verify expected behavior
    mock_history_table.query_entities.assert_called_once_with(f"PartitionKey eq '{mock_session_id}'")
    mock_history_table.delete_entity.assert_has_calls([call(partition_key=mock_session_id, row_key="2"), call(partition_key=mock_session_id, row_key="1")])
    assert response == {"message": "Deleted 2 records successfully."}