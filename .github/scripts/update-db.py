import os
from azure.cosmos import CosmosClient, PartitionKey
from langchain_community.vectorstores.azure_cosmos_db_no_sql import AzureCosmosDBNoSqlVectorSearch
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredMarkdownLoader
import nltk

nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')

# Azure Cosmos DB parameters
cosmos_client = CosmosClient(os.getenv("AZURE_COSMOS_DB_URI"), os.getenv("AZURE_COSMOS_DB_KEY"))
database_name = "rag_ai_chatbot_db"
container_name = "knowledge_base"
partition_key = PartitionKey(path="/id")
cosmos_container_properties = {"partition_key": partition_key}
cosmos_database_properties = {"id": database_name}

# Define how the text should be split:
#  - Each chunk should be up to 512 characters long.
#  - There should be an overlap of 64 characters between consecutive chunks. 
#  - This overlap helps maintain context across the chunks.
splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)

data_chunks = []

# Iterate over each file in the knowledge base and split it into chunks
for root, dirs, files in os.walk('knowledge-base'):
    for file in files:
        file_path = os.path.join(root, file)
        data_loader = UnstructuredMarkdownLoader(file_path)

        # Load pdf and split into chunks.
        file_chunks = data_loader.load_and_split(text_splitter=splitter)
        data_chunks.append(file_chunks)

        print(f"{file_path} splitted into {len(file_chunks)} chunks")