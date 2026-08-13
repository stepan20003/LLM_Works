import psycopg2
from config import DatabaseConfig

class Database:
    def __init__(self):
        self.config = DatabaseConfig()
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=self.config.DB_HOST,
                database=self.config.DB_NAME,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD,
                port=self.config.DB_PORT
            )
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")

    def execute_query(self, query):
        if self.conn:
            cur = self.conn.cursor()
            cur.execute(query)
            self.conn.commit()
            return cur.fetchall()
        else:
            print("Database connection not established")
            return None