### Document Ingestion Process

The document ingestion process is automatically triggered whenever an update occurs in the `knowledge-base` folder. This process is handled by the `Update Database` pipeline, which performs the following steps:

1. **Document Format**: The pipeline processes only files in PDF or Markdown format. Ensure that all documents in the `knowledge-base` folder meet this requirement.

2. **Document Splitting**: Upon triggering, the pipeline splits the documents into smaller chunks for efficient embedding generation and retrieval.

3. **Embedding Generation**: Each document chunk is transformed into embeddings, which are vector representations that capture the semantic meaning of the text. These embeddings are later used for similarity search and response generation.

4. **Database Purge**: Before the ingestion process begins, the existing data in the database is completely purged. This means that all previous entries are deleted, ensuring that the only documents available in the database are the ones currently present in the `knowledge-base` folder.

5. **Database Update**: Once the database is cleared, the newly generated embeddings from the documents in the `knowledge-base` folder are uploaded to the database.

### Required Secrets and Variables

For the pipeline to work correctly, you must create the following **secrets** in the repository:

- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_SERVICE_NAME`
- `AZURE_RESOURCE_GROUP`
- `AZURE_SEARCH_KEY`
- `AZURE_SEARCH_SERVICE_NAME`
- `AZURE_SEARCH_URI`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_TENANT_ID`
- `GOOGLE_API_KEY`

Additionally, the following **variables** need to be set:

- `RAG_INDEX`
- `EMBEDDINGS_MODEL`

### Important Notes:

- **Trigger**: The ingestion process is triggered automatically whenever a change is detected in the `knowledge-base` folder.
- **Persistence**: Any document not currently in the `knowledge-base` folder will be removed from the database during the purge step.
- **Supported Formats**: Ensure that only PDF and Markdown files are added to the folder, as other formats are not supported by the pipeline.
