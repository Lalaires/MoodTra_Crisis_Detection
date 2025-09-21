import pymysql

DB_HOST = "postgresql+psycopg2://ta24:cojxe8-zofzox-huzgYk@db-ta24-mindpal.cnwcamiuul3a.ap-southeast-4.rds.amazonaws.com:5432/postgres"
DB_USER = "ta24"
DB_PASSWORD = "cojxe8-zofzox-huzgYk"
DB_NAME = "postgres"
DB_PORT = 5432

cursor.execute("SELECT * FROM chat_session")
print(cursor.fetchall())

def lambda_handler(event, context):
    print("Entered Lambda function")
    try:
        connection = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, port=DB_PORT)
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM chat_session")
            result = cursor.fetchall()

    except Exception as e:
        print(f"Error: {e}")
        return {
            "statusCode": 500,
            "body": f"Error: {e}"
        }
    finally:
        connection.close()
    return {
        "statusCode": 200,
        "body": "Lambda function executed successfully"
    }