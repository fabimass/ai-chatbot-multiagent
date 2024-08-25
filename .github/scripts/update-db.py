import os
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredMarkdownLoader, PyPDFLoader
import nltk

nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')

# Embedding model
openai_embeddings = AzureOpenAIEmbeddings(model="ada-002", openai_api_version="2024-06-01")

# Connect with database
azure_search = AzureSearch(
    azure_search_endpoint=os.getenv("AZURE_SEARCH_URI"),
    azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
    index_name="main",
    embedding_function=openai_embeddings.embed_query
)

print("Cleaning up database...")

# Clean database
azure_search.delete()

print("Database clean and ready to be updated!")

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

            # Push to the database
            if len(file_chunks) > 0 :
                inserted_ids = azure_search.add_documents(file_chunks)
                print(f"Inserted {len(inserted_ids)} documents")

        except:
            print(f"Error splitting {file_path}")
