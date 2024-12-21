import pytest
from unittest.mock import MagicMock, patch
from modules.models import State
from modules.agent_csv import AgentCsv
import pandas as pd

@pytest.fixture
def config():
    return {
        "agent_name": "CSV Agent Test",
        "agent_directive": "You are a CSV agent",
        "connection_string": "mock-connection-string",
        "container_name": "mock-container",
        "index_file_name": "mock-index.csv"
    }

@pytest.fixture
def test_variables():
    return {
        "mock_question": "This is a test question",
        "mock_raw_code": "```python\nresult=1\n```",
        "mock_fixed_code": "```python\nresult=1\n```",
        "mock_cleaned_code": "result=1",
        "mock_code_result": 1,
        "mock_answer": "This is a test answer",
        "mock_index": "col1,col2\nval1,val2",
        "mock_relevant_files": ["file1.csv", "file2.csv"],
        "mock_context": "col1,col2\nval1,val2\nval3,val4\nval5,val6\nval7,val8\nval9,val10",
        "mock_history": [{"role": "user", "content": "hi!"}, {"role": "bot", "content": "hi! how can I help you?"}]
    }

@pytest.fixture
def agent_csv(config):
    with patch('modules.agent_csv.BlobServiceClient') as MockBlob, \
         patch('modules.agent_csv.AzureChatOpenAI') as MockLLM:
        
        # Mock the blob client and LLM
        MockBlob.return_value = MagicMock(from_connection_string=MagicMock())
        MockLLM.return_value = MagicMock()
        
        return AgentCsv(config)

def test_get_index(agent_csv, test_variables):
    # Mock Azure Blob Storage responses
    mock_blob_client = MagicMock()
    agent_csv.blob_service_client.get_blob_client.return_value = mock_blob_client
    mock_blob_client.download_blob.return_value.content_as_text.return_value = test_variables["mock_index"]

    # Call the method under test
    index = agent_csv.get_index()

    # Assert the result is a pandas dataframe
    assert isinstance(index, pd.DataFrame)
    assert index.equals(pd.DataFrame({"col1": ["val1"], "col2": ["val2"]}))

def test_get_relevant_files(agent_csv, test_variables):
    # Mock LLM response
    agent_csv.llm.side_effect = ["file1.csv, file2.csv", ""]

    # Test when the LLM provides a list of files
    files = agent_csv.get_relevant_files(test_variables["mock_question"], test_variables["mock_index"], test_variables["mock_history"])
    assert files == test_variables["mock_relevant_files"]

    # Test when the LLM doesn't provide any file
    files = agent_csv.get_relevant_files(test_variables["mock_question"], test_variables["mock_index"], test_variables["mock_history"])
    assert files == []

    # Assert that the user question and the index were used when choosing relevant files
    assert test_variables["mock_question"] in agent_csv.llm.call_args_list[0][0][0].messages[1].content
    assert test_variables["mock_index"] in agent_csv.llm.call_args_list[0][0][0].messages[0].content

    # Assert the agent is aware of the chat history
    assert str(test_variables["mock_history"]) in agent_csv.llm.call_args_list[0][0][0].messages[0].content

def test_get_files_head(agent_csv, test_variables):
    # Mock Azure Blob Storage responses
    mock_blob_client = MagicMock()
    agent_csv.blob_service_client.get_blob_client.return_value = mock_blob_client
    mock_blob_client.download_blob.return_value.content_as_text.return_value = test_variables["mock_context"]

    # Call the method under test
    files_head = agent_csv.get_files_head(["file1.csv", "file2.csv"])

    # Assertions to verify expected behavior
    assert "file1.csv" in files_head
    assert "file2.csv" in files_head
    assert len(files_head["file1.csv"]) == 5  # Expect 5 rows
    assert len(files_head["file2.csv"]) == 5  # Expect 5 rows
    assert files_head["file1.csv"][0]["col1"] == "val1"
    assert files_head["file2.csv"][0]["col1"] == "val1"

def test_generate_code(agent_csv, test_variables):
    # Mock LLM response
    agent_csv.llm.side_effect = [test_variables["mock_raw_code"], test_variables["mock_fixed_code"]]
    
    # Call the method under test
    generated_code = agent_csv.generate_code(test_variables["mock_question"], test_variables["mock_context"], test_variables["mock_history"])
    
    # Assert that the user question and the csv extract were used when generating the code
    assert test_variables["mock_question"] in agent_csv.llm.call_args_list[0][0][0].messages[1].content
    assert test_variables["mock_context"] in agent_csv.llm.call_args_list[0][0][0].messages[0].content

    # Assert that the previously generated code was used when looking for mistakes
    assert test_variables["mock_raw_code"] in agent_csv.llm.call_args_list[1][0][0].messages[1].content

    # Assert the agent is aware of the chat history
    assert str(test_variables["mock_history"]) in agent_csv.llm.call_args_list[0][0][0].messages[0].content

    # Assert generated code
    assert generated_code == test_variables["mock_cleaned_code"]

def test_run_code(agent_csv, test_variables):   
    # Call the method under test
    result = agent_csv.run_code(test_variables["mock_cleaned_code"])

    # Assertions to verify expected behavior
    assert result == test_variables["mock_code_result"]

def test_generate_answer_success(agent_csv, test_variables, config):
    # Mock already tested methods
    agent_csv.get_index = MagicMock(return_value=test_variables["mock_index"])
    agent_csv.get_relevant_files = MagicMock(return_value=test_variables["mock_relevant_files"])
    agent_csv.get_files_head = MagicMock(return_value=test_variables["mock_context"])
    agent_csv.generate_code = MagicMock(return_value=test_variables["mock_cleaned_code"])
    agent_csv.run_code = MagicMock(return_value=test_variables["mock_code_result"])
    
    # Mock LLM response
    agent_csv.llm.return_value = test_variables["mock_answer"]
    
    # Call the method under test
    answer = agent_csv.generate_answer(State({"question": test_variables["mock_question"], "history": test_variables["mock_history"]}))

    # Assert that the user question, the generated code and the code result were used when generating an answer
    assert test_variables["mock_question"] in agent_csv.llm.call_args[0][0].messages[1].content
    assert test_variables["mock_cleaned_code"] in agent_csv.llm.call_args[0][0].messages[0].content
    assert str(test_variables["mock_code_result"]) in agent_csv.llm.call_args[0][0].messages[0].content

    # Assert the agent is aware of its own skills
    assert config["agent_directive"] in agent_csv.llm.call_args[0][0].messages[0].content
    
    # Assert the agent is aware of the chat history
    assert str(test_variables["mock_history"]) in agent_csv.llm.call_args[0][0].messages[0].content

    # Assert the final answer
    assert answer == {"agent_csv": test_variables["mock_answer"]}

def test_generate_answer_error(agent_csv, test_variables):
    # Mock to raise an error
    agent_csv.get_index = MagicMock(side_effect=Exception("Mocked exception"))

    response = agent_csv.generate_answer(State({"question": test_variables["mock_question"], "history": test_variables["mock_history"]}))

    assert response == {"agent_csv": "I don't know"}