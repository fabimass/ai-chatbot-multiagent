import pytest
from fastapi.testclient import TestClient
from main import app, get_chat_history
from unittest.mock import patch

client = TestClient(app)

def test_ping():
    response = client.get("/api/ping")
    assert response.status_code == 200
    assert response.json() == "pong"

#@patch('modules.generator.Generator.invoke', return_value="This is a mock answer")
#@patch('main.get_chat_history', return_value=[])
#def test_generate_answer(mock_get_chat_history, mock_invoke):
#    body = {"session_id": "1234", "question": "What is AI?"}
#    response = client.post("/api/ask", json=body)
#    assert response.status_code == 200
#    assert response.json() == {"question": "What is AI?", "answer": "This is a mock answer"}
#    mock_invoke.assert_called_once_with("What is AI?", [])
#    mock_get_chat_history.assert_called_once_with("1234")