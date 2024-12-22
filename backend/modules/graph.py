from .models import State
from langchain_core.runnables import RunnableLambda
from langgraph.graph import StateGraph

class Graph():
    def __init__(self, supervisor, agent_list): 
        self.builder = StateGraph(State)
        
        # Add a node for the supervisor
        self.builder.add_node("supervisor_node", supervisor.pick_next_agent)
        
        # Add a node for the summarizer
        self.builder.add_node("summarizer_node", supervisor.summarize)
        
        # Loop through each agent in the agent list and add a node for each agent.
        for agent in agent_list:
            self.builder.add_node(f"{agent.name}_node", agent.generate_answer)
        
        # Add conditional edges from the supervisor node to other nodes.
        # Edges lead to agent-specific nodes or to the summarizer node
        self.builder.add_conditional_edges(
            "supervisor_node",
            RunnableLambda(lambda inputs: inputs["next"]),
            {**{ f"{agent.name}": f"{agent.name}_node" for agent in agent_list }, "FINISH": "summarizer_node"}
        )
        
        # For each agent, add a direct edge back to the supervisor node.
        # This allows the graph to loop back after processing an agent's node.
        for agent in agent_list:
            self.builder.add_edge(f"{agent.name}_node", "supervisor_node")
        
        # Set the entry point of the graph to the supervisor node.
        self.builder.set_entry_point("supervisor_node")
        
        # Compile the graph structure into a runnable object.
        self.graph = self.builder.compile()

    def invoke(self, state):
        return self.graph.invoke(state)