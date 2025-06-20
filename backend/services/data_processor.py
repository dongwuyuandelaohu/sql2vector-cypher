from typing import List, Dict, Any, Optional, Union
from sqlglot import parse_one, exp


class DataProcessor:
    def __init__(self):
        pass

    def ddl_to_graph(self, ddl_statements: List[str]) -> Dict[str, List]:
        """
        将 DDL 转换为图结构（nodes + relationships）
        :param ddl_statements: SQL CREATE TABLE 语句列表
        :return: 包含 nodes 和 relationships 的字典
        """
        nodes = []
        relationships = []

        for ddl in ddl_statements:
            parsed = parse_one(ddl)
            if not isinstance(parsed, exp.Create):
                continue

            table_name = parsed.find(exp.Table).name
            schema = parsed.find(exp.Schema)

            # 添加表节点
            nodes.append({
                "id": f"table_{table_name}",
                "labels": ["Table"],
                "properties": {
                    "name": table_name,
                    "description": ""
                }
            })

            # 遍历字段
            for column in schema.expressions:
                if isinstance(column, exp.ColumnDef):
                    col_name = column.this.name
                    col_type = column.kind.name

                    # 添加字段节点
                    col_id = f"column_{table_name}_{col_name}"
                    nodes.append({
                        "id": col_id,
                        "labels": ["Column"],
                        "properties": {
                            "name": col_name,
                            "type": col_type,
                            "description": ""
                        }
                    })

                    # 建立字段与表的关系
                    relationships.append({
                        "id": f"rel_{col_id}_in_table",
                        "type": "BELONGS_TO",
                        "start_node": col_id,
                        "end_node": f"table_{table_name}",
                        "properties": {}
                    })

                    # 检查是否是外键
                    for constraint in column.constraints:
                        if isinstance(constraint.this, exp.Reference):
                            ref_table = constraint.this.table
                            relationships.append({
                                "id": f"rel_{col_id}_fk_to_{ref_table}",
                                "type": "REFERENCES",
                                "start_node": col_id,
                                "end_node": f"table_{ref_table}",
                                "properties": {
                                    "reference_column": constraint.this.column
                                }
                            })

        return {"nodes": nodes, "relationships": relationships}

    def extract_table_descriptions(self, ddl_statements: List[str]) -> List[Dict]:
        """
        从 DDL 中提取表名和字段信息，用于构建向量库中的文本描述
        :param ddl_statements: SQL CREATE TABLE 语句列表
        :return: 列表，每项为 {'text': "...", 'metadata': {...}}
        """
        descriptions = []

        for ddl in ddl_statements:
            parsed = parse_one(ddl)
            if not isinstance(parsed, exp.Create):
                continue

            table_name = parsed.find(exp.Table).name
            schema = parsed.find(exp.Schema)

            fields = []
            for column in schema.expressions:
                if isinstance(column, exp.ColumnDef):
                    col_name = column.this.name
                    col_type = column.kind.name
                    fields.append(f"{col_name} ({col_type})")

            description = f"Table '{table_name}' has columns: {', '.join(fields)}"
            descriptions.append({
                "text": description,
                "metadata": {
                    "table": table_name,
                    "fields": fields
                }
            })

        return descriptions