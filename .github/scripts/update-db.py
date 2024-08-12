import os
from azure.cosmos import CosmosClient, PartitionKey
from langchain_community.vectorstores.azure_cosmos_db_no_sql import AzureCosmosDBNoSqlVectorSearch
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredMarkdownLoader

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

for root, dirs, files in os.walk('knowledge-base'):
    for file in files:
        # Get the full file path
        file_path = os.path.join(root, file)
        print(f"Found file: {file_path}")

#md_loader = UnstructuredMarkdownLoader("example_data/example_markdown.md")

# Load pdf and split into chunks.
#md_chunks = md_loader.load_and_split(text_splitter=splitter)

# Get the number of chunks
#print(f"Number of chunks: {len(md_chunks)}")

# Print the first 5 chunks
#for chunk in md_chunks[:5]:
#    print(chunk)