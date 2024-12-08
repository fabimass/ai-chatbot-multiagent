import os
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class Retriever():

    def __init__(self):
        # Embeddings model instantiation
        if os.getenv("EMBEDDINGS_MODEL") == "openai":
            self.embeddings = AzureOpenAIEmbeddings(model="ada-002", openai_api_version="2024-06-01")
        elif os.getenv("EMBEDDINGS_MODEL") == "google":    
            self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        else:
            self.embeddings = AzureOpenAIEmbeddings(model="ada-002", openai_api_version="2024-06-01")

        # Vector store instantiation
        self.vstore = AzureSearch(
            azure_search_endpoint=os.getenv("AZURE_SEARCH_URI"),
            azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
            index_name=os.getenv("DB_INDEX"),
            embedding_function=self.embeddings.embed_query
        )

    def invoke(self, query):
        # Run a similarity search on the database for the given query
        docs = self.vstore.similarity_search(query['input'], k=3)
        #print(docs)
        return self.format_docs(docs)
    
    def format_docs(self, docs):
        # Put together the results of the similarity search into one chunk of text
        return "\n\n".join(doc.page_content for doc in docs)