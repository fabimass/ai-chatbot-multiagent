from .models import State
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

class Supervisor:
    
    def __init__(self, agent_list): 

        # List with all the agents to supervise
        self.agents = [{
            "agent_name": agent.name,
            "agent_skills": agent.skills } for agent in agent_list]

        # Instantiate a pre-trained Large Language Model from Azure OpenAI
        self.llm = AzureChatOpenAI(
            deployment_name="gpt-4o",
            api_version="2023-06-01-preview"
        )

        # The system prompt guides the agent on how to respond
        self.system_prompt = (
            f"You are a supervisor tasked with managing a conversation between the following agents: {str(self.agents).replace('{', '{{').replace('}', '}}')}. "
            "Given an input question, think which would be the most capable agents to answer the question. "
            "Then provide a list of those agents. "
            "The list must be a comma separated string containing only the agent names. "
            "Respond only with the generated list, nothing else. "
            "If you have doubts between two agents, then add them both to the list. "
            "NEVER provide an empty list. If you think none of the agents are capable, then add all of them to the list. "
            "\n\n"
            "Chat history: {history}"
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
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "history": RunnableLambda(lambda inputs: inputs["history"]) }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | self.prompt
            | self.llm
            | self.parser
        )

    def get_relevant_agents(self, state: State):
        print("Supervisor says: getting relevant agents...")
        agents = self.chain.invoke({"question": state["question"], "agents": self.agents, "history": state["history"]})
        if agents == "":
            agents_list = []
        else:
            agents_list = agents.replace(" ", "").split(",")
        print(f"Supervisor says: {agents_list}")
        return { "relevant_agents": agents_list }

    def generate_answer(self, state: State):
        if "agents" not in state:
            state["agents"] = {}
        for agent in state["relevant_agents"]:
            if agent not in state["agents"]:
                print(f"Next agent: {agent}")
                return { "next": agent }
        return { "next": "FINISH" }
