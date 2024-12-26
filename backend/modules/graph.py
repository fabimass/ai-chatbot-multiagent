from .models import State
from langchain_core.runnables import RunnableLambda
from langgraph.graph import StateGraph

class Graph():
    def __init__(self, supervisor, summarizer, agent_list): 
        self.builder = StateGraph(State)
        
        # The supervisor is made of 2 connected nodes
        self.builder.add_node("supervisor_agent_filter_node", supervisor.get_relevant_agents)
        self.builder.add_node("supervisor_agent_picker_node", supervisor.generate_answer)
        self.builder.add_edge("supervisor_agent_filter_node", "supervisor_agent_picker_node")
        
        # Add a node for the summarizer
        self.builder.add_node("summarizer_node", summarizer.generate_answer)
        
        # Loop through each agent in the agent list and add a node for each agent.
        for agent in agent_list:
            self.builder.add_node(f"{agent.name}_node", agent.generate_answer)
        
        # Add conditional edges from the supervisor to other nodes.
        # Edges lead to agent-specific nodes or to the summarizer node
        self.builder.add_conditional_edges(
            "supervisor_agent_picker_node",
            RunnableLambda(lambda inputs: inputs["next"]),
            {**{ f"{agent.name}": f"{agent.name}_node" for agent in agent_list }, "FINISH": "summarizer_node"}
        )
        
        # For each agent, add a direct edge back to the supervisor.
        # This allows the graph to loop back after processing an agent's node.
        for agent in agent_list:
            self.builder.add_edge(f"{agent.name}_node", "supervisor_agent_picker_node")
        
        # Set the entry point of the graph to the supervisor node.
        self.builder.set_entry_point("supervisor_agent_filter_node")
        
        # Compile the graph structure into a runnable object.
        self.graph = self.builder.compile()

    def invoke(self, state):
        return self.graph.invoke(state)