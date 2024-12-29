import mysql.connector
import time

class DB:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.passfail = None
        self.username = None
        self.databaseName = None

    async def connect(self, database, username, password, host="db", port=3306):
        """
        Connect to the MySQL database. 
        :param database: Name of the database to connect to
        :param username: MySQL username
        :param password: MySQL password
        :param host:     Hostname of the DB container or server (default "db")
        :param port:     Port number for MySQL (default 3306)
        """
        try:
            self.connection = mysql.connector.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                database=database
            )
            # Dict cursor so we get results as dictionaries
            self.cursor = self.connection.cursor(dictionary=True)

            # If we've made it this far, connection is successful
            self.passfail = True
            self.username = username
            self.databaseName = database
            return True
        
        except Exception as e:
            print(f"Connection error: {e}")
            self.passfail = False
            return False
