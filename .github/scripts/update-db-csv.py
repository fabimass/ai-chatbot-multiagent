import os
import time
from azure.storage.blob import BlobServiceClient

connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = os.getenv("CSV_CONTAINER")
source_folder = "knowledge-base/csv"

# Create BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

# Delete and recreate the container if it exists
if container_client.exists():
    print(f"Container '{container_name}' exists. Deleting it...")
    container_client.delete_container()
    while container_client.exists():
        print("Waiting for the container to be deleted...")
        time.sleep(10)
    print(f"Container '{container_name}' deleted.")
        
print(f"Creating container '{container_name}'...")
container_client.create_container()
print(f"Container '{container_name}' created.")

print(f"Discovering files in {source_folder}...")

# Loop through files in the source folder
for root, dirs, files in os.listdir(source_folder):
    for file in files:
        file_path = os.path.join(root, file)
    
        if file.endswith('.pdf'):
            blob_client = container_client.get_blob_client(file)
            print(f"Uploading {file}...")
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            print(f"{file} uploaded successfully.")
