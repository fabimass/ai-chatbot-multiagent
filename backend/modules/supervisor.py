from backend.modules.models import State
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

class Supervisor:
    
    def __init__(self, agent_list): 

        # List with all the agents to supervise
        self.agents = agent_list

        # Instantiate a pre-trained Large Language Model from Azure OpenAI
        self.llm = AzureChatOpenAI(
            deployment_name="gpt-4o",
            api_version="2023-06-01-preview"
        )

        # The system prompt guides the agent on how to respond
        self.system_prompt = (
            f"You are a supervisor tasked with managing a conversation between the following workers: {self.agents}."
            "Given the following user question, all the workers will provide a response."
            "Your task is to analyze each of the responses and provide the best possible response to the user."
            "Do not make up new information that is not explicitly in the workers response."
            "\n\n"
            "Workers response: {agents_output}"
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
        self.rag_chain = (
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "agents_output": RunnableLambda(lambda inputs: inputs["agents_output"]) }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | self.prompt
            | self.llm
            | self.parser
        )
       
    def pick_next_agent(self, state: State):
        for agent in self.agents:
            if agent not in state:
                print(f"Next agent: {agent}")
                return { "next": agent }
        return { "next": "FINISH" }

    def summarize(self, state: State):
        print("Summarizing...")
        agents_output = {key: state[key] for key in self.agents if key in state}
        answer = self.rag_chain.invoke({ "question": state["question"], "agents_output": agents_output })
        return { "answer": answer }
