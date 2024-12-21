from .models import State
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

class AgentRag:    
    def __init__(self, config):
        self.name = config["agent_name"]
        
        # Embeddings model instantiation
        if config["embeddings"] == "openai":
            self.embeddings = AzureOpenAIEmbeddings(model="ada-002", openai_api_version="2024-06-01")
        elif config["embeddings"] == "google":    
            self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        else:
            self.embeddings = AzureOpenAIEmbeddings(model="ada-002", openai_api_version="2024-06-01")
        
        # Vector store instantiation
        self.vstore = AzureSearch(
            azure_search_endpoint=config["azure_search_endpoint"],
            azure_search_key=config["azure_search_key"],
            index_name=config["index_name"],
            embedding_function=self.embeddings.embed_query
        )

        # LLM instantiation
        self.llm = AzureChatOpenAI(
            deployment_name="gpt-4o",
            api_version="2023-06-01-preview"
        )

        # The system prompt guides the agent on how to respond
        self.system_prompt = (
            "You are an AI assistant for question-answering tasks."
            "Your skills are listed below, these skills dictate what you can answer about."
            "Use only the following pieces of retrieved context and your knowledge about your skills to answer the question." 
            "If you cannot find the answer, say that you don't know."
            "Never make up information that is not in the provided context nor in your list of skills." 
            "Use three sentences maximum and keep the answer concise."
            "\n\n"
            f"Your skills: {config['agent_directive']}"
            "\n\n"
            "Context: {context}"
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
        self.rag_chain = (
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "context": RunnableLambda(lambda inputs: inputs["context"]), "history": RunnableLambda(lambda inputs: inputs["history"]) }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | self.prompt
            | self.llm
            | self.parser
        )
       
    def retrieve_context(self, query):
        print(f"{self.name} says: retrieving relevant information...")      
        docs = self.vstore.similarity_search(query, k=3)
        print(f"{self.name} says: {docs}")
        # Put together the results of the similarity search into one chunk of text
        return "\n\n".join(doc.page_content for doc in docs)

    def generate_answer(self, state: State):
        print(f"{self.name} says: received question '{state['question']}'")

        # Retrieve the most relevant documents from the vector store
        context = self.retrieve_context(state['question'])
        
        print(f"{self.name} says: generating answer...")
        answer = self.rag_chain.invoke({"question": state["question"], "context": context, "history": state["history"]})
        print(f"{self.name} says: {answer}")
        return { "agent_rag": answer }
