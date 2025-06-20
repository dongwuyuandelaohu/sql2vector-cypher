import re
from neo4j import GraphDatabase
from typing import List, Dict, Any
from pydantic import BaseModel

class SqlContent(BaseModel):
    content: str

class ColumnInfo(BaseModel):
    name: str
    type: str

class RelationshipInfo(BaseModel):
    from_table: str
    from_column: str
    to_table: str
    to_column: str

class TableInfo(BaseModel):
    columns: List[ColumnInfo]
    relationships: List[RelationshipInfo] = []

class MetadataInput(BaseModel):
    fk_tables: Dict[str, TableInfo] = {}
    independent_tables: Dict[str, TableInfo] = {}

    class Config:
        schema_extra = {
            "example": {
                "fk_tables": {
                    "orders": {
                        "columns": [
                            {"name": "order_id", "type": "int"},
                            {"name": "user_id", "type": "int"}
                        ],
                        "relationships": [
                            {
                                "from_table": "orders",
                                "from_column": "user_id",
                                "to_table": "users",
                                "to_column": "user_id"
                            }
                        ]
                    }
                },
                "independent_tables": {
                    "users": {
                        "columns": [
                            {"name": "user_id", "type": "int"},
                            {"name": "username", "type": "string"}
                        ]
                    }
                }
            }
        }


class Neo4jClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.verify_connection()

    def verify_connection(self):
        try:
            self.driver.verify_connectivity()
            print("Connected to Neo4j successfully!")
        except Exception as e:
            print(f"Error connecting to Neo4j: {e}")
            raise e

    def close(self):
        self.driver.close()

    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return list(result)

    # ===== 新增方法：清空图库 =====
    def clear_graph(self):
        """清空整个图数据库"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            return {"message": "Graph database has been cleared."}

    # ===== 新增方法：插入 .cypher 文件内容 =====
    def insert_cypher_content(self, cypher_statements: str):
        """
        接收完整的 cypher 脚本内容，按行解析并逐条执行
        支持 CREATE 和 MERGE 语句
        """
        statements = [
            stmt.strip() for stmt in cypher_statements.split(";") if stmt.strip()
        ]

        success_count = 0
        failed_statements = []

        with self.driver.session() as session:
            for stmt in statements:
                try:
                    session.run(stmt)
                    success_count += 1
                except Exception as e:
                    failed_statements.append({"statement": stmt, "error": str(e)})

        return {
            "total": len(statements),
            "success": success_count,
            "failed": failed_statements
        }
    
    def get_table_info(self, table_name):
        query_columns = """
        MATCH (t:Table {name: $table_name})-[:HAS_COLUMN]->(c:Column)
        OPTIONAL MATCH (c)-[:REFERENCES]->(target_col:Column)
        OPTIONAL MATCH (target_col)<-[:HAS_COLUMN]-(target_table:Table)
        RETURN 
            c.name AS column_name,
            c.type AS data_type,
            target_table.name AS references_table,
            target_col.name AS references_column
        """

        query_referenced_by = """
        MATCH (c:Column {name: $column_name})<-[:REFERENCES]-(source_col:Column)
        MATCH (source_col)<-[:HAS_COLUMN]-(source_table:Table)
        RETURN 
            source_table.name AS referenced_by_table,
            source_col.name AS referenced_by_column
        """

        columns_result = self.run_query(query_columns, {"table_name": table_name})
        all_columns = []

        for record in columns_result:
            column_name = record["column_name"]
            data_type = record["data_type"]
            references_table = record["references_table"]
            references_column = record["references_column"]

            column_info = {
                "name": column_name,
                "type": data_type
            }

            if references_table and references_column:
                column_info["references"] = [
                    {
                        "table": references_table,
                        "column": references_column
                    }
                ]

            # Check for referenced_by relationships
            referenced_by_result = self.run_query(query_referenced_by, {"column_name": column_name})
            referenced_by_list = []
            for ref_record in referenced_by_result:
                referenced_by_list.append({
                    "table": ref_record["referenced_by_table"],
                    "column": ref_record["referenced_by_column"]
                })
            
            if referenced_by_list:
                column_info["referenced_by"] = referenced_by_list

            all_columns.append(column_info)

        if not all_columns:
            return None

        related_tables_set = set()
        for column in all_columns:
            if "references" in column:
                for ref in column["references"]:
                    related_tables_set.add(ref["table"])
            if "referenced_by" in column:
                for ref in column["referenced_by"]:
                    related_tables_set.add(ref["table"])

        related_tables = list(related_tables_set)

        return {
            "table": table_name,
            "columns": all_columns,
            "related_tables": related_tables
        }

    def get_field_info(self, field_name):
        query_find_table = """
        MATCH (t:Table)-[:HAS_COLUMN]->(c:Column {name: $field_name})
        RETURN t.name AS table_name
        LIMIT 1
        """
        table_result = self.run_query(query_find_table, {"field_name": field_name})
        if not table_result:
            return None

        table_name = table_result[0]["table_name"]

        query_references = """
        MATCH (c:Column {name: $field_name})<-[:HAS_COLUMN]-(t:Table {name: $table_name})
        OPTIONAL MATCH (c)-[:REFERENCES]->(target_col:Column)
        OPTIONAL MATCH (target_col)<-[:HAS_COLUMN]-(target_table:Table)
        RETURN 
            target_table.name AS references_table,
            target_col.name AS references_column,
            target_col.type AS data_type
        """

        query_referenced_by = """
        MATCH (c:Column {name: $field_name})<-[:HAS_COLUMN]-(t:Table {name: $table_name})
        OPTIONAL MATCH (referencing_col:Column)-[:REFERENCES]->(c)
        OPTIONAL MATCH (referencing_col)<-[:HAS_COLUMN]-(referencing_table:Table)
        RETURN 
            referencing_table.name AS referenced_by_table,
            referencing_col.name AS referenced_by_column,
            referencing_col.type AS data_type
        """

        references_result = self.run_query(query_references, {"field_name": field_name, "table_name": table_name})
        referenced_by_result = self.run_query(query_referenced_by, {"field_name": field_name, "table_name": table_name})

        if not references_result and not referenced_by_result:
            return None

        references = []
        for record in references_result:
            if record["references_table"] and record["references_column"]:
                references.append({
                    "table": record["references_table"],
                    "column": record["references_column"],
                    "data_type": record["data_type"]
                })

        referenced_by = []
        for record in referenced_by_result:
            if record["referenced_by_table"] and record["referenced_by_column"]:
                referenced_by.append({
                    "table": record["referenced_by_table"],
                    "column": record["referenced_by_column"],
                    "data_type": record["data_type"]
                })

        return {
            "field": field_name,
            "table": table_name,
            "references": references,
            "referenced_by": referenced_by
        }

    def query_database(self, input_string):
        # First, try to find the input string as a table
        print(f"Querying for table or field: {input_string}")
        table_info = self.get_table_info(input_string)
        if table_info:
            return table_info
        print(f"Table '{input_string}' not found, checking as field...")
        # If not found as a table, try to find it as a field
        field_info = self.get_field_info(input_string)
        if field_info:
            return field_info
        print(f"Field '{input_string}' not found in any table.")
        # If neither table nor field is found
        return {"error": "No information found for the provided input."}
    
def generate_cypher(json_data: Dict[str, Any]) -> str:
    cypher_statements = []

    # 创建表节点和字段节点，并建立 HAS_COLUMN 关系
    for table_name, table_info in json_data.get("fk_tables", {}).items():
        cypher_statements.append(f'CREATE (t_{table_name}:Table {{name: "{table_name}"}})')
        for column in table_info.get("columns", []):
            column_name = column["name"]
            column_type = column["type"]
            cypher_statements.append(
                f'CREATE (c_{table_name}_{column_name}:Column {{name: "{column_name}", type: "{column_type}"}})'
            )
            cypher_statements.append(
                f'CREATE (t_{table_name})-[:HAS_COLUMN]->(c_{table_name}_{column_name})'
            )

    for table_name, table_info in json_data.get("independent_tables", {}).items():
        cypher_statements.append(f'CREATE (t_{table_name}:Table {{name: "{table_name}"}})')
        for column in table_info.get("columns", []):
            column_name = column["name"]
            column_type = column["type"]
            cypher_statements.append(
                f'CREATE (c_{table_name}_{column_name}:Column {{name: "{column_name}", type: "{column_type}"}})'
            )
            cypher_statements.append(
                f'CREATE (t_{table_name})-[:HAS_COLUMN]->(c_{table_name}_{column_name})'
            )

    # 创建 REFERENCES 关系
    for table_name, table_info in json_data.get("fk_tables", {}).items():
        for relationship in table_info.get("relationships", []):
            from_table = relationship["from_table"]
            from_column = relationship["from_column"]
            to_table = relationship["to_table"]
            to_column = relationship["to_column"]
            cypher_statements.append(
                f'CREATE (c_{from_table}_{from_column})-[:REFERENCES]->(c_{to_table}_{to_column})'
            )

    return "\n".join(cypher_statements)

def parse_sql_metadata(sql_content: str):
    # Step 0: 移除 /*!50001 ... */ 这类伪注释内容（MySQL 条件注释）
    sql_content = re.sub(r'/\*!\d{5}\s+(.*?)\*/', '', sql_content, flags=re.DOTALL)

    tables = {}
    relationships = []
    fk_tables = set()

    # Step 1: 定位每一个 CREATE TABLE，并用括号配对拿到字段块
    create_re = re.compile(r"CREATE\s+TABLE\s+`([^`]+)`\s*\(", re.IGNORECASE)
    pos = 0
    while (m := create_re.search(sql_content, pos)):
        table = m.group(1)
        i, depth, in_q, q = m.end(), 1, False, ''
        while depth and i < len(sql_content):
            ch = sql_content[i]
            if in_q:
                if ch == q and sql_content[i-1] != '\\':
                    in_q = False
            else:
                if ch in ("'", '"'):
                    in_q, q = True, ch
                elif ch == '(': depth += 1
                elif ch == ')': depth -= 1
            i += 1
        cols_block = sql_content[m.end():i-1]
        pos = i

        # Step 2: 逐行解析字段
        columns = []
        for line in cols_block.splitlines():
            line = line.strip().rstrip(',')
            if not line:
                continue
            # 提取外键信息
            if 'FOREIGN KEY' in line.upper():
                fk = re.search(
                    r'FOREIGN KEY\s*\(([^)]+)\)\s*REFERENCES\s+(?:`[^`]+`\.)?`([^`]+)`\s*\(([^)]+)\)',
                    line, re.I
                )
                if fk:
                    from_cols = [c.strip('` ') for c in fk.group(1).split(',')]
                    to_table = fk.group(2)
                    to_cols = [c.strip('` ') for c in fk.group(3).split(',')]
                    for fc, tc in zip(from_cols, to_cols):
                        relationships.append({
                            "from_table": table,
                            "from_column": fc,
                            "to_table": to_table,
                            "to_column": tc
                        })
                        fk_tables.add(table)
                continue

            if line.upper().startswith(
                ('PRIMARY KEY', 'UNIQUE KEY', 'KEY ', 'CONSTRAINT', 'INDEX')
            ):
                continue

            # 处理字段定义行
            name_match = re.match(r'`([^`]+)`\s+(.*)', line)
            if not name_match:
                continue
            col_name, rest = name_match.groups()

            # 提取 COMMENT
            comment = ''
            cmt_m = re.search(r"COMMENT\s+'((?:[^'\\]|\\.)*)'", rest, re.I)
            if cmt_m:
                comment = cmt_m.group(1)
                rest = rest[:cmt_m.start()].strip()

            # 提取字段类型（第一个 token 是类型及其括号参数）
            typ_m = re.match(r'([A-Za-z0-9]+(?:\s*\([^)]*\))?)', rest)
            col_type = typ_m.group(1).strip() if typ_m else rest.split()[0]

            columns.append({
                "name": col_name,
                "type": col_type,
                "comment": comment
            })

        tables[table] = columns

    # Step 3: 分类输出
    fk_info = {t: {"columns": tables[t], "relationships": []} for t in fk_tables}
    for r in relationships:
        fk_info[r["from_table"]]["relationships"].append(r)

    indep_info = {t: {"columns": cols} for t, cols in tables.items() if t not in fk_tables}

    return {
        "fk_tables": fk_info,
        "independent_tables": indep_info
    }
