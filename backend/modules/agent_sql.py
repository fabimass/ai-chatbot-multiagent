from backend.modules.models import State
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_community.utilities import SQLDatabase
import re

class AgentSql:
    def __init__(self, config): 
        self.name = config["agent_name"]
        
        # Database instantiation
        self.db_uri = config["connection_string"]
        self.db = self.connect()
        
        # LLM instantiation
        self.llm = AzureChatOpenAI(
            deployment_name="gpt-4o",
            api_version="2023-06-01-preview"
        )

        # The prompt puts together the system prompt with the user question
        self.prompt = lambda inputs: ChatPromptTemplate.from_messages(
            [
                ("system", inputs["system_prompt"]),
                ("human", inputs["human_prompt"]),
            ]
        )

        # The parser just plucks the string content out of the LLM's output message
        self.parser = StrOutputParser()

        # A prompt to generate a SQL query from a user question
        self.query_generator_prompt = (
            "You are a SQL expert with a strong attention to detail."
            "Given an input question, output a syntactically correct SQL query to run."
            "Respond only with the generated query, nothing else."
            "When generating the query:"
            "- Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results." 
            "- You can order the results by a relevant column to return the most interesting examples in the database."
            "- Never query for all the columns from a specific table, only ask for the relevant columns given the question." 
            "- DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database."
            "- Pay attention to use only the column names that you can see in the schema description. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table."
            "\n\n"
            "Schema description (TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE): {schema}"
        )

        self.query_generator_chain = (
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "schema": RunnableLambda(lambda inputs: inputs["schema"]) }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | RunnableLambda(lambda inputs: self.prompt({"system_prompt": self.query_generator_prompt, "human_prompt": inputs["question"]}))
            | self.llm
            | self.parser
        )

        # A prompt to double check the generated query and adjust if needed
        self.query_corrector_prompt = (
            "You are a SQL expert with a strong attention to detail."
            "Double check the SQL query for common mistakes, including:"
            "- Using NOT IN with NULL values"
            "- Using UNION when UNION ALL should have been used"
            "- Using BETWEEN for exclusive ranges"
            "- Data type mismatch in predicates"
            "- Properly quoting identifiers (e.g., using square brackets for column/table names)"
            "- Using the correct number of arguments for functions"
            "- Casting to the correct data type"
            "- Using the proper columns for joins"
            "- Ensuring TOP is used for limiting rows instead of LIMIT"
            "If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query."
            "Respond only with the rewritten query or the original query, nothing else."
        )

        self.query_corrector_chain = (
            { "query": RunnablePassthrough() }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | RunnableLambda(lambda inputs: self.prompt({"system_prompt": self.query_corrector_prompt, "human_prompt": inputs["query"]}))
            | self.llm
            | self.parser
        )

        # A prompt to generate an answer to the question given the information pulled from the database
        self.answer_generator_prompt = (
            "Given the following user question, corresponding SQL query, and SQL result, answer the user question."
            "\n\n"
            "SQL query: {query}"
            "SQL result: {result}"
        )

        self.answer_generator_chain = (
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "query": RunnableLambda(lambda inputs: inputs["query"]), "result": RunnableLambda(lambda inputs: inputs["result"]) }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | RunnableLambda(lambda inputs: self.prompt({"system_prompt": self.answer_generator_prompt, "human_prompt": inputs["question"]}))
            | self.llm
            | self.parser
        )

    def connect(self):
        print(f"{self.name} says: connecting to database...")
        db = SQLDatabase.from_uri(self.db_uri)
        print(f"{self.name} says: connection established.")
        return db

    def check_connection(self):
        print(f"{self.name} says: checking connection to database...")
        try:
            self.db.run("""SELECT 1""")
            print(f"{self.name} says: connection up and running.")
            return True
        except Exception as e:
            print(f"{self.name} says: there is no open connection.")
            return False

    def get_schema(self):
        print(f"{self.name} says: retrieving database schema...")
        schema = self.db.run("SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS")
        print(f"{self.name} says: {schema}")
        return schema

    def generate_query(self, question, schema):
        print(f"{self.name} says: generating query...")
        query = self.query_generator_chain.invoke({"question": question, "schema": schema})
        print(f"{self.name} says: {query}")

        print(f"{self.name} says: reviewing query...")
        corrected_query = self.query_corrector_chain.invoke(query)
        print(f"{self.name} says: {corrected_query}")

        cleaned_query = re.sub(r"^```sql\n", "", corrected_query)  # Remove start markdown
        cleaned_query = re.sub(r"\n```$", "", cleaned_query)  # Remove end markdown
        cleaned_query = re.sub(r"\n", " ", cleaned_query) # Replace new line with space
        cleaned_query = cleaned_query.strip() # Remove leading and trailing whitespace (just in case)   
        return cleaned_query
    
    def run_query(self, query):
        print(f"{self.name} says: executing query...")
        result = self.db.run(query)
        print(f"{self.name} says: {result}")
        return result
    
    def generate_answer(self, state: State):
        print(f"{self.name} says: received question '{state['question']}'")
        
        # Reconnect with database if connection was closed
        if(self.check_connection() is False):
            self.connect()
        
        try:
            # Get tables and columns from the database
            schema = self.get_schema()
            # Construct a SQL query
            query = self.generate_query(state['question'], schema)
            # Execute the query
            result = self.run_query(query)
            # Finally answer the question
            print(f"{self.name} says: generating answer...")
            answer = self.answer_generator_chain.invoke({"question": state["question"], "query": query, "result": result})
            print(f"{self.name} says: {answer}")
            return { "agent_sql": answer }
        
        except Exception as e:
            print(f"{self.name} says: ERROR {e}")
            return { "agent_sql": f"I don't know" }