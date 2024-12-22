import os
from dotenv import load_dotenv

load_dotenv()

rag_config = {
    "agent_id": "rag",
    "agent_directive": "You are able to answer questions related to Fabian's final project for his master degree in AI.",
    "azure_search_endpoint": os.getenv("AZURE_SEARCH_URI"),
    "azure_search_key": os.getenv("AZURE_SEARCH_KEY"),
    "index_name": os.getenv("RAG_INDEX"),
    "embeddings": os.getenv("EMBEDDINGS_MODEL")
}

sql_config = {
    "agent_id": "sql",
    "agent_directive": "You are able to answer questions related to AdventureWorks database, which contains sample data for e-commerce scenarios, showcasing sales and product management.",
    "connection_string": f"mssql+pyodbc://{os.getenv('SQL_USERNAME')}:{os.getenv('SQL_PASSWORD')}@{os.getenv('SQL_SERVER')}:1433/{os.getenv('SQL_DATABASE')}?driver=ODBC+Driver+18+for+SQL+Server"
}

csv_config = {
    "agent_id": "csv",
    "agent_directive": "You are able to answer questions related to a collection of CSV files, which contains data from DC and Marvel characters.",
    "connection_string": os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
    "container_name": os.getenv("CSV_CONTAINER"),
    "index_file_name": "index.csv"
}