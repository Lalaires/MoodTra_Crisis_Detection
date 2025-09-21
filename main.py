import json
import psycopg2
import psycopg2.extras
import os
import logging
from uuid import uuid4
from datetime import datetime

DB_HOST = "db-ta24-mindpal.cnwcamiuul3a.ap-southeast-4.rds.amazonaws.com"   
DB_NAME = "postgres"
DB_USER = "ta24"
DB_PASSWORD = "cojxe8-zofzox-huzgYk"
DB_PORT = 5432

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_connection():
    """
    Create database connection using environment variables
    """
    try:
        logger.info("Attempting to connect to database...")
        
        # Get database credentials from environment variables
        connection = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
            connect_timeout=10
        )
        
        logger.info("Successfully connected to RDS database")
        return connection
        
    except KeyError as e:
        logger.error(f"Missing required environment variable: {e}")
        raise e
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise e

def execute_query(connection, query, params=None):
    """
    Execute a SQL query with optional parameters
    """
    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query, params)
            
            # Check if it's a SELECT query
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
                return result
            else:
                # For INSERT, UPDATE, DELETE queries
                connection.commit()  # PostgreSQL requires explicit commit
                affected_rows = cursor.rowcount
                return {"affected_rows": affected_rows}
                
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise e

def fetch_latest_child_messages(connection, account_id, limit=10):
    """
    Fetch the latest child messages from the chat_message table for a specific account
    """
    try:
        query = """
        SELECT cm.message_text
        FROM chat_message cm
        JOIN chat_session cs ON cm.session_id = cs.session_id
        WHERE cm.message_role = 'child' AND cs.account_id = %s
        ORDER BY cm.message_ts DESC 
        LIMIT %s
        """
        messages = execute_query(connection, query, (account_id, limit))
        logger.info(f"Fetched {len(messages)} child messages for account {account_id}")
        return messages
    except Exception as e:
        logger.error(f"Error fetching child messages: {e}")
        raise e

def get_or_create_crisis_id(connection, crisis_name):
    """
    Get existing crisis_id or create new crisis entry
    """
    try:
        # First, try to get existing crisis
        select_query = "SELECT crisis_id FROM crisis WHERE crisis_name = %s"
        existing = execute_query(connection, select_query, (crisis_name,))
        
        if existing:
            return existing[0]['crisis_id']
        
        # If not found, create new crisis entry
        insert_query = "INSERT INTO crisis (crisis_name) VALUES (%s)"
        execute_query(connection, insert_query, (crisis_name,))
        
        # Get the newly created crisis_id
        new_crisis = execute_query(connection, select_query, (crisis_name,))
        return new_crisis[0]['crisis_id']
        
    except Exception as e:
        logger.error(f"Error getting/creating crisis_id: {e}")
        raise e

def store_crisis_alert(connection, account_id, crisis_id, severity, note=None):
    """
    Store crisis alert information in the crisis_alert table
    """
    try:
        crisis_alert_id = str(uuid4())
        current_time = datetime.now()
        
        query = """
        INSERT INTO crisis_alert 
        (crisis_alert_id, account_id, crisis_id, crisis_alert_severity, 
         crisis_alert_status, crisis_alert_note, crisis_alert_ts)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            crisis_alert_id,
            account_id,
            crisis_id,
            severity,
            'pending',  # Default status
            note,  # Can be None/NULL
            current_time
        )
        
        result = execute_query(connection, query, params)
        logger.info(f"Stored crisis alert with ID: {crisis_alert_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error storing crisis alert: {e}")
        raise e

def test_database_operations(connection):
    """
    Test database connection and basic operations with mock data
    """
    try:
        logger.info("Starting database operations test")
        
        # Test 1: Fetch latest 10 child messages for specific account
        logger.info("Test 1: Fetching child messages")
        test_account_id = "00000000-0000-0000-0000-00000000C0DE"
        messages = fetch_latest_child_messages(connection, test_account_id, 10)
        logger.info(f"Found {len(messages)} child messages")
        
        # Test 2: Insert mock crisis data
        logger.info("Test 2: Testing crisis table operations")
        mock_crisis_name = "suicidal"
        crisis_id = get_or_create_crisis_id(connection, mock_crisis_name)
        logger.info(f"Got/created crisis_id: {crisis_id} for '{mock_crisis_name}'")
        
        # Test 3: Insert mock crisis alert
        logger.info("Test 3: Testing crisis_alert table operations")
        mock_severity = "extremely_high"
        mock_note = "The use of the phrase 'I'm going to kill myself' clearly indicates that the person is expressing thoughts of suicide. This is a clear indication of suicidal ideation and a potential mental health concern."
        
        alert_result = store_crisis_alert(
            connection, 
            test_account_id, 
            crisis_id, 
            mock_severity, 
            mock_note
        )
        logger.info(f"Crisis alert stored successfully: {alert_result}")
        
        # Test 4: Verify the data was inserted correctly
        logger.info("Test 4: Verifying inserted data")
        verify_query = """
        SELECT ca.crisis_alert_id, ca.crisis_alert_severity, ca.crisis_alert_note, 
               c.crisis_name, ca.crisis_alert_ts
        FROM crisis_alert ca
        JOIN crisis c ON ca.crisis_id = c.crisis_id
        WHERE ca.account_id = %s
        ORDER BY ca.crisis_alert_ts DESC
        LIMIT 1
        """
        verification = execute_query(connection, verify_query, (test_account_id,))
        
        if verification:
            logger.info(f"Verification successful: {verification[0]}")
            # Convert datetime to string for JSON serialization
            verification_data = dict(verification[0])
            if 'crisis_alert_ts' in verification_data:
                verification_data['crisis_alert_ts'] = str(verification_data['crisis_alert_ts'])
        else:
            logger.warning("No verification data found")
            verification_data = None
        
        return {
            "status": "success",
            "messages_found": len(messages),
            "crisis_id": crisis_id,
            "alert_result": alert_result,
            "verification": verification_data,
            "test_account_id": test_account_id
        }
        
    except Exception as e:
        logger.error(f"Error in database operations test: {e}")
        raise e

def lambda_handler(event, context):
    """
    Main Lambda handler function - Database Connection Test
    """
    connection = None
    
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        logger.info("Starting Lambda function...")
        
        # Test 1: Check database configuration
        logger.info("Test 1: Checking database configuration")
        db_config = {
            'DB_HOST': DB_HOST,
            'DB_USER': DB_USER, 
            'DB_PASSWORD': DB_PASSWORD,
            'DB_NAME': DB_NAME,
            'DB_PORT': DB_PORT
        }
        
        missing_vars = []
        for var_name, var_value in db_config.items():
            if not var_value:
                missing_vars.append(var_name)
            else:
                # Mask password for security
                display_value = '*' * len(var_value) if 'PASSWORD' in var_name else var_value
                logger.info(f"{var_name}: {display_value}")
        
        if missing_vars:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': f'Missing environment variables: {missing_vars}'
                })
            }
        
        # Test 2: Attempt database connection
        logger.info("Test 2: Attempting database connection")
        connection = create_connection()
        
        # Test 3: query test
        logger.info("Test 3: Testing database_operations")
        result = test_database_operations(connection)
        
        logger.info(f"Database operations test completed: {result}")
        
        # Return success
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Database operations test completed',
                'test_result': result
            })
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
    
    finally:
        # Always close the database connection
        if connection:
            connection.close()
            logger.info("Database connection closed")

def test_database_workflow():
    """
    Test function to demonstrate the database operations workflow
    This can be called independently for testing purposes
    """
    connection = None
    
    try:
        logger.info("Starting database operations workflow test")
        
        # Create database connection
        connection = create_connection()
        
        # Run database operations test
        result = test_database_operations(connection)
        
        logger.info(f"Database operations test completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in test workflow: {e}")
        raise e
    
    finally:
        if connection:
            connection.close()
            logger.info("Test database connection closed")

# Example SQL table creation (run this separately to set up your database)
"""
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Crisis detection related tables (based on model.py schema)
CREATE TABLE crisis (
    crisis_id INT AUTO_INCREMENT PRIMARY KEY,
    crisis_name TEXT NOT NULL
);

CREATE TABLE crisis_alert (
    crisis_alert_id VARCHAR(36) PRIMARY KEY,
    account_id VARCHAR(36) NOT NULL,
    crisis_id INT NOT NULL,
    crisis_alert_severity TEXT NOT NULL,
    crisis_alert_status TEXT NOT NULL,
    crisis_alert_note TEXT,
    crisis_alert_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (crisis_id) REFERENCES crisis(crisis_id) ON DELETE CASCADE
);
"""