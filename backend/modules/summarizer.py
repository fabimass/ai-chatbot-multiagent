from .models import State
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

class Summarizer:
    
    def __init__(self): 

        # Instantiate a pre-trained Large Language Model from Azure OpenAI
        self.llm = AzureChatOpenAI(
            deployment_name="gpt-4o",
            api_version="2023-06-01-preview"
        )

        # The system prompt guides the agent on how to respond
        self.system_prompt = (
            "You are an AI assistant tasked with summarizing a list of responses. "
            "If you see NO RESPONSES, respond with: 'This question falls outside of my area of knowledge'. "
            "Else, given the following user question, your task is to analyze each of the provided responses and provide the best possible response to the user. "
            "DO NOT provide any information that is not in the responses. "
            "\n\n"
            "Responses: {agents_output}"
        )

        # The prompt puts together the system prompt with the user question
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "{question}"),
            ]
        )

        # The parser just plucks the string content out of the LLM's output message
        self.parser = StrOutputParser()

        # The chain orchestrates the whole flow
        self.chain = (
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "agents_output": RunnableLambda(lambda inputs: inputs["agents_output"]) }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | self.prompt
            | self.llm
            | self.parser
        )

    def generate_answer(self, state: State):
        print("Summarizing...")
        if "agents" not in state:    
            answer = self.chain.invoke({ "question": state["question"], "agents_output": "NO RESPONSES" })
            return { "answer": answer, "agents": {} }
        else:
            answer = self.chain.invoke({ "question": state["question"], "agents_output": state["agents"] })
            return { "answer": answer }
