import concurrent
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Any, List, Dict, Optional
from sentence_transformers import SentenceTransformer
from backend.services.milvus_client import MilvusClient
from backend.utils.config import get_settings
import threading
from backend.models.m3e_base import model  
from fastapi import UploadFile, File
import pandas as pd
from io import StringIO
router = APIRouter(tags=["VectorDB"])


# 全局共享 Milvus 客户端实例
_milvus_client = None
_lock = threading.Lock()

def get_milvus_client():
    global _milvus_client
    with _lock:
        if _milvus_client is None:
            settings = get_settings()
            _milvus_client = MilvusClient(host=settings.MILVUS_HOST, port=settings.MILVUS_PORT)
            _milvus_client.connect()
    return _milvus_client


# ===== 请求模型定义 =====

class VectorSearchRequest(BaseModel):
    vquery: str
    collections: List[str]  # 自定义要检索哪些集合
    top_k: int = 5

class CreateCollectionRequest(BaseModel):
    collection_name: str

class ClearCollectionRequest(BaseModel):
    collection_name: str
    confirm: bool

class InsertDataRequest(BaseModel):
    collection_name: str
    data: List[Dict]



# ===== 接口实现 =====
class EmbeddingRequest(BaseModel):
    text: str

@router.post("/generate-embedding")
def generate_embedding(request: EmbeddingRequest):
    """
    根据提供的文本生成嵌入向量。
    """
    try:
        embedding = model.encode([request.text]).tolist()[0]
        return {"embedding": embedding}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embedding: {str(e)}")


@router.post("/search")
def vector_search(request: VectorSearchRequest, client: Any = Depends(get_milvus_client)):
    query = request.vquery
    if not query:
        raise HTTPException(status_code=400, detail="Query string is required.")

    if not hasattr(client, 'connected') or not client.connected:
        raise HTTPException(status_code=500, detail="Milvus connection not initialized.")

    try:
        # 使用模型生成查询嵌入
        query_embedding = model.encode([query]).tolist()[0]

        from concurrent.futures import ThreadPoolExecutor
        results = {}
        with ThreadPoolExecutor(max_workers=len(request.collections)) as executor:
            future_to_col = {
                executor.submit(client.search, col, query_embedding, request.top_k): col
                for col in request.collections
            }
            for future in concurrent.futures.as_completed(future_to_col):
                col = future_to_col[future]
                try:
                    results[col] = future.result()
                except Exception as exc:
                    results[col] = {"error": str(exc)}

        return {
            "query": query,
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during search: {str(e)}")

@router.post("/search-qa")
def search_qa_vector(
    request: VectorSearchRequest,
    client: MilvusClient = Depends(get_milvus_client)
):
    """QA专用搜索接口"""
    query = request.vquery
    if not query:
        raise HTTPException(status_code=400, detail="Query string is required.")

    try:
        # 生成查询嵌入
        query_embedding = model.encode([query]).tolist()[0]
        
        results = {}
        for collection in request.collections:
            # QA专用搜索
            matched_results = client.search_qa(
                collection_name=collection,
                query_embedding=query_embedding,
                top_k=request.top_k
            )
            results[collection] = matched_results

        return {
            "query": query,
            "results": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"QA search error: {str(e)}"
        )


@router.get("/collections")
def list_collections(client: MilvusClient = Depends(get_milvus_client)):
    """列出所有可用的向量集合"""
    try:
        return {"collections": client.list_collections()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-collection")
def create_collection(request: CreateCollectionRequest, client: MilvusClient = Depends(get_milvus_client)):
    """创建一个新的向量集合"""
    try:
        client.create_collection(request.collection_name)
        return {"message": f"集合 {request.collection_name} 创建成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-qa-collection")
def create_collection(request: CreateCollectionRequest, client: MilvusClient = Depends(get_milvus_client)):
    """创建一个新的向量集合"""
    try:
        client.create_qa_collection(request.collection_name)
        return {"message": f"集合 {request.collection_name} 创建成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/clear-collection")
def clear_collection(request: ClearCollectionRequest, client: MilvusClient = Depends(get_milvus_client)):
    """清空指定集合的数据和索引"""
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Operation not confirmed.")
    try:
        client.clear_collection_data(request.collection_name)
        return {"message": f"集合 {request.collection_name} 数据已清除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insert-data")
def insert_data(request: InsertDataRequest, client: MilvusClient = Depends(get_milvus_client)):
    """向指定集合插入数据"""
    try:
        # 处理数据并生成嵌入向量
        processed_data = []
        for item in request.data:
            # 确保数据包含必要的内容字段
            if "content" not in item:
                raise HTTPException(
                    status_code=400,
                    detail=f"Item missing 'content' field: {item}"
                )
            
            # 生成嵌入向量
            content = item["content"]
            embedding = model.encode([content]).tolist()[0]
            
            # 创建新的数据项，包含嵌入向量
            processed_item = {
                **item,  # 保留原始字段
                "embedding": embedding  # 添加嵌入向量
            }
            processed_data.append(processed_item)
        
        # 插入处理后的数据
        client.insert_and_create_index(request.collection_name, processed_data)
        return {
            "message": f"已插入 {len(processed_data)} 条数据到集合 {request.collection_name}",
            "processed_count": len(processed_data)
        }
    except HTTPException:
        raise  # 直接抛出已有的HTTP异常
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing or inserting data: {str(e)}"
        )
    
@router.post("/insert-qa-csv")
async def insert_qa_csv(
    collection_name: str = Query(..., description="集合名称"),
    csv_file: UploadFile = File(..., description="CSV文件"),
    client: MilvusClient = Depends(get_milvus_client)
):
    """
    从CSV文件导入QA数据到指定集合
    CSV格式要求：
    - 必须有"问题"和"答案"两列
    - 文件编码应为UTF-8
    """
    try:
        # 读取CSV文件
        contents = await csv_file.read()
        df = pd.read_csv(StringIO(contents.decode('utf-8')))
        
        # 检查必要列是否存在
        if "问题" not in df.columns or "答案" not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="CSV文件必须包含'问题'和'答案'两列"
            )

        # 处理数据并生成嵌入向量
        questions = []
        answers = []
        embeddings = []
        
        for _, row in df.iterrows():
            question = str(row["问题"]).strip()
            answer = str(row["答案"]).strip()
            
            if not question or not answer:
                continue
            
            try:
                embedding = model.encode([question]).tolist()[0]
                if len(embedding) != 768:
                    continue
                
                questions.append(question)
                answers.append(answer)
                embeddings.append(embedding)
            except Exception as e:
                continue

        if not questions:
            raise HTTPException(
                status_code=400,
                detail="没有有效的QA数据可插入"
            )

        # 准备插入数据
        data_to_insert = [
            {"question": q, "answer": a, "embedding": e}
            for q, a, e in zip(questions, answers, embeddings)
        ]

        # 插入数据
        client.insert_qa_and_create_index(collection_name, data_to_insert)
        
        return {
            "message": f"成功插入 {len(questions)} 条QA数据到集合 {collection_name}",
            "processed_count": len(questions),
            "failed_count": len(df) - len(questions),
            "collection": collection_name
        }

    except HTTPException:
        raise
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV文件为空")
    except pd.errors.ParserError:
        raise HTTPException(status_code=400, detail="CSV文件解析失败")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码应为UTF-8")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理CSV文件失败: {str(e)}"
        )


@router.post("/create-index")
def create_index(collection_name: str, client: MilvusClient = Depends(get_milvus_client)):
    """为指定集合创建索引"""
    try:
        client.create_index(collection_name)
        return {"message": f"集合 {collection_name} 索引创建完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))