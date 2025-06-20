import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseClient:
    def __init__(self, host="localhost", port=3306, user="root", password="Zhanke0211...", database=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            logger.info("成功连接到数据库")
        except Error as e:
            logger.error(f"连接数据库失败: {e}")
            raise

    def get_databases(self) -> List[str]:
        if not self.connection:
            self.connect()
        cursor = self.connection.cursor()
        cursor.execute("SHOW DATABASES")
        return [db[0] for db in cursor.fetchall()]

    def get_tables(self, database: str) -> List[str]:
        if not self.connection or self.connection.database != database:
            self.disconnect()
            self.connection = None
            self.database = database
            self.connect()
        cursor = self.connection.cursor()
        cursor.execute("SHOW TABLES")
        return [table[0] for table in cursor.fetchall()]

    def get_table_schema(self, database: str, table: str) -> str:
        if not self.connection or self.connection.database != database:
            self.disconnect()
            self.connection = None
            self.database = database
            self.connect()
        cursor = self.connection.cursor()
        cursor.execute(f"SHOW CREATE TABLE `{table}`")
        result = cursor.fetchone()[1]
        return result

    def get_all_schemas(self, database: str) -> Dict[str, str]:
        tables = self.get_tables(database)
        schemas = {}
        for table in tables:
            schemas[table] = self.get_table_schema(database, table)
        return schemas

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("数据库连接已关闭")

    def generate_er_json(self, database: str) -> Dict:
        """
        简单生成 ER 关系图的 JSON 结构（模拟外键关系）
        实际可以使用 information_schema 查询 foreign_key_columns 表来获取真实数据
        """
        tables = self.get_tables(database)
        er_data = {"tables": [], "relationships": []}

        for table in tables:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{table}'
            """)
            columns = cursor.fetchall()

            er_data["tables"].append({
                "name": table,
                "columns": [
                    {
                        "name": col["COLUMN_NAME"],
                        "type": col["DATA_TYPE"],
                        "nullable": col["IS_NULLABLE"] == "YES",
                        "key": col["COLUMN_KEY"]
                    } for col in columns
                ]
            })

        # TODO: 查询 information_schema.KEY_COLUMN_USAGE 获取外键关系
        return er_data