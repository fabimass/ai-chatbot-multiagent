import os
from azure.data.tables import TableServiceClient
from pydantic import BaseModel

# Define body model for the http requests
class Question(BaseModel):
    question: str
    session_id: str

class Answer(Question):
    answer: str

class Feedback(Answer):
    like: bool

# Set up the connection to Azure Table Storage
def get_table_client(table_name):
    table_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    table_service = TableServiceClient.from_connection_string(conn_str=table_connection_string)
    table_client = table_service.get_table_client(table_name)
    return table_client