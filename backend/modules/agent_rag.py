from .models import State
from .utils import filter_agent_history
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

class AgentRag:    
    def __init__(self, config):
        self.name = f"agent_{config['agent_id']}"
        self.skills = config['agent_directive']
        
        # Vector store instantiation
        self.vstore = self.connect(config)

        # LLM instantiation
        self.llm = AzureChatOpenAI(
            deployment_name="gpt-4o",
            api_version="2023-06-01-preview"
        )

        # The system prompt guides the agent on how to respond
        self.answer_generator_prompt = (
            "You are an AI assistant for question-answering tasks. "
            "Use only the following pieces of retrieved context to answer the question. " 
            "If you cannot find the answer, say that you don't know. "
            "Never make up information that is not in the provided data. " 
            "Use three sentences maximum and keep the answer concise. "
            "\n\n"
            "Context: {context}"
            "\n\n"
            "Chat history: {history}"
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

        # The chain orchestrates the whole flow
        self.answer_generator_chain = (
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "context": RunnableLambda(lambda inputs: inputs["context"]), "history": RunnableLambda(lambda inputs: inputs["history"]) }
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

    def connect(self, config):
        print(f"{self.name} says: connecting to vector store...")
        try:
            # Embeddings model instantiation
            if config["embeddings"] == "openai":
                embeddings = AzureOpenAIEmbeddings(model="ada-002", openai_api_version="2024-06-01")
            elif config["embeddings"] == "google":    
                embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            else:
                embeddings = AzureOpenAIEmbeddings(model="ada-002", openai_api_version="2024-06-01")

            # Connect to the vector store    
            vstore = AzureSearch(
                azure_search_endpoint=config["azure_search_endpoint"],
                azure_search_key=config["azure_search_key"],
                index_name=config["index_name"],
                embedding_function=embeddings.embed_query
            )
            print(f"{self.name} says: connection established.")
            return vstore
        except Exception as e:
            print(f"{self.name} says: ERROR {e}")
            return None

    def check_connection(self):
        print(f"{self.name} says: checking connection to vector store...")
        try:
            self.vstore.similarity_search("test", k=1)
            print(f"{self.name} says: connection up and running.")
            return True
        except:
            print(f"{self.name} says: there is no open connection.")
            return False

    def retrieve_context(self, query):
        print(f"{self.name} says: retrieving relevant information...")      
        docs = self.vstore.similarity_search(query, k=3)
        print(f"{self.name} says: {docs}")
        # Put together the results of the similarity search into one chunk of text
        return "\n\n".join(doc.page_content for doc in docs)

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
                # Retrieve the most relevant documents from the vector store
                context = self.retrieve_context(state['question'])
                
                print(f"{self.name} says: generating answer...")
                answer = self.answer_generator_chain.invoke({"question": state["question"], "context": context, "history": agent_history})
                print(f"{self.name} says: {answer}")
            
            state["agents"][f"{self.name}"] = answer
            return state
        
        except Exception as e:
            print(f"{self.name} says: ERROR {e}")
            state["agents"][f"{self.name}"] = "I don't know"
            return state
