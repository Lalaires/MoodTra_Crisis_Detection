import json
import psycopg2
import psycopg2.extras
import os
import logging
from uuid import uuid4
from datetime import datetime, timezone
from crisis_pipeline import CrisisDetector

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lazy-initialized singleton for CrisisDetector to avoid reloading models repeatedly
_crisis_detector = None

def get_crisis_detector():
    global _crisis_detector
    if _crisis_detector is None:
        logger.info("Initializing CrisisDetector models...")
        _crisis_detector = CrisisDetector()
        logger.info("CrisisDetector initialized.")
    return _crisis_detector

def _normalize_to_utc(dt):
    """
    Ensure a datetime is timezone-aware and in UTC.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def create_connection():
    """
    Create database connection using environment variables
    """
    try:
        logger.info("Attempting to connect to database...")
        
        # Get database credentials from environment variables
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=os.getenv('DB_PORT'),
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

def fetch_latest_child_messages(connection, account_id, limit=5):
    """
    Fetch the latest child messages from the newest session for a specific account
    Returns messages and the timestamp of the latest message
    """
    try:
        query = """
        WITH newest_session AS (
            SELECT cs.session_id
            FROM chat_session cs
            JOIN chat_message cm ON cs.session_id = cm.session_id
            WHERE cs.account_id = %s AND cm.message_role = 'child'
            ORDER BY cm.message_ts DESC
            LIMIT 1
        )
        SELECT cm.message_text, cm.message_ts
        FROM chat_message cm
        WHERE cm.session_id = (SELECT session_id FROM newest_session)
          AND cm.message_role = 'child'
        ORDER BY cm.message_ts DESC 
        LIMIT %s
        """
        messages = execute_query(connection, query, (account_id, limit))
        logger.info(f"Fetched {len(messages)} child messages from newest session for account {account_id}")
        return messages
    except Exception as e:
        logger.error(f"Error fetching child messages: {e}")
        raise e

def get_all_child_accounts(connection):
    """
    Get all child accounts from the account table
    """
    try:
        query = """
        SELECT account_id, account_type
        FROM account
        WHERE account_type = 'child'
        ORDER BY account_id
        """
        accounts = execute_query(connection, query)
        logger.info(f"Found {len(accounts)} child accounts in database")
        return [account['account_id'] for account in accounts]
    except Exception as e:
        logger.error(f"Error fetching child accounts: {e}")
        raise e

def get_crisis_id(connection, crisis_name):
    """
    Get existing crisis_id entry
    """
    try:
        # get existing crisis
        select_query = "SELECT crisis_id FROM crisis WHERE crisis_name = %s"
        existing = execute_query(connection, select_query, (crisis_name,))
        return existing[0]['crisis_id']
        
    except Exception as e:
        logger.error(f"Error getting crisis_id: {e}")
        raise e

def get_last_message_timestamp(connection, account_id):
    """
    Get the most recent processed message timestamp for an account
    """
    try:
        # Use MAX to get the latest processed message timestamp regardless of alert insertion order
        query = """
        SELECT MAX(last_msg_ts) AS last_msg_ts
        FROM crisis_alert
        WHERE account_id = %s
        """
        result = execute_query(connection, query, (account_id,))
        if result and result[0]['last_msg_ts']:
            return result[0]['last_msg_ts']
        return None
    except Exception as e:
        logger.error(f"Error fetching last message timestamp: {e}")
        raise e

def store_crisis_alert(connection, account_id, crisis_id, severity, note=None, last_msg_ts=None):
    """
    Store crisis alert information in the crisis_alert table
    """
    try:
        crisis_alert_id = str(uuid4())
        current_time = datetime.now(timezone.utc)
        
        query = """
        INSERT INTO crisis_alert 
        (crisis_alert_id, account_id, crisis_id, crisis_alert_severity, 
         crisis_alert_status, crisis_alert_note, crisis_alert_ts, last_msg_ts)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            crisis_alert_id,
            account_id,
            crisis_id,
            severity,
            'pending',  # Default status
            note,  # Can be None/NULL
            current_time,
            last_msg_ts  # Timestamp of the latest message processed
        )
        
        result = execute_query(connection, query, params)
        logger.info(f"Stored crisis alert with ID: {crisis_alert_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error storing crisis alert: {e}")
        raise e

def process_crisis_detection(connection, account_id):
    """
    Process crisis detection for the latest 10 child messages as a batch
    """
    try:
        logger.info(f"Starting crisis detection for account: {account_id}")
        
        # Fetch latest 10 child messages
        messages = fetch_latest_child_messages(connection, account_id, 10)
        logger.info(f"Found {len(messages)} child messages to process as batch")
        
        if not messages:
            logger.info("No child messages found for processing")
            return {
                "status": "success",
                "messages_processed": 0,
                "alerts_created": 0
            }
        
        # Get the timestamp of the latest message
        latest_msg_ts = messages[0]['message_ts']  # First message is the latest due to ORDER BY DESC
        
        # Skip if we've already processed up to this timestamp (use <= to handle duplicates)
        last_processed_ts = get_last_message_timestamp(connection, account_id)
        logger.info(f"Last processed timestamp: {last_processed_ts}")

        # Normalize to UTC to avoid naive/aware comparison errors
        latest_msg_ts_utc = _normalize_to_utc(latest_msg_ts)
        last_processed_ts_utc = _normalize_to_utc(last_processed_ts)
        
        if last_processed_ts_utc and latest_msg_ts_utc <= last_processed_ts_utc:
            logger.info(
                f"Latest message_ts {latest_msg_ts_utc} is not newer than last processed {last_processed_ts_utc} - skipping"
            )
            return {
                "status": "success",
                "messages_processed": len(messages),
                "alerts_created": 0,
                "reason": "messages_already_processed"
            }
        
        # Get lazy-initialized crisis detector
        crisis_detector = get_crisis_detector()

        # Build chronological, sanitized, and trimmed message context
        child_history_rows = list(reversed(messages))
        child_history = [msg.get('message_text') for msg in child_history_rows]
        lines = []
        for msg_text in child_history:
            safe_msg = (msg_text or "").strip()
            if len(safe_msg) > 800:
                safe_msg = safe_msg[:800] + " ..."
            lines.append(f"{safe_msg}")
        child_history_context = "\n".join(lines)
        logger.info(
            f"Processing {len(messages)} messages as newline-joined context"
        )

        # Process context through crisis detection (already returns a dict)
        crisis_dict = crisis_detector.detect_crisis(child_history_context)
        logger.info(f"Crisis detection result: {crisis_dict}")
        
        # Get or create crisis_id
        crisis_name = crisis_dict.get('crisis_name', 'unknown')
        crisis_id = get_crisis_id(connection, crisis_name.lower())
        
        # Store crisis alert
        severity = crisis_dict.get('severity')
        note = crisis_dict.get('crisis_note')
        
        alert_result = store_crisis_alert(
            connection,
            account_id,
            crisis_id,
            severity,
            note,
            latest_msg_ts_utc
        )
        
        logger.info(f"Crisis alert stored successfully: {alert_result}")
        
        return {
            "status": "success",
            "messages_processed": len(messages),
            "alerts_created": 1,
            "crisis_result": crisis_dict,
            "alert_id": alert_result.get('affected_rows', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Error in batch crisis detection processing: {e}")
        raise e

def process_all_accounts(connection):
    """
    Process crisis detection for all accounts in the database and return summary counters only.
    """
    try:
        logger.info("Starting crisis detection for all accounts")

        # Get all account IDs
        account_ids = get_all_child_accounts(connection)

        if not account_ids:
            logger.info("No accounts found in database")
            return {
                "status": "success",
                "total_accounts": 0,
                "processed_accounts": 0,
                "skipped_already_processed": 0,
                "failed_accounts": 0,
                "total_alerts_created": 0
            }

        total_alerts_created = 0
        processed_accounts = 0
        skipped_already_processed = 0
        failed_accounts = 0

        # Process each account
        for i, account_id in enumerate(account_ids):
            logger.info(f"Processing account {i+1}/{len(account_ids)}: {account_id}")

            try:
                result = process_crisis_detection(connection, account_id)
                processed_accounts += 1

                # Track if we skipped due to already processed messages
                if result.get("reason") == "messages_already_processed":
                    skipped_already_processed += 1

                total_alerts_created += result.get("alerts_created", 0)

            except Exception as e:
                failed_accounts += 1
                logger.error(f"Error processing account {account_id}: {e}")

        logger.info(
            f"Crisis detection completed for {len(account_ids)} accounts. "
            f"Processed: {processed_accounts}, Skipped(already processed): {skipped_already_processed}, "
            f"Failed: {failed_accounts}, Alerts created: {total_alerts_created}"
        )

        return {
            "status": "success",
            "total_accounts": len(account_ids),
            "processed_accounts": processed_accounts,
            "skipped_already_processed": skipped_already_processed,
            "failed_accounts": failed_accounts,
            "total_alerts_created": total_alerts_created
        }

    except Exception as e:
        logger.error(f"Error in process_all_accounts: {e}")
        raise e

def lambda_handler(event, context):
    """
    Main Lambda handler function - Crisis Detection Pipeline for All Accounts
    """
    connection = None
    
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        logger.info("Starting Crisis Detection Lambda function for all accounts...")
        
        # Create database connection
        connection = create_connection()
        
        # Process crisis detection for all accounts
        result = process_all_accounts(connection)
        
        logger.info(f"Crisis detection completed for all accounts: {result}")
        
        # Return success
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Crisis detection completed for all accounts',
                'result': result
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
