import pytest
from unittest.mock import MagicMock, patch
from modules.models import State
from modules.agent_api import AgentApi
import yaml
import json

@pytest.fixture
def config():
    return {
        "agent_id": "api",
        "agent_directive": "You are an API agent",
        "spec_url": "https://mock-url",
        "spec_format": "json",
        "endpoint_filter": []
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
        "mock_spec_yaml": """openapi: 3.0.1
servers:
  - url: https://api.example.com/v1
paths:
  /endpoint1:
    get:
      summary: Endpoint 1
  /endpoint2:
    get:
      summary: Endpoint 2
""",
        "mock_spec_json": """{
  "openapi": "3.0.1",
  "servers": [
    {
      "url": "https://api.example.com/v1"
    }
  ],
  "paths": {
    "/endpoint1": {
      "get": {
        "summary": "Endpoint 1"
      }
    },
    "/endpoint2": {
      "get": {
        "summary": "Endpoint 2"
      }
    }
  }
}
""",
        "mock_relevant_endpoints": ["/endpoint1", "/endpoint2"],
        "mock_context": "Endpoint details",
        "mock_history": [{"role": "user", "content": "hi!"}, {"role": "bot", "content": "hi! how can I help you?"}]
    }

@pytest.fixture
def agent_api(config, test_variables):
    with patch('modules.agent_api.AzureChatOpenAI') as MockLLM, \
         patch('modules.agent_api.requests') as MockRequests:
        
        # Mock LLM and API specification
        MockLLM.return_value = MagicMock()
        MockRequests.get.return_value.text = test_variables["mock_spec_json"]
         
        return AgentApi(config)

def test_get_spec(agent_api, test_variables):
    with patch('modules.agent_api.requests') as MockRequests:
        
        # Test JSON specification
        MockRequests.get.return_value.text = test_variables["mock_spec_json"]
        base_url, endpoints, spec = agent_api.get_spec("json")

        assert spec == json.loads(test_variables["mock_spec_json"])
        assert base_url == "https://api.example.com/v1"
        assert len(endpoints) == 2

        # Test YAML specification
        MockRequests.get.return_value.text = test_variables["mock_spec_yaml"]
        base_url, endpoints, spec = agent_api.get_spec("yaml")

        assert spec == yaml.safe_load(test_variables["mock_spec_yaml"])
        assert base_url == "https://api.example.com/v1"
        assert len(endpoints) == 2

def test_get_relevant_endpoints(agent_api, test_variables):
    # Mock LLM response
    agent_api.llm.side_effect = ["/endpoint1, /endpoint2", ""]

    # Test when the LLM provides a list of endpoints
    endpoints = agent_api.get_relevant_endpoints(test_variables["mock_question"], test_variables["mock_history"])
    assert endpoints == test_variables["mock_relevant_endpoints"]

    # Test when the LLM doesn't provide any file
    endpoints = agent_api.get_relevant_endpoints(test_variables["mock_question"], test_variables["mock_history"])
    assert endpoints == []

    # Assert that the user question and the list of endpoints were used when choosing relevant endpoints
    assert test_variables["mock_question"] in agent_api.llm.call_args_list[0][0][0].messages[1].content
    assert str([('GET', '/endpoint1', 'Endpoint 1'), ('GET', '/endpoint2', 'Endpoint 2')]) in agent_api.llm.call_args_list[0][0][0].messages[0].content

    # Assert the agent is aware of the chat history
    assert str(test_variables["mock_history"]) in agent_api.llm.call_args_list[0][0][0].messages[0].content

def test_get_endpoint_details(agent_api, test_variables):

    # Call the method under test
    details = agent_api.get_endpoint_details(test_variables["mock_relevant_endpoints"])
    
    # Assertions to verify expected behavior
    assert len(details) == 2
    assert "/endpoint1" in details
    assert "/endpoint2" in details

def test_generate_code(agent_api, test_variables):
    # Mock LLM response
    agent_api.llm.side_effect = [test_variables["mock_raw_code"], test_variables["mock_fixed_code"]]
    
    # Call the method under test
    generated_code = agent_api.generate_code(test_variables["mock_question"], test_variables["mock_context"], test_variables["mock_history"])
    
    # Assert that the user question and the endpoint details were used when generating the code
    assert test_variables["mock_question"] in agent_api.llm.call_args_list[0][0][0].messages[1].content
    assert test_variables["mock_context"] in agent_api.llm.call_args_list[0][0][0].messages[0].content

    # Assert that the previously generated code was used when looking for mistakes
    assert test_variables["mock_raw_code"] in agent_api.llm.call_args_list[1][0][0].messages[1].content

    # Assert the agent is aware of the chat history
    assert str(test_variables["mock_history"]) in agent_api.llm.call_args_list[0][0][0].messages[0].content

    # Assert generated code
    assert generated_code == test_variables["mock_cleaned_code"]

def test_run_code(agent_api, test_variables):   
    # Call the method under test
    result = agent_api.run_code(test_variables["mock_cleaned_code"])

    # Assertions to verify expected behavior
    assert result == test_variables["mock_code_result"]

def test_generate_answer_complete_flow(agent_api, test_variables, config):
    with patch('modules.agent_api.filter_agent_history') as MockFilterAgentHistory:
        MockFilterAgentHistory.return_value = test_variables["mock_history"]

        # Mock already tested methods
        agent_api.get_relevant_endpoints = MagicMock(return_value=test_variables["mock_relevant_endpoints"])
        agent_api.get_endpoint_details = MagicMock(return_value=test_variables["mock_context"])
        agent_api.generate_code = MagicMock(return_value=test_variables["mock_cleaned_code"])
        agent_api.run_code = MagicMock(return_value=test_variables["mock_code_result"])
        
        # Mock LLM response (the entry point asks for more information)
        agent_api.llm.side_effect = ["CONTINUE", test_variables["mock_answer"]]
        
        # Call the method under test
        answer = agent_api.generate_answer(State({"question": test_variables["mock_question"], "history": test_variables["mock_history"]}))

        # Assert that the user question, the generated code and the code result were used when generating an answer
        assert test_variables["mock_question"] in agent_api.llm.call_args_list[0][0][0].messages[1].content
        assert test_variables["mock_question"] in agent_api.llm.call_args_list[1][0][0].messages[1].content
        assert test_variables["mock_cleaned_code"] not in agent_api.llm.call_args_list[0][0][0].messages[0].content
        assert test_variables["mock_cleaned_code"] in agent_api.llm.call_args_list[1][0][0].messages[0].content
        assert str(test_variables["mock_code_result"]) not in agent_api.llm.call_args_list[0][0][0].messages[0].content
        assert str(test_variables["mock_code_result"]) in agent_api.llm.call_args_list[1][0][0].messages[0].content

        # Assert the agent is aware of its own skills
        assert config["agent_directive"] in agent_api.llm.call_args_list[0][0][0].messages[0].content
        assert config["agent_directive"] not in agent_api.llm.call_args_list[1][0][0].messages[0].content
        
        # Assert the agent is aware of the chat history
        assert str(test_variables["mock_history"]) in agent_api.llm.call_args_list[0][0][0].messages[0].content
        assert str(test_variables["mock_history"]) in agent_api.llm.call_args_list[1][0][0].messages[0].content

        # Assert that the chat history was filtered
        MockFilterAgentHistory.assert_called_once_with(test_variables["mock_history"], "agent_api")

        # Assert the final answer
        assert "agent_api" in answer["agents"]
        assert answer["agents"]["agent_api"] == test_variables["mock_answer"]

def test_generate_answer_skip_flow(agent_api, test_variables, config):
    with patch('modules.agent_api.filter_agent_history') as MockFilterAgentHistory:
        MockFilterAgentHistory.return_value = test_variables["mock_history"]

        # Mock already tested methods
        agent_api.get_relevant_endpoints = MagicMock(return_value=test_variables["mock_relevant_endpoints"])
        agent_api.get_endpoint_details = MagicMock(return_value=test_variables["mock_context"])
        agent_api.generate_code = MagicMock(return_value=test_variables["mock_cleaned_code"])
        agent_api.run_code = MagicMock(return_value=test_variables["mock_code_result"])
        
        # Mock LLM response (the entry point provides the answer right away)
        agent_api.llm.return_value = test_variables["mock_answer"]
        
        # Call the method under test
        answer = agent_api.generate_answer(State({"question": test_variables["mock_question"], "history": test_variables["mock_history"]}))

        # Assert that the LLM was called only once
        agent_api.llm.assert_called_once()

        # Assert no other methods were called
        agent_api.get_relevant_endpoints.assert_not_called()
        agent_api.get_endpoint_details.assert_not_called()
        agent_api.generate_code.assert_not_called()
        agent_api.run_code.assert_not_called()

        # Assert the final answer
        assert "agent_api" in answer["agents"]
        assert answer["agents"]["agent_api"] == test_variables["mock_answer"]

def test_generate_answer_error(agent_api, test_variables):
    # Mock to raise an error
    agent_api.get_relevant_endpoints = MagicMock(side_effect=Exception("Mocked exception"))

    answer = agent_api.generate_answer(State({"question": test_variables["mock_question"], "history": test_variables["mock_history"]}))

    assert "agent_api" in answer["agents"]
    assert answer["agents"]["agent_api"] == "I don't know"