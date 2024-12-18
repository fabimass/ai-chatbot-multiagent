import os
from dotenv import load_dotenv

load_dotenv()

rag_config = {
    "agent_name": "RAG Agent",
    "azure_search_endpoint": os.getenv("AZURE_SEARCH_URI"),
    "azure_search_key": os.getenv("AZURE_SEARCH_KEY"),
    "index_name": os.getenv("DB_INDEX"),
    "embeddings": os.getenv("EMBEDDINGS_MODEL")
}

sql_config = {
    "agent_name": "SQL Agent",
    "connection_string": f"mssql+pyodbc://{os.getenv('SQL_USERNAME')}:{os.getenv('SQL_PASSWORD')}@{os.getenv('SQL_SERVER')}:1433/{os.getenv('SQL_DATABASE')}?driver=ODBC+Driver+18+for+SQL+Server"
}