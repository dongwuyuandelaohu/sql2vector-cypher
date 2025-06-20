# backend/api/database.py

from fastapi import APIRouter, Depends, HTTPException
from backend.services.database_client import DatabaseClient
from backend.utils.config import get_settings
from pydantic import BaseModel
from typing import List, Optional, Dict

class TableSchema(BaseModel):
    table_name: str
    schema_sql: str

class DatabaseInfo(BaseModel):
    database_name: str
    tables: List[str]

class SchemaResponse(BaseModel):
    database: str
    tables: List[TableSchema]
router = APIRouter(tags=["Database"])

def get_db_client():
    settings = get_settings()
    client = DatabaseClient(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    try:
        yield client
    finally:
        client.disconnect()

@router.get("/databases", response_model=List[str])
def list_databases(client: DatabaseClient = Depends(get_db_client)):
    """获取所有数据库名称"""
    try:
        return client.get_databases()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/databases/{database}/tables", response_model=List[str])
def list_tables(database: str, client: DatabaseClient = Depends(get_db_client)):
    """获取指定数据库中的所有表"""
    try:
        return client.get_tables(database)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/databases/{database}/schema", response_model=Dict[str, str])
def get_all_schemas(database: str, client: DatabaseClient = Depends(get_db_client)):
    """获取指定数据库中所有表的建表语句"""
    try:
        return client.get_all_schemas(database)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/databases/{database}/er", response_model=Dict)
def get_er_diagram(database: str, client: DatabaseClient = Depends(get_db_client)):
    """生成指定数据库的 ER 图 JSON 数据"""
    try:
        return client.generate_er_json(database)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))