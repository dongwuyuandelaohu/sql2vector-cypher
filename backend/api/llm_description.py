import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from backend.services.llm import LLMClient, generate_vector_items
from backend.services.database_client import DatabaseClient
from pydantic import BaseModel
import functools
from typing import List, Optional, Dict, Any
from backend.utils.config import get_settings
from backend.services.task_manager import task_manager
router = APIRouter(tags=["Table Description"])

class TableInfo(BaseModel):
    table_name: str
    chinese_name: str
    description: str
    purpose: str

class FieldInfo(BaseModel):
    field_name: str
    chinese_name: str
    data_type: str
    description: str
    usage: str

class MetricInfo(BaseModel):
    metric_name: str
    expression: str
    scenario: str
    description: str

class TableDescriptionResponse(BaseModel):
    table_info: TableInfo
    fields: List[FieldInfo]
    metrics: List[MetricInfo]

def get_llm_client():
    settings = get_settings()
    client = LLMClient(
        api_url=settings.LLM_API_URL,
        api_key=settings.LLM_API_KEY
    )
    return client

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

@router.get("/database/{database}", response_model=List[TableDescriptionResponse])
def describe_all_tables(
    database: str,
    background_tasks: BackgroundTasks,
    tables: Optional[List[str]] = Query(None),  # 支持传入多个表名进行过滤
    db_client: DatabaseClient = Depends(get_db_client),
    llm_client: LLMClient = Depends(get_llm_client)
):
    """
    获取指定数据库中所有表的结构化描述。
    
    参数：
    - database: 数据库名
    - tables: (可选) 指定要处理的表名列表，不传则处理全部表
    """
    task_id = str(uuid.uuid4())
    def worker():
        try:
            all_tables = db_client.get_tables(database)
            
            if not all_tables:
                raise HTTPException(status_code=404, detail="数据库中没有表")

            if tables:
                valid_tables = [t for t in tables if t in all_tables]
                if len(valid_tables) != len(tables):
                    invalid = set(tables) - set(all_tables)
                    raise HTTPException(status_code=404, detail=f"以下表不存在: {', '.join(invalid)}")
                target_tables = valid_tables
            else:
                target_tables = all_tables

            results = []
            for table in target_tables:
                if task_manager.tasks[task_id].cancelled():  # 检查是否被取消
                    raise Exception("Task cancelled")
                
                table_sql = db_client.get_table_schema(database, table)
                description = llm_client.generate_table_description(table_sql)
                results.append(description)

            return results
        except Exception as e:
            raise e

    future = task_manager.executor.submit(worker)
    task_manager.add_task(task_id, future)
    
    # 任务完成后自动清理
    background_tasks.add_task(
        functools.partial(task_manager.cancel_task, task_id)
    )

    try:
        return future.result()  # 阻塞直到任务完成
    except Exception as e:
        if "cancelled" in str(e):
            raise HTTPException(status_code=499, detail="任务已被中止")
        raise HTTPException(status_code=500, detail=str(e))    

@router.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: str):
    """
    中止指定任务
    """
    if task_manager.cancel_task(task_id):
        return {"message": f"任务 {task_id} 已中止"}
    raise HTTPException(status_code=404, detail="任务不存在")


class MetadataInput(BaseModel):
    metadata: List[Dict[str, Any]]  
    
@router.post("/format-vector-items", response_model=List[Dict])
def format_vector_items_endpoint(input_data: MetadataInput):
    """
    将大模型生成的 metadata 列表格式化为知识库标准格式。
    
    输入：
    - metadata_list: 包含多个 metadata 的列表，每个 metadata 是包含 table_info、fields、metrics 的字典
    
    输出：
    - list of items，每项包含 type, content, metadata
    """
    try:
        all_items = []
        # 遍历每个 metadata 字典并生成 items
        for metadata in input_data.metadata:
            print(f"Processing metadata: {metadata}")
            items = generate_vector_items(metadata)
            print(f"Generated items: {items}")
            all_items.extend(items)
        return all_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"格式化失败: {str(e)}")
