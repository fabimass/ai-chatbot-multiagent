import os
import requests
from langchain_openai import AzureOpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredMarkdownLoader, PyPDFLoader
import nltk
import time

nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')

index_name = os.getenv("DB_INDEX")

print("Cleaning up database...")

def delete_index(azure_search_endpoint, azure_search_key, index_name):
    # Set up the API URL and headers
    url = f"{azure_search_endpoint}/indexes('{index_name}')?api-version=2023-11-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": f"{azure_search_key}"
    }

    # Send the request to delete all documents
    response = requests.delete(url, headers=headers)

    # Check the response
    if response.status_code == 204:
        print("All documents deleted successfully.")
    else:
        print(f"Failed to delete documents. Status code: {response.status_code}, Response: {response.text}")


def split_into_batches(lst, batch_size):
    for i in range(0, len(lst), batch_size):
        yield lst[i:i + batch_size]


# Clean database
delete_index(
    azure_search_endpoint=os.getenv("AZURE_SEARCH_URI"),
    azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
    index_name=index_name
)

# Embeddings model
if os.getenv("EMBEDDINGS_MODEL") == "openai":
    embeddings = AzureOpenAIEmbeddings(model="ada-002", openai_api_version="2024-06-01")
elif os.getenv("EMBEDDINGS_MODEL") == "google":    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
else:
    embeddings = AzureOpenAIEmbeddings(model="ada-002", openai_api_version="2024-06-01")

# Connect with database
azure_search = AzureSearch(
    azure_search_endpoint=os.getenv("AZURE_SEARCH_URI"),
    azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
    index_name=index_name,
    embedding_function=embeddings.embed_query
)

# Define how the text should be split:
#  - Each chunk should be up to 512 characters long.
#  - There should be an overlap of 64 characters between consecutive chunks. 
#  - This overlap helps maintain context across the chunks.
splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)

documents = []

print("Discovering files in the knowledge base...")

# Iterate over each file in the knowledge base, split it into chunks and push it to the database
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
            print(f"{file_path} splitted into {len(file_chunks)} chunks")
        
        except Exception as e:
            raise ValueError(f"Error splitting {file_path}: {e}")

        try:
            # Push to the database
            if len(file_chunks) > 0 :
                # Split file_chunks into batches and upload each batch
                #for batch in split_into_batches(file_chunks, batch_size=5):
                inserted_ids = azure_search.add_documents(file_chunks)
                    #time.sleep(5)

                print(f"Inserted {len(inserted_ids)} documents")

        except Exception as e:
            raise ValueError(f"Error pushing {file_path} chunks to the database: {e}")
