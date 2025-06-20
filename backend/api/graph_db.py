from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, List, Dict, Optional
from backend.services.neo4j_client import MetadataInput, Neo4jClient, SqlContent, generate_cypher, parse_sql_metadata
from backend.utils.config import get_settings

router = APIRouter(tags=["GraphDB"])

# ===== 请求模型定义 =====
class ClearGraphRequest(BaseModel):
    confirm: bool  # 强制确认是否真的要清空图库

class InsertCypherRequest(BaseModel):
    cypher_content: str  # 从 .cypher 文件加载的内容

class QueryGraphRequest(BaseModel):
    input_string: str  # 要查询的字符串，可能是表名或字段名
    limit: int = 100  # 查询结果限制数量
    return_data: bool = True  # 是否返回完整数据，默认为True

# ===== 初始化 Neo4j 客户端 =====
# def get_neo4j_client():
#     settings = get_settings()
#     client = Neo4jClient(
#         uri=settings.NEO4J_URI,
#         user=settings.NEO4J_USER,
#         password=settings.NEO4J_PASSWORD
#     )
#     yield client
#     client.close()
def get_neo4j_client():
    client = Neo4jClient(
        uri="bolt://localhost:7687",  # 直接写死 URI
        user="neo4j",                # 直接写死用户名
        password="password"          # 直接写死密码
    )
    yield client
    client.close()

# ===== 接口实现 =====

@router.post("/clear")
def clear_graph(request: ClearGraphRequest, client: Neo4jClient = Depends(get_neo4j_client)):
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Operation not confirmed.")
    
    try:
        result = client.clear_graph()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 插入 Cypher 内容到图数据库
@router.post("/insert")
def insert_cypher_data(request: InsertCypherRequest, client: Neo4jClient = Depends(get_neo4j_client)):
    try:
        result = client.insert_cypher_content(request.cypher_content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 查询图数据库中的部分数据（用于前端预览）
@router.post("/query")
def query_graph(request: QueryGraphRequest, client: Neo4jClient = Depends(get_neo4j_client)):
    """
    根据输入的字符串查询图数据库中的表或字段信息
    示例输入：表名 "User" 或字段名 "user_id"
    """
    try:
        result = client.query_database(request.input_string)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return {
            "query": request.input_string,
            "data": result            
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/sql-to-cypher")
async def convert_sql_to_cypher(input_data: SqlContent):
    """
    将 SQL 文件内容转换为 Neo4j 可用的 Cypher 语句。
    
    输入：
    - SQL 文件的内容字符串
    
    输出：
    - 生成的 Cypher 脚本
    """
    try:
        metadata = parse_sql_metadata(input_data.content)
        cypher_script = generate_cypher(metadata)
        return {"cypher": cypher_script}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")