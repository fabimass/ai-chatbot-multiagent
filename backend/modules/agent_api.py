from .models import State
from .utils import filter_agent_history
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
import re
import requests
import yaml
import json

class AgentApi:
    
    def __init__(self, config): 
        self.name = f"agent_{config['agent_id']}"
        self.skills = config['agent_directive']
        self.spec_url = config["spec_url"]
        self.endpoint_filter = config["endpoint_filter"]
        self.base_url, self.endpoints, self.spec_data = self.get_spec(config["spec_format"])
        
        # LLM instantiation
        self.llm = AzureChatOpenAI(
            deployment_name="gpt-4o",
            api_version="2023-06-01-preview"
        )

        # The prompt puts together the system prompt with the user question
        self.prompt = lambda inputs: ChatPromptTemplate.from_messages(
            [
                ("system", inputs["system_prompt"]),
                ("human", inputs["human_prompt"]),
            ]
        )

        # The parser just plucks the string content out of the LLM's output message
        self.parser = StrOutputParser()

        # A prompt to select the most relevant endpoints based on a user question
        self.endpoint_selector_prompt = (
            "You are an endpoint selector. "
            "Given an input question and a list of the available endpoints, provide a list with the most relevant endpoints. "
            "The list must be a comma separated string containing only the endpoint paths. "
            "Respond only with the generated list, nothing else. "
            "\n\n"
            "Endpoints: {endpoints}"
            "\n\n"
            "Chat history: {history}"
        )

        self.endpoint_selector_chain = (
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "endpoints": RunnableLambda(lambda inputs: inputs["endpoints"]), "history": RunnableLambda(lambda inputs: inputs["history"]) }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | RunnableLambda(lambda inputs: self.prompt({"system_prompt": self.endpoint_selector_prompt, "human_prompt": inputs["question"]}))
            | self.llm
            | self.parser
        )

        # A prompt to double check the generated query and adjust if needed
        self.code_generator_prompt = (
            "You are a Python expert specialized in working with REST APIs using the requests library. "
            "Given an input question, output a syntactically correct Python code to run. "
            "Respond only with the generated code, nothing else. "
            "When generating the code: "
            "- Understand the context: analyze the user's question and the API details to understand how to make the request. " 
            "- Use requests library to call the API. "
            "- Handle edge cases such as missing values or empty datasets gracefully. " 
            "- Ensure the code is executable. "
            "- ALWAYS assign the final result to a variable called 'result'. "
            "\n\n"
            f"API base url: {self.base_url}"
            "\n\n"
            "Endpoint specification: {context}"
            "\n\n"
            "Token: {token}"
            "\n\n"
            "Chat history: {history}"
        )

        self.code_generator_chain = (
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "context": RunnableLambda(lambda inputs: inputs["context"]), "token": RunnableLambda(lambda inputs: inputs["token"]), "history": RunnableLambda(lambda inputs: inputs["history"]) }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | RunnableLambda(lambda inputs: self.prompt({"system_prompt": self.code_generator_prompt, "human_prompt": inputs["question"]}))
            | self.llm
            | self.parser
        )

        # A prompt to double check the generated code and adjust if needed
        self.code_reviewer_prompt = (
            "You are a Python expert with a strong attention to detail. "
            "Double check the Python code for common mistakes. "
            "Ensure the final result is assigned to a variable called 'result'. "
            "Ensure the code is executable. "
            "If you see any mistakes, rewrite the code. If there are no mistakes, just reproduce the original code. "
            "Respond only with the rewritten code or the original code, nothing else. "
        )

        self.code_reviewer_chain = (
            { "code": RunnablePassthrough() }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | RunnableLambda(lambda inputs: self.prompt({"system_prompt": self.code_reviewer_prompt, "human_prompt": inputs["code"]}))
            | self.llm
            | self.parser
        )

        # A prompt to generate an answer to the question given the information pulled from the csv
        self.answer_generator_prompt = (
            "You are an AI assistant for question-answering tasks. "
            "Use only the following Python code and result to answer the question. " 
            "If you cannot find the answer, say that you don't know. "
            "Never make up information that is not in the provided data. " 
            "Use three sentences maximum and keep the answer concise. "
            "\n\n"
            "Python code: {code}"
            "\n\n"
            "Python result: {result}"
            "\n\n"
            "Chat history: {history}"
        )

        self.answer_generator_chain = (
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "code": RunnableLambda(lambda inputs: inputs["code"]), "result": RunnableLambda(lambda inputs: inputs["result"]), "history": RunnableLambda(lambda inputs: inputs["history"]) }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | RunnableLambda(lambda inputs: self.prompt({"system_prompt": self.answer_generator_prompt, "human_prompt": inputs["question"]}))
            | self.llm
            | self.parser
        )

        self.entry_point_prompt = (
            "You are an AI assistant for question-answering tasks. "
            f"This is what you can do: {self.skills} "
            "\n\n"
            "Given the following user question, analyze if you can answer it based solely on what you know about your skills and the data from previous conversations. "
            "If you have a clear answer, provide it. " 
            "If you are not sure, then answer with 'CONTINUE', nothing else. "
            "If the user asked you to look for more information, then answer with 'CONTINUE', nothing else. "
            "Never make up information that is not in the provided data. " 
            "\n\n"
            "Chat history: {history}"
        )

        self.entry_point_chain = (
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "history": RunnableLambda(lambda inputs: inputs["history"]) }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | RunnableLambda(lambda inputs: self.prompt({"system_prompt": self.entry_point_prompt, "human_prompt": inputs["question"]}))
            | self.llm
            | self.parser
        )

    def get_spec(self, format):
        print(f"{self.name} says: retrieving api specification...")

        try:
            response = requests.get(self.spec_url)
            spec = response.text

            if format == "yaml":
                # YAML specification
                openapi_data = yaml.safe_load(spec)
            else:
                # JSON specification
                openapi_data = json.loads(spec)
            
            endpoints = []
            for path, methods in openapi_data["paths"].items():
                for method, details in methods.items():
                    # Take only the GET endpoints nas specific endpoints if specified
                    if method == "get" and (any(keyword in path for keyword in self.endpoint_filter) or len(self.endpoint_filter)==0):
                        summary = details.get("summary", "No summary")
                        endpoints.append((method.upper(), path, summary))

            servers = openapi_data.get("servers", [])
            base_url = servers[0].get("url", None)

            print(f"{self.name} says:\n {base_url}\n {endpoints[:5]}")
            return base_url, endpoints, openapi_data
       
        except Exception as e:
            print(f"{self.name} says: ERROR {e}")
            return None   

    def get_relevant_endpoints(self, question, history):
        print(f"{self.name} says: getting relevant endpoints...")
        endpoints = self.endpoint_selector_chain.invoke({"question": question, "endpoints": self.endpoints, "history": history})
        if endpoints == "":
            endpoints_list = []
        else:
            endpoints_list = endpoints.replace(" ", "").split(",")
        print(f"{self.name} says: {endpoints_list}")
        return endpoints_list

    def get_endpoint_details(self, endpoints_list):
        print(f"{self.name} says: getting endpoint details...")
        endpoint_details = {}
        for endpoint in endpoints_list:
            details = self.spec_data["paths"].get(endpoint)
            print(f"{self.name} says:\n {details}")
            endpoint_details[endpoint] = details
        return endpoint_details
    
    def get_token(self):
        return ""

    def generate_code(self, question, context, history):
        print(f"{self.name} says: generating code...")
        token = self.get_token()
        code = self.code_generator_chain.invoke({"question": question, "context": context, "token": token, "history": history})
        print(f"{self.name} says: {code}")

        print(f"{self.name} says: reviewing code...")
        reviewed_code = self.code_reviewer_chain.invoke(code.replace("{", "{{").replace("}", "}}"))
        print(f"{self.name} says: {reviewed_code}")
        
        cleaned_code = re.sub(r"^```python\n", "", reviewed_code)  # Remove start markdown
        cleaned_code = re.sub(r"\n```$", "", cleaned_code)  # Remove end markdown
        return cleaned_code
    
    def run_code(self, code):
        safe_locals = {}
        print(f"{self.name} says: executing code...")
        exec(code, globals(), safe_locals)
        result = safe_locals['result']
        print(f"{self.name} says: {result}")
        return result
    
    def generate_answer(self, state: State):
        print(f"{self.name} says: received question '{state['question']}'")
        
        if "agents" not in state:
            state["agents"] = {}

        try:
            # Filter agent history
            agent_history = filter_agent_history(state["history"], self.name)

            # Check if it can answer the question right away or if it needs to continue
            answer = self.entry_point_chain.invoke({"question": state["question"], "history": agent_history})
            print(f"{self.name} says: {answer}")
            if answer == 'CONTINUE':
                # Get relevant endpoints
                relevant_endpoints = self.get_relevant_endpoints(state['question'], agent_history)

                # Get relevant endpoints details
                context = self.get_endpoint_details(relevant_endpoints)

                # Generate Python code to interact with the files
                code = self.generate_code(state['question'], context, agent_history)

                # Execute the code
                result = self.run_code(code)

                # Finally answer the question
                print(f"{self.name} says: generating answer...")
                answer = self.answer_generator_chain.invoke({"question": state["question"], "code": code.replace("{", "{{").replace("}", "}}"), "result": result, "history": agent_history})
                print(f"{self.name} says: {answer}")
            
            state["agents"][f"{self.name}"] = answer
            return state
        
        except Exception as e:
            print(f"{self.name} says: ERROR {e}")
            state["agents"][f"{self.name}"] = "I don't know"
            return state