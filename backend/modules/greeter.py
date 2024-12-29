from .models import State
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

class Greeter:
    
    def __init__(self, agent_list): 

        self.agents = [agent.skills for agent in agent_list]
        
        # Instantiate a pre-trained Large Language Model from Azure OpenAI
        self.llm = AzureChatOpenAI(
            deployment_name="gpt-4o",
            api_version="2023-06-01-preview"
        )

        # The system prompt guides the agent on how to respond
        self.system_prompt = (
            "You are an AI assistant for question-answering tasks. "
            f"This is a list of what you can do: {self.agents}. "
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
            { "question": RunnableLambda(lambda inputs: inputs["question"]) }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | self.prompt
            | self.llm
            | self.parser
        )

    def generate_answer(self):
        print("Greeting the user...")
        answer = self.chain.invoke({ "question": "hi! what can you do?" })
        return { "answer": answer }
