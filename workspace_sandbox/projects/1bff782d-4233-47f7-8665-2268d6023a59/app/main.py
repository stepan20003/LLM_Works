import psycopg2
from config import DatabaseConfig

def main(database, database_config):
    # Connect to the database
    database.connect()

    # Execute a query
    query = "SELECT * FROM tasks"
    results = database.execute_query(query)

    # Print the results
    print(results)