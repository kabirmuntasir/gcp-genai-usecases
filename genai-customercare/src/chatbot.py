import google.generativeai as genai
import os
from dotenv import load_dotenv
from google.cloud import bigquery
from google.api_core import exceptions as google_exceptions
import pandas as pd
import time
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables and set up paths
load_dotenv()
api_key = os.getenv("GENAI_API_KEY")
genai.configure(api_key=api_key)

# Get the current directory where .env is located
current_dir = os.path.dirname(os.path.abspath(__file__))
credentials_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Log the path to the service account key file
logging.info(f"Using service account key file: {credentials_file}")

def get_table_schema():
    """Get the table schema to know available columns"""
    try:
        return """
        Available Tables and Their Columns:

        1. Customer Table (`local-terminus-448520-p6.gemeni_usecases.customer`):
        - int64_field_0 (INTEGER) : Auto-incremented ID
        - customer_id (STRING) : Unique customer identifier (Primary Key)
        - customer_name (STRING) : Full name of the customer
        - customer_address (STRING) : Complete address
        - gender (STRING) : Customer's gender
        - age (INTEGER) : Customer's age
        - info_updated (TIMESTAMP) : Last update timestamp

        2. Sales Table (`local-terminus-448520-p6.gemeni_usecases.sales`):
        - invoice_no (STRING) : Unique invoice identifier
        - customer_id (STRING) : Customer reference (Foreign Key)
        - gender (STRING) : Customer gender
        - age (INTEGER) : Customer age
        - category (STRING) : Product category
        - quantity (INTEGER) : Number of items
        - price (FLOAT) : Purchase amount
        - payment_method (STRING) : Payment method used
        - invoice_date (TIMESTAMP) : Transaction date

        Relationships:
        - Join tables using customer_id as the key
        
        Common Query Patterns:
        1. For address lookup:
           SELECT customer_name, customer_address 
           FROM `local-terminus-448520-p6.gemeni_usecases.customer` 
           WHERE customer_id = 'C123'

        2. For purchase history:
           SELECT s.invoice_date, s.category, s.quantity, s.price
           FROM `local-terminus-448520-p6.gemeni_usecases.sales` s
           WHERE s.customer_id = 'C123'
           ORDER BY s.invoice_date DESC

        3. For total spending:
           SELECT SUM(price) as total_spent
           FROM `local-terminus-448520-p6.gemeni_usecases.sales`
           WHERE customer_id = 'C123'
           AND invoice_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 YEAR)
        """
    except Exception as e:
        logging.error(f"Error getting table schema: {str(e)}")
        return str(e)

@retry(
    retry=retry_if_exception_type(google_exceptions.ResourceExhausted),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3)
)
def generate_sql_query(user_question):
    """Generate SQL query with retry logic"""
    try:
        logging.info(f"Generating SQL query for user question: {user_question}")
        
        # First extract customer ID
        import re
        customer_id_match = re.search(r'C\d{6}', user_question)
        if not customer_id_match:
            logging.warning("Customer ID not found in user question.")
            return None
        customer_id = customer_id_match.group(0)
        
        # For address update queries
        if 'update' in user_question.lower() and 'address' in user_question.lower():
            # Extract address using regex
            address_pattern = r'to\s+([\d\w\s,\.]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|boulevard|blvd|way|parkway|pkwy|circle|cir)[,\s]+[\w\s]+,\s*[A-Z]{2}\s+\d{5})'
            address_match = re.search(address_pattern, user_question.lower(), re.IGNORECASE)
            
            if address_match:
                new_address = address_match.group(1).strip()
                query = f"""
                UPDATE `local-terminus-448520-p6.gemeni_usecases.customer`
                SET 
                    customer_address = '{new_address}',
                    info_updated = CAST(CURRENT_TIMESTAMP() AS DATE)
                WHERE customer_id = '{customer_id}'
                """
                logging.info(f"Generated SQL query: {query}")
                return query
        
        # For address lookup queries
        elif 'address' in user_question.lower():
            query = f"""
            SELECT customer_name, customer_address 
            FROM `local-terminus-448520-p6.gemeni_usecases.customer` 
            WHERE customer_id = '{customer_id}'
            """
            logging.info(f"Generated SQL query: {query}")
            return query
            
        # For other queries, use LLM
        prompt = f"""
        You are a SQL expert. Generate a BigQuery SQL query for this request: "{user_question}"
        
        Rules:
        1. Return ONLY the SQL query, no explanations
        2. Use fully qualified table name: `local-terminus-448520-p6.gemeni_usecases.customer`
        3. Always include WHERE customer_id = '{customer_id}'
        4. Include only necessary columns
        5. Use proper JOIN syntax if needed
        6. For updates, include info_updated = CURRENT_TIMESTAMP()
        
        Table Schema:
        {get_table_schema()}
        
        Examples:
        1. For address lookup:
           SELECT customer_name, customer_address 
           FROM `local-terminus-448520-p6.gemeni_usecases.customer` 
           WHERE customer_id = 'C123'

        2. For purchase history:
           SELECT s.invoice_date, s.category, s.quantity, s.price
           FROM `local-terminus-448520-p6.gemeni_usecases.sales` s
           WHERE s.customer_id = 'C123'
           ORDER BY s.invoice_date DESC

        3. For total spending:
           SELECT SUM(price) as total_spent
           FROM `local-terminus-448520-p6.gemeni_usecases.sales`
           WHERE customer_id = 'C123'
           AND invoice_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 YEAR)
        """
        
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(prompt)
        query = response.text.strip()
        
        # Log the response from the LLM
        logging.info(f"LLM response: {response.text}")
        
        # Strip backticks and the `sql` keyword
        query = query.replace('```sql', '').replace('```', '').strip()
        
        # Basic validation
        if not query.upper().startswith(('SELECT', 'UPDATE', 'INSERT', 'DELETE')):
            logging.warning("Generated query is not a valid SQL statement.")
            return None
        
        logging.info(f"Generated SQL query: {query}")
        return query.strip()
    except google_exceptions.ResourceExhausted as e:
        logging.error(f"Resource exhausted error: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error generating query: {str(e)}")
        return None

def check_query_type(query):
    """Determine if query is read-only or modification"""
    if not query:
        return 'INVALID'
    query_type = query.strip().upper().split()[0]
    if query_type == 'SELECT':  # Make this an exact match
        return 'READ'
    elif query_type in ['UPDATE', 'INSERT', 'DELETE']:
        return 'WRITE'
    return 'INVALID'

def check_permissions(client, table_id, operation_type):
    """Check if service account has required permissions"""
    try:
        if operation_type == 'READ':
            test_query = f"""
            SELECT 1 
            FROM `{table_id}` 
            LIMIT 1
            """
        elif operation_type == 'WRITE':
            test_query = f"""
            BEGIN TRANSACTION;
            UPDATE `{table_id}`
            SET info_updated = info_updated
            WHERE FALSE;
            ROLLBACK;
            """
        client.query(test_query).result()
        return True, None
    except Exception as e:
        logging.error(f"Permission check error: {str(e)}")
        return False, str(e)

def execute_query(query, require_confirmation=False):
    """Execute query with permission checks"""
    try:
        logging.info(f"Executing query: {query}")
        
        if not query:
            logging.warning("No valid query generated.")
            return {
                'success': False,
                'error': 'No valid query generated',
                'requires_confirmation': False
            }
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file
        client = bigquery.Client(project='local-terminus-448520-p6')
        table_id = 'local-terminus-448520-p6.gemeni_usecases.customer'
        
        # Check query type and permissions
        operation_type = check_query_type(query)
        if operation_type == 'WRITE':
            if require_confirmation:
                logging.info("Query requires confirmation.")
                return {
                    'success': False,
                    'error': 'This operation requires confirmation',
                    'requires_confirmation': True,
                    'pending_query': query
                }
            
            has_permission, error = check_permissions(client, table_id, 'WRITE')
            if not has_permission:
                logging.error(f"Permission denied: {error}")
                return {
                    'success': False,
                    'error': f'Permission denied: {error}',
                    'requires_confirmation': False
                }
        
        # Execute the query
        job = client.query(query)
        results = job.result()
        
        # Convert results to dataframe
        if operation_type == 'READ':
            df = results.to_dataframe()
        else:
            df = pd.DataFrame([{'status': 'Update successful'}])
        
        logging.info("Query executed successfully.")
        return {
            'success': True,
            'data': df,
            'requires_confirmation': False
        }
    except google_exceptions.ResourceExhausted as e:
        logging.error(f"Resource exhausted error: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Query execution error: {str(e)}")
        return {
            'success': False,
            'error': f'Query execution error: {str(e)}',
            'requires_confirmation': False
        }

@retry(
    retry=retry_if_exception_type(google_exceptions.ResourceExhausted),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3)
)
def generate_content_with_retry(model, prompt):
    """Generate content with retry logic for rate limits"""
    try:
        logging.info(f"Generating content with prompt: {prompt}")
        return model.generate_content(prompt)
    except google_exceptions.ResourceExhausted as e:
        logging.error(f"Resource exhausted error: {str(e)}")
        raise
    except Exception as e:
        if "Resource has been exhausted" in str(e):
            time.sleep(2)
            raise
        raise

def generate_response(user_question, confirmed=False):
    """Generate response with retry logic"""
    try:
        logging.info(f"Generating response for user question: {user_question}")
        
        # Generate SQL query
        sql_query = generate_sql_query(user_question)
        
        if not sql_query:
            logging.warning("Failed to generate a valid SQL query.")
            return {
                'answer': "Sorry, I couldn't generate a valid SQL query.",
                'sql_query': None,
                'results': pd.DataFrame(),
                'requires_confirmation': False
            }
        
        # Execute query with confirmation check
        query_result = execute_query(sql_query, require_confirmation=not confirmed)
        
        if query_result.get('requires_confirmation'):
            logging.info("Operation requires confirmation.")
            return {
                'answer': '⚠️ This operation requires confirmation. Please confirm to proceed.',
                'sql_query': sql_query,
                'results': pd.DataFrame(),
                'requires_confirmation': True,
                'pending_query': query_result.get('pending_query')
            }
        
        if not query_result['success']:
            logging.error(f"Query execution failed: {query_result['error']}")
            return {
                'answer': f"Error: {query_result['error']}",
                'sql_query': sql_query,
                'results': pd.DataFrame(),
                'requires_confirmation': False
            }
        
        # Generate natural language response
        prompt = f"""
        Based on this query: {sql_query}
        And these results: {query_result['data'].to_string()}
        
        Please provide a natural language answer to: "{user_question}"
        Make it conversational and easy to understand.
        """
        
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = generate_content_with_retry(model, prompt)
        
        logging.info("Response generated successfully.")
        return {
            'answer': response.text,
            'sql_query': sql_query,
            'results': query_result['data'],
            'requires_confirmation': False
        }
        
    except google_exceptions.ResourceExhausted as e:
        logging.error(f"Resource exhausted error: {str(e)}")
        return {
            'answer': "Sorry, the system is currently experiencing high load. Please try again later.",
            'sql_query': None,
            'results': pd.DataFrame(),
            'requires_confirmation': False
        }
    except Exception as e:
        logging.error(f"Error generating response: {str(e)}")
        return {
            'answer': f"Sorry, I encountered an error: {str(e)}. Please try again in a moment.",
            'sql_query': sql_query if 'sql_query' in locals() else None,
            'results': pd.DataFrame(),
            'requires_confirmation': False
        }

def validate_and_update_data(pending_operation, confirmed=False):
    """Validate and update data based on pending operation"""
    try:
        logging.info(f"Validating and updating data for operation: {pending_operation}")
        
        if not confirmed:
            logging.info("Operation not confirmed.")
            return {
                'success': False,
                'error': 'Operation not confirmed',
                'requires_confirmation': True
            }
        
        # Generate SQL query for the pending operation
        sql_query = generate_sql_query(pending_operation)
        
        if not sql_query:
            logging.warning("Failed to generate a valid SQL query for the pending operation.")
            return {
                'success': False,
                'error': "Sorry, I couldn't generate a valid SQL query.",
                'requires_confirmation': False
            }
        
        # Execute the update query
        query_result = execute_query(sql_query, require_confirmation=False)
        
        if not query_result['success']:
            logging.error(f"Query execution failed: {query_result['error']}")
            return {
                'success': False,
                'error': f"Error: {query_result['error']}",
                'requires_confirmation': False
            }
        
        logging.info("Data updated successfully.")
        return {
            'success': True,
            'answer': "Data updated successfully.",
            'requires_confirmation': False
        }
        
    except google_exceptions.ResourceExhausted as e:
        logging.error(f"Resource exhausted error: {str(e)}")
        return {
            'success': False,
            'error': "Sorry, the system is currently experiencing high load. Please try again later.",
            'requires_confirmation': False
        }
    except Exception as e:
        logging.error(f"Error validating and updating data: {str(e)}")
        return {
            'success': False,
            'error': f"Error validating and updating data: {str(e)}",
            'requires_confirmation': False
        }