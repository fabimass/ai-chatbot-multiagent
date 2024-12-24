from .models import State
from .utils import filter_agent_history
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_community.utilities import SQLDatabase
import re

class AgentSql:
    def __init__(self, config): 
        self.name = f"agent_{config['agent_id']}"
        
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
            "You are a SQL expert with a strong attention to detail. "
            "Given an input question, output a syntactically correct SQL query to run. "
            "Respond only with the generated query, nothing else. "
            "When generating the query: "
            "- Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results. " 
            "- You can order the results by a relevant column to return the most interesting examples in the database. "
            "- Never query for all the columns from a specific table, only ask for the relevant columns given the question. " 
            "- DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database. "
            "- Pay attention to use only the column names that you can see in the schema description. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table. "
            "\n\n"
            "Schema description (TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE): {schema}"
            "\n\n"
            "Chat history: {history}"
        )

        self.query_generator_chain = (
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "schema": RunnableLambda(lambda inputs: inputs["schema"]), "history": RunnableLambda(lambda inputs: inputs["history"]) }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | RunnableLambda(lambda inputs: self.prompt({"system_prompt": self.query_generator_prompt, "human_prompt": inputs["question"]}))
            | self.llm
            | self.parser
        )

        # A prompt to double check the generated query and adjust if needed
        self.query_reviewer_prompt = (
            "You are a SQL expert with a strong attention to detail. "
            "Double check the SQL query for common mistakes, including: "
            "- Using NOT IN with NULL values. "
            "- Using UNION when UNION ALL should have been used. "
            "- Using BETWEEN for exclusive ranges. "
            "- Data type mismatch in predicates. "
            "- Properly quoting identifiers (e.g., using square brackets for column/table names). "
            "- Using the correct number of arguments for functions. "
            "- Casting to the correct data type. "
            "- Using the proper columns for joins. "
            "- Ensuring TOP is used for limiting rows instead of LIMIT. "
            "If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query. "
            "Respond only with the rewritten query or the original query, nothing else. "
        )

        self.query_reviewer_chain = (
            { "query": RunnablePassthrough() }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | RunnableLambda(lambda inputs: self.prompt({"system_prompt": self.query_reviewer_prompt, "human_prompt": inputs["query"]}))
            | self.llm
            | self.parser
        )

        # A prompt to generate an answer to the question given the information pulled from the database
        self.answer_generator_prompt = (
            "You are an AI assistant for question-answering tasks. "
            "Use only the following SQL query and result to answer the question. " 
            "If you cannot find the answer, say that you don't know. "
            "Never make up information that is not in the provided data. " 
            "Use three sentences maximum and keep the answer concise. "
            "\n\n"
            "SQL query: {query}"
            "\n\n"
            "SQL result: {result}"
            "\n\n"
            "Chat history: {history}"
        )

        self.answer_generator_chain = (
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "query": RunnableLambda(lambda inputs: inputs["query"]), "result": RunnableLambda(lambda inputs: inputs["result"]), "history": RunnableLambda(lambda inputs: inputs["history"]) }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | RunnableLambda(lambda inputs: self.prompt({"system_prompt": self.answer_generator_prompt, "human_prompt": inputs["question"]}))
            | self.llm
            | self.parser
        )

        self.entry_point_prompt = (
            "You are an AI assistant for question-answering tasks. "
            f"This is what you can do: {config['agent_directive']} "
            "\n\n"
            "Given the following user question, analyze if you can answer it based solely on what you know about your skills and the data from previous conversations. "
            "If you have a clear answer, provide it. " 
            "If you are not sure, then answer with 'CONTINUE', nothing else. "
            "If the user asked you to look for more information, then answer with 'CONTINUE', nothing else. "
            "Never make up information that is not in the provided data. " 
            "\n\n"
            "Chat history: {history}"
        )

        self.entry_point_chain = (
            { "question": RunnableLambda(lambda inputs: inputs["question"]), "history": RunnableLambda(lambda inputs: inputs["history"]) }
            #| RunnableLambda(lambda inputs: (print(f"Logging Inputs: {inputs}") or inputs))
            | RunnableLambda(lambda inputs: self.prompt({"system_prompt": self.entry_point_prompt, "human_prompt": inputs["question"]}))
            | self.llm
            | self.parser
        )

    def connect(self):
        print(f"{self.name} says: connecting to database...")
        try:
            db = SQLDatabase.from_uri(self.db_uri)
            print(f"{self.name} says: connection established.")
            return db
        except Exception as e:
            print(f"{self.name} says: ERROR {e}")
            return None

    def check_connection(self):
        print(f"{self.name} says: checking connection to database...")
        try:
            self.db.run("""SELECT 1""")
            print(f"{self.name} says: connection up and running.")
            return True
        except:
            print(f"{self.name} says: there is no open connection.")
            return False

    def get_schema(self):
        print(f"{self.name} says: retrieving database schema...")
        schema = self.db.run("SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS")
        print(f"{self.name} says: {schema}")
        return schema

    def generate_query(self, question, schema, history):
        print(f"{self.name} says: generating query...")
        query = self.query_generator_chain.invoke({"question": question, "schema": schema, "history": history})
        print(f"{self.name} says: {query}")

        print(f"{self.name} says: reviewing query...")
        reviewed_query = self.query_reviewer_chain.invoke(query)
        print(f"{self.name} says: {reviewed_query}")

        cleaned_query = re.sub(r"^```sql\n", "", reviewed_query)  # Remove start markdown
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
        
        if "agents" not in state:
            state["agents"] = {}

        # Reconnect with database if connection was closed
        if(self.check_connection() is False):
            self.db = self.connect()
        
        try:
            # Filter agent history
            agent_history = filter_agent_history(state["history"], self.name)

            # Check if it can answer the question right away or if it needs to continue
            answer = self.entry_point_chain.invoke({"question": state["question"], "history": agent_history})
            print(f"{self.name} says: {answer}")
            if answer == 'CONTINUE':
                # Get tables and columns from the database
                schema = self.get_schema()

                # Construct a SQL query
                query = self.generate_query(state['question'], schema, agent_history)

                # Execute the query
                result = self.run_query(query)

                # Finally answer the question
                print(f"{self.name} says: generating answer...")
                answer = self.answer_generator_chain.invoke({"question": state["question"], "query": query, "result": result, "history": agent_history})
                print(f"{self.name} says: {answer}")
            
            state["agents"][f"{self.name}"] = answer
            return state
        
        except Exception as e:
            print(f"{self.name} says: ERROR {e}")
            state["agents"][f"{self.name}"] = "I don't know"
            return state