from .models import State
from .utils import filter_agent_history
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from azure.storage.blob import BlobServiceClient
from io import StringIO
import re
import pandas as pd

class AgentCsv:
    
    def __init__(self, config): 
        self.name = f"agent_{config['agent_id']}"
        self.skills = config['agent_directive']
        self.config = config
        self.status = ""
        
        # Blob storage instantiation
        self.blob_service_client = self.connect()
        
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

        # A prompt to select the most relevant files based on a user question and an index
        self.file_selector_prompt = (
            "You are a file selector. "
            "Given an input question and an index, provide a list with the most relevant files. "
            "The list must be a comma separated string containing only the file names. "
            "Respond only with the generated list, nothing else. "
            "\n\n"
            "Index: {index}"
            "\n\n"
            "Chat history: {history}"
        )

        self.file_selector_chain = (
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "index": RunnableLambda(lambda inputs: inputs["index"]), "history": RunnableLambda(lambda inputs: inputs["history"]) }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | RunnableLambda(lambda inputs: self.prompt({"system_prompt": self.file_selector_prompt, "human_prompt": inputs["question"]}))
            | self.llm
            | self.parser
        )

        # A prompt to double check the generated query and adjust if needed
        self.code_generator_prompt = (
            "You are a Python expert specialized in working with CSV files using the pandas library. "
            "Given an input question, output a syntactically correct Python code to run. "
            "Respond only with the generated code, nothing else. "
            "When generating the code: "
            "- Understand the context: analyze the user's question and the CSV data provided to infer the structure and relevant fields. " 
            "- Use pandas library to load, manipulate, and analyze the data. "
            "- Handle edge cases such as missing values or empty datasets gracefully. " 
            "- Ensure the code is executable. "
            "- ALWAYS assign the final result to a variable called 'result'. "
            "- DO NOT attempt to modify the data in the csv files. "
            "\n\n"
            f"CSV files location: Azure storage account. Container name: {self.container_name}. Connection string: {self.connection_string}"
            "\n\n"
            "Use the following function to load csv files: "
            """```python
            def load_csv_file(file_name, blob_container, blob_service_client):
                blob_client = blob_service_client.get_blob_client(container=blob_container, blob=file_name)
                blob_data = blob_client.download_blob().content_as_text()
                csv_data = StringIO(blob_data)
                return pd.read_csv(csv_data)
            ```
            """
            "\n\n"
            "Context: {context}"
            "\n\n"
            "Chat history: {history}"
        )

        self.code_generator_chain = (
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "context": RunnableLambda(lambda inputs: inputs["context"]), "history": RunnableLambda(lambda inputs: inputs["history"]) }
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

    def connect(self):
        self.index_file_name = self.config["index_file_name"]
        self.container_name = self.config["container_name"]
        self.connection_string = self.config["connection_string"]
        print(f"{self.name} says: connecting to Azure Blob Storage...")
        try:
            blob_client = BlobServiceClient.from_connection_string(self.connection_string)
            print(f"{self.name} says: connection established.")
            return blob_client
        except Exception as e:
            print(f"{self.name} says: ERROR {e}")
            self.status = e
            return None
        
    def check_connection(self):
        print(f"{self.name} says: checking connection to storage account...")
        try:
            self.blob_service_client.get_blob_client(container=self.container_name, blob=self.index_file_name)
            print(f"{self.name} says: connection up and running.")
            self.status = "up and running"
            return { "healthy": True, "info": self.status }
        except Exception as e:
            print(f"{self.name} says: ERROR {e}")
            # Try to reconnect
            self.blob_service_client = self.connect()
            return { "healthy": True if self.blob_service_client is not None else False, "info": self.status }

    def get_index(self):
        print(f"{self.name} says: retrieving index file...")
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=self.index_file_name)
        blob_data = blob_client.download_blob().content_as_text()
        csv_data = StringIO(blob_data)
        index = pd.read_csv(csv_data)
        print(f"{self.name} says:\n {index}")
        return index

    def get_relevant_files(self, question, index, history):
        print(f"{self.name} says: getting relevant files...")
        files = self.file_selector_chain.invoke({"question": question, "index": index, "history": history})
        if files == "":
            files_list = []
        else:
            files_list = files.replace(" ", "").split(",")
        print(f"{self.name} says: {files_list}")
        return files_list
    
    def get_files_head(self, files_list):
        print(f"{self.name} says: getting a sample from the files...")
        files_head = {}
        for file in files_list:
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=file)
            blob_data = blob_client.download_blob().content_as_text()
            csv_data = StringIO(blob_data)
            head = pd.read_csv(csv_data, nrows=5)
            print(f"{self.name} says:\n {head}")
            files_head[file] = head.fillna("null").to_dict(orient="records")
        return files_head

    def generate_code(self, question, context, history):
        print(f"{self.name} says: generating code...")
        code = self.code_generator_chain.invoke({"question": question, "context": context, "history": history})
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
                # Get index file
                index = self.get_index()

                # Get relevant files
                relevant_files = self.get_relevant_files(state['question'], index, agent_history)
                
                # Get an extract from the relevant files
                context = self.get_files_head(relevant_files)

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