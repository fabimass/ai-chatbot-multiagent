# Run the backend

### Create environment file

Create a `.env` file inside the `backend/` folder with the following variables. Complete with the corresponding values.

```
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_API_KEY=<your Azure OpenAI API key>
AZURE_SEARCH_URI=https://your-resource-name.search.windows.net
AZURE_SEARCH_KEY=<your Azure Search key>
AZURE_STORAGE_CONNECTION_STRING=<your Azure Storage Account connection string>
RAG_INDEX=<index name in the vector database>
SQL_SERVER=server-name.database.windows.net
SQL_DATABASE=database-name
SQL_USERNAME=<username for the agent to connect to the database>
SQL_PASSWORD=<password for the agent to connect to the database>
CSV_CONTAINER=<container name in the storage account>
API_SPEC_URL=<URL for the specification file of the API>
API_SPEC_FORMAT=<choose yaml or json>
```

> [!CAUTION]
> This file is included in the `.gitignore` file and should not be commited to the repo as it contains sensitive information.

### Position yourself in the backend folder

```bash
cd backend
```

### Create virtual environment

```bash
python -m venv venv

cd venv/Scripts

activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the development server

```bash
fastapi dev main.py
```

### (Optional) Run tests

```bash
pytest
```
