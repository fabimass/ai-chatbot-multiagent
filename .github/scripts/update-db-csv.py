import os
import time
import csv
from azure.storage.blob import BlobServiceClient
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
import pandas as pd

connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = os.getenv("CSV_CONTAINER")
source_folder = "knowledge-base/csv"

# Instantiate LLM model
llm = AzureChatOpenAI(
    deployment_name="gpt-4o",
    api_version="2023-06-01-preview"
)

prompt = lambda inputs: ChatPromptTemplate.from_messages(
    [
        ("system", inputs["system_prompt"]),
        ("human", inputs["human_prompt"]),
    ]
)

parser = StrOutputParser()

# A prompt to get a summary from a csv extract
system_prompt = (
    "You are a summarizer for csv files. "
    "Given the file name and an extract of it, provide a short summary. "
    "Respond only with the summary, nothing else. "
    "Do not include the name of the file in the summary. "
    "Do not use quotes. "
)

chain = (
    { "question": RunnableLambda(lambda inputs: inputs["question"]) }
    #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
    | RunnableLambda(lambda inputs: prompt({"system_prompt": system_prompt, "human_prompt": inputs["question"]}))
    | llm
    | parser
)

# Create BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

# Delete and recreate the container if it exists
if container_client.exists():
    print(f"Container '{container_name}' exists. Deleting it...")
    container_client.delete_container()
        
print(f"Creating container '{container_name}'...")
retries = 5
while(retries):
    try:
        container_client.create_container()
        print(f"Container '{container_name}' created.")
        break
    except Exception as e:
        print(f"Container creation failed: {e}")
        print("Retrying...")
        retries -= 1
        time.sleep(60)

print(f"Discovering files in {source_folder}...")

# Index file
index_exists = False
index_file_name = "index.csv"
index_file_path = os.path.join(source_folder, index_file_name)
for root, dirs, files in os.walk(source_folder):
    for file in files:
        if file == index_file_name:
            print("Index file already provided.")
            index_exists = True
            break
    # Create index.csv if it was not provided
    print("Index file not provided. Proceeding to create one...")
    with open(index_file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["FILE_NAME", "SUMMARY"])

# Function to summarize file using LLM model
def get_file_summary(filepath, filename):
    print(f"Getting summary for {filename}")
    df = pd.read_csv(filepath, nrows=5)
    csv_extract = df.to_csv(index=False, header=True, sep=",")
    csv_summary = chain.invoke({"question": f"CSV name: {filename} \n\n CSV extract: {csv_extract}"})
    index_new_row = {"FILE_NAME": filename, "SUMMARY": csv_summary}
    df = pd.DataFrame([index_new_row])
    df.to_csv(index_file_path, mode="a", index=False, header=False)
    print(csv_summary)

# Loop through files in the source folder
for root, dirs, files in os.walk(source_folder):
    for file in files:
        file_path = os.path.join(root, file)
        if file.endswith('.csv') and file != index_file_name:
            if index_exists == False:
                get_file_summary(file_path, file)
            blob_client = container_client.get_blob_client(file)
            print(f"Uploading {file}...")
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            print(f"{file} uploaded successfully.")

# Finally upload index file
print(f"Uploading {index_file_name}...")
blob_client = container_client.get_blob_client(index_file_name)
with open(index_file_path, "rb") as data:
    blob_client.upload_blob(data, overwrite=True)
print(f"{index_file_name} uploaded successfully.")