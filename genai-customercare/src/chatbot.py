import google.generativeai as genai
import os
from dotenv import load_dotenv
from google.cloud import bigquery
import pandas as pd
import db_dtypes 

# Load environment variables and set up paths
load_dotenv()
api_key = os.getenv("GENAI_API_KEY")
genai.configure(api_key=api_key)

# Get the current directory where .env is located
current_dir = os.path.dirname(os.path.abspath(__file__))
credentials_file = os.path.join(os.path.dirname(current_dir), 'local-terminus-448520-p6-5eaccf4414ad.json')


def get_table_schema():
    """Get the table schema to know available columns"""
    try:
        client = bigquery.Client(project='local-terminus-448520-p6')
        table_id = 'local-terminus-448520-p6.gemeni_usecases.customer'
        table = client.get_table(table_id)
        
        # Create a more detailed schema string with example usage
        schema_info = """
        Table Columns:
        - int64_field_0 (INTEGER) : Auto-incremented ID
        - customer_id (STRING) : Unique customer identifier (e.g., 'C111565')
        - customer_name (STRING) : Full name of the customer
        - customer_address (STRING) : Complete address
        - gender (STRING) : Customer's gender
        - age (INTEGER) : Customer's age
        - info_updated (TIMESTAMP) : Last update timestamp
        
        Example queries:
        - Find customer by ID: SELECT customer_name, customer_address FROM ... WHERE customer_id = 'C123'
        - Get customer details: SELECT customer_name, customer_address, age FROM ... WHERE customer_id = 'C123'
        """
        return schema_info
    except Exception as e:
        return str(e)

def generate_sql_query(user_question):
    # Extract customer ID using simple pattern matching
    import re
    customer_id_match = re.search(r'C\d{6}', user_question)
    if customer_id_match:
        customer_id = customer_id_match.group(0)
        return f"""
        SELECT customer_name, customer_address 
        FROM `local-terminus-448520-p6.gemeni_usecases.customer` 
        WHERE customer_id = '{customer_id}'
        """
    
    # If no customer ID found, use the general query generation
    schema = get_table_schema()
    prompt = f"""
    Given this user question: "{user_question}"
    Write a SQL query for BigQuery table `local-terminus-448520-p6.gemeni_usecases.customer`.
    
    {schema}
    
    Rules:
    1. Use valid BigQuery SQL syntax
    2. Start with SELECT
    3. Always include customer_name with the requested information
    4. Use customer_address (not address) for location information
    5. Return only the SQL query
    6. Add LIMIT 10 for queries without specific customer_id
    
    Example format:
    SELECT customer_name, customer_address 
    FROM `local-terminus-448520-p6.gemeni_usecases.customer` 
    WHERE customer_id = 'C123';
    """
    
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(prompt)
    query = response.text.strip()
    
    # Basic validation
    if not query.upper().startswith('SELECT'):
        return """
        SELECT customer_name, customer_address 
        FROM `local-terminus-448520-p6.gemeni_usecases.customer` 
        LIMIT 1
        """
    
    return query

def execute_query(query):
    try:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file
        client = bigquery.Client(project='local-terminus-448520-p6')
        
        # Validate query before execution
        try:
            # Dry run to check query syntax
            job_config = bigquery.QueryJobConfig(dry_run=True)
            client.query(query, job_config=job_config)
        except Exception as e:
            return {
                'success': False,
                'error': f'Invalid query syntax: {str(e)}'
            }
            
        # Execute actual query
        df = client.query(query).to_dataframe()
        return {'success': True, 'data': df}
    except Exception as e:
        return {
            'success': False,
            'error': f'Query execution error: {str(e)}'
        }

def generate_response(user_question):
    # First, generate the SQL query
    sql_query = generate_sql_query(user_question)
    
    # Execute the query
    query_result = execute_query(sql_query)
    
    if not query_result['success']:
        return {
            'answer': f"Error: {query_result['error']}",
            'sql_query': sql_query,
            'results': pd.DataFrame()  # Empty DataFrame for error cases
        }
    
    # Generate natural language response
    prompt = f"""
    Based on this query: {sql_query}
    And these results: {query_result['data'].to_string()}
    
    Please provide a natural language answer to the user's question: "{user_question}"
    Make it conversational and easy to understand.
    """
    
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(prompt)
    return {
        'answer': response.text,
        'sql_query': sql_query,
        'results': query_result['data']
    }