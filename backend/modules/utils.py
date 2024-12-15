import os
from azure.data.tables import TableServiceClient

# Set up the connection to Azure Table Storage
def get_table_client(table_name):
    table_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    table_service = TableServiceClient.from_connection_string(conn_str=table_connection_string)
    table_client = table_service.get_table_client(table_name)
    return table_client