# Run the backend

1. Create a virtual environment

```
cd backend

python -m venv venv

cd venv/Scripts

activate

cd ../..
```

2. Install dependencies

```
pip install -r requirements.txt
```

3. Create an account in [Hugging Face](https://huggingface.co/) and generate an [access token](https://huggingface.co/settings/tokens)

4. Create a `.env` file and add a variable called `HUGGINGFACEHUB_API_TOKEN` where the value should be the token created in the previous step.

5. Run the server

```
fastapi dev main.py
```
