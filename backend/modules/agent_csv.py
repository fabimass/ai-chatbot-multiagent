from .models import State
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
        self.name = config["agent_name"]
        self.index_file_name = config["index_file_name"]
        self.container_name = config["container_name"]
        self.connection_string = config["connection_string"]
        print(f"{self.name} says: connecting to Azure Blob Storage...")
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        print(f"{self.name} says: connection estabished.")
        
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

        # A prompt to generate a SQL query from a user question
        self.file_selector_prompt = (
            "You are a file selector."
            "Given an input question and an index, provide a list with the most relevant files."
            "The list must be a comma separated string containing only the file names."
            "Respond only with the generated list, nothing else."
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
            "You are a Python expert specialized in working with CSV files using the pandas library."
            "Given an input question, output a syntactically correct Python code to run."
            "Respond only with the generated code, nothing else."
            "When generating the code:"
            "- Understand the context: analyze the user's question and the CSV data provided to infer the structure and relevant fields." 
            "- Use pandas library to load, manipulate, and analyze the data."
            "- Avoid unnecessary dependencies, use only pandas and Python's standard libraries."
            "- Handle edge cases such as missing values or empty datasets gracefully." 
            "- Ensure the code is executable."
            "- ALWAYS assign the final result to a variable called 'result'"
            "- DO NOT attempt to modify the data in the csv files."
            "\n\n"
            f"CSV files location: Azure storage account. Container name: {self.container_name}. Connection string: {self.connection_string}"
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
            "You are a Python expert with a strong attention to detail."
            "Double check the Python code for common mistakes."
            "Ensure the final result is assigned to a variable called 'result'."
            "Ensure the code is executable."
            "If you see any mistakes, rewrite the code. If there are no mistakes, just reproduce the original code."
            "Respond only with the rewritten code or the original code, nothing else."
        )

        self.code_reviewer_chain = (
            { "code": RunnablePassthrough() }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | RunnableLambda(lambda inputs: self.prompt({"system_prompt": self.code_reviewer_prompt, "human_prompt": inputs["code"]}))
            | self.llm
            | self.parser
        )

        # A prompt to generate an answer to the question given the information pulled from the database
        self.answer_generator_prompt = (
            "You are an AI assistant for question-answering tasks."
            "Your skills are listed below, these skills dictate what you can answer about."
            "Use only the following user question, corresponding Python code, Python result, and your knowledge about your skills to answer the question. " 
            "If you cannot find the answer, say that you don't know."
            "Never make up information that is not in the provided results nor in your list of skills." 
            "Use three sentences maximum and keep the answer concise."
            "\n\n"
            f"Your skills: {config['agent_directive']}"
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
        reviewed_code = self.code_reviewer_chain.invoke(code)
        print(f"{self.name} says: {reviewed_code}")
        
        cleaned_code = re.sub(r"^```python\n", "", reviewed_code)  # Remove start markdown
        cleaned_code = re.sub(r"\n```$", "", cleaned_code)  # Remove end markdown
        return cleaned_code
    
    def run_code(self, code):
        safe_globals = {}
        safe_locals = {}
        print(f"{self.name} says: executing code...")
        try:
            exec(code, safe_globals, safe_locals)
            result = safe_locals['result']
        except Exception as e:
            result = f"ERROR {e}"
        print(f"{self.name} says: {result}")
        return result
    
    def generate_answer(self, state: State):
        print(f"{self.name} says: received question '{state['question']}'")
        
        try:
            # Get index file
            index = self.get_index()

            # Get relevant files
            relevant_files = self.get_relevant_files(state['question'], index, state["history"])
            
            # Get an extract from the relevant files
            context = self.get_files_head(relevant_files)

            # Generate Python code to interact with the files
            code = self.generate_code(state['question'], context, state["history"])

            # Execute the code
            result = self.run_code(code)

            # Finally answer the question
            print(f"{self.name} says: generating answer...")
            answer = self.answer_generator_chain.invoke({"question": state["question"], "code": code, "result": result, "history": state["history"]})
            print(f"{self.name} says: {answer}")
            return { "agent_csv": answer }
        except Exception as e:
            print(f"{self.name} says: ERROR {e}")
            return { "agent_csv": f"I don't know" }