import pytest
from unittest.mock import MagicMock, patch
from modules.models import State
from modules.agent_sql import AgentSql

@pytest.fixture
def config():
    return {
        "agent_name": "SQL Agent Test",
        "agent_directive": "You are a SQL agent",
        "connection_string": "mock-connection-string"
    }

@pytest.fixture
def test_variables():
    return {
        "mock_schema": [
            ('dbo', 'users', 'id', 'int'),
            ('dbo', 'users', 'name', 'nvarchar')
        ],
        "mock_question": "What are the names of all users?",
        "mock_raw_query": "```sql\nSELECT name\nFROM users LIMIT 5;\n```",
        "mock_fixed_query": "```sql\nSELECT TOP(5) name\nFROM users;\n```",
        "mock_cleaned_query": "SELECT TOP(5) name FROM users;",
        "mock_query_result": [("Alice"), ("Bob")],
        "mock_answer": "The users are Alice and Bob",
        "mock_history": [{"role": "user", "content": "hi!"}, {"role": "bot", "content": "hi! how can I help you?"}]
    }

@pytest.fixture
def agent_sql(config):
    with patch('modules.agent_sql.SQLDatabase') as MockSQL, \
         patch('modules.agent_sql.AzureChatOpenAI') as MockLLM:
        
        # Mock the SQL connection and LLM
        MockSQL.return_value = MagicMock(from_uri=MagicMock())
        MockLLM.return_value = MagicMock()
        
        return AgentSql(config)

def test_check_connection_success(agent_sql):
    agent_sql.db.run = MagicMock(return_value=None)
    assert agent_sql.check_connection() is True

def test_check_connection_failure(agent_sql):
    agent_sql.db.run = MagicMock(side_effect=Exception("Connection error"))
    assert agent_sql.check_connection() is False

def test_get_schema(agent_sql, test_variables):
    agent_sql.db.run = MagicMock(return_value=test_variables["mock_schema"])
    schema = agent_sql.get_schema()
    assert schema == test_variables["mock_schema"]
    agent_sql.db.run.assert_called_once_with(
        "SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS"
    )

def test_generate_query(agent_sql, test_variables):
    # Mock LLM response
    agent_sql.llm.side_effect = [test_variables["mock_raw_query"], test_variables["mock_fixed_query"]]
    
    # Call the method under test
    generated_query = agent_sql.generate_query(test_variables["mock_question"], test_variables["mock_schema"], test_variables["mock_history"])
    
    # Assert that the user question and the schema were used when generating the query
    assert test_variables["mock_question"] in agent_sql.llm.call_args_list[0][0][0].messages[1].content
    assert str(test_variables["mock_schema"]) in agent_sql.llm.call_args_list[0][0][0].messages[0].content

    # Assert that the previously generated query was used when looking for mistakes
    assert test_variables["mock_raw_query"] in agent_sql.llm.call_args_list[1][0][0].messages[1].content

    # Assert the agent is aware of the chat history
    assert str(test_variables["mock_history"]) in agent_sql.llm.call_args_list[0][0][0].messages[0].content

    # Assert generated query
    assert generated_query == test_variables["mock_cleaned_query"]

def test_run_query(agent_sql, test_variables):   
    # Mock the query execution
    agent_sql.db.run = MagicMock(return_value=test_variables["mock_query_result"])
    
    # Call the method under test
    result = agent_sql.run_query(test_variables["mock_cleaned_query"])

    # Assertions to verify expected behavior
    assert result == test_variables["mock_query_result"]
    agent_sql.db.run.assert_called_once_with(test_variables["mock_cleaned_query"])

def test_generate_answer(agent_sql, test_variables, config):
    # Mock already tested methods
    agent_sql.get_schema = MagicMock(return_value=test_variables["mock_schema"])
    agent_sql.generate_query = MagicMock(return_value=test_variables["mock_cleaned_query"])
    agent_sql.run_query = MagicMock(return_value=test_variables["mock_query_result"])
    
    # Mock LLM response
    agent_sql.llm.return_value = test_variables["mock_answer"]
    
    # Call the method under test
    answer = agent_sql.generate_answer(State({"question": test_variables["mock_question"], "history": test_variables["mock_history"]}))

    # Assert that the user question, the generated query and the query result were used when generating an answer
    assert test_variables["mock_question"] in agent_sql.llm.call_args[0][0].messages[1].content
    assert test_variables["mock_cleaned_query"] in agent_sql.llm.call_args[0][0].messages[0].content
    assert str(test_variables["mock_query_result"]) in agent_sql.llm.call_args[0][0].messages[0].content

    # Assert the agent is aware of its own skills
    assert config["agent_directive"] in agent_sql.llm.call_args[0][0].messages[0].content
    
    # Assert the agent is aware of the chat history
    assert str(test_variables["mock_history"]) in agent_sql.llm.call_args[0][0].messages[0].content

    # Assert the final answer
    assert answer == {"agent_sql": test_variables["mock_answer"]}