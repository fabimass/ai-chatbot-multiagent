import os
from azure.cosmos import CosmosClient, PartitionKey
from langchain_community.vectorstores.azure_cosmos_db_no_sql import AzureCosmosDBNoSqlVectorSearch
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredMarkdownLoader, PyPDFLoader
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
indexing_policy = {
    "indexingMode": "consistent",
    "includedPaths": [{"path": "/*"}],
    "excludedPaths": [{"path": '/"_etag"/?'}],
    "vectorIndexes": [{"path": "/embedding", "type": "quantizedFlat"}],
}
vector_embedding_policy = {
    "vectorEmbeddings": [
        {
            "path": "/embedding",
            "dataType": "float32",
            "distanceFunction": "cosine",
            "dimensions": 768,
        }
    ]
}

# Embedding model
google_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Connect with database
cosmos_db = AzureCosmosDBNoSqlVectorSearch(
    embedding=google_embeddings,
    cosmos_client=cosmos_client,
    database_name=database_name,
    container_name=container_name,
    vector_embedding_policy=vector_embedding_policy,
    indexing_policy=indexing_policy,
    cosmos_container_properties=cosmos_container_properties,
    cosmos_database_properties=cosmos_database_properties,
    create_container=True
)

# Clean database
cosmos_db.delete([])

# Define how the text should be split:
#  - Each chunk should be up to 512 characters long.
#  - There should be an overlap of 64 characters between consecutive chunks. 
#  - This overlap helps maintain context across the chunks.
splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)

documents = []

# Iterate over each file in the knowledge base and split it into chunks
for root, dirs, files in os.walk('knowledge-base'):
    for file in files:
        file_path = os.path.join(root, file)

        # Construct the data loader according to the file extension
        if file.endswith('.pdf'):
            data_loader = PyPDFLoader(file_path)
        elif file.endswith('.md'):
            data_loader = UnstructuredMarkdownLoader(file_path)
        
        try:
            # Load pdf and split into chunks.
            file_chunks = data_loader.load_and_split(text_splitter=splitter)
            documents.append(file_chunks)

            print(f"{file_path} splitted into {len(file_chunks)} chunks")

        except:
            print(f"Error splitting {file_path}")

# Insert data
for doc in documents:
    # Check that the document is not empty
    if len(doc) > 0 :
        inserted_ids = cosmos_db.add_documents(doc)
        print(f"Inserted {len(inserted_ids)} documents.")