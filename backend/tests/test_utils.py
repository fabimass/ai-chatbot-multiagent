import pytest
from modules.utils import filter_agent_history

@pytest.fixture
def history():
    return [
        {
            "role": "user", "content": "hello"
        },
        {
            "role": "bot",
            "content": "Hi, how can I help you?",
            "agent_rag": "Hello, this is RAG agent.",
            "agent_sql": "Hello, this is SQL agent.",
            "agent_csv": "Hello, this is CSV agent."
        },
        {
            "role": "user", "content": "test message"
        },
        {
            "role": "bot",
            "content": "Default bot response.",
            "agent_rag": "RAG specific response.",
            "agent_sql": "SQL specific response.",
            "agent_csv": "CSV specific response."
        }
    ]

def test_filter_agent_history(history):
    
    # Test agent_rag
    result = filter_agent_history(history, "agent_rag")
    expected = [
        {"role": "user", "content": "hello"},
        {"role": "bot", "content": "Hello, this is RAG agent."},
        {"role": "user", "content": "test message"},
        {"role": "bot", "content": "RAG specific response."}
    ]
    assert result == expected

    # Test agent_sql
    result = filter_agent_history(history, "agent_sql")
    expected = [
        {"role": "user", "content": "hello"},
        {"role": "bot", "content": "Hello, this is SQL agent."},
        {"role": "user", "content": "test message"},
        {"role": "bot", "content": "SQL specific response."}
    ]
    assert result == expected

    # Test agent_csv
    result = filter_agent_history(history, "agent_csv")
    expected = [
        {"role": "user", "content": "hello"},
        {"role": "bot", "content": "Hello, this is CSV agent."},
        {"role": "user", "content": "test message"},
        {"role": "bot", "content": "CSV specific response."}
    ]
    assert result == expected

    # Test non-existent
    result = filter_agent_history(history, "nonexistent")
    expected = [
        {"role": "user", "content": "hello"},
        {"role": "user", "content": "test message"},
    ]
    assert result == expected

    # Test empty history
    result = filter_agent_history([], "rag")
    assert result == []