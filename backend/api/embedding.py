import json
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import threading
from tqdm import tqdm
import logging
import os

from backend.utils.config import get_settings

router = APIRouter(tags=["Embed"])

# 全局共享模型实例
_embedding_model = None
_model_lock = threading.Lock()

# ===== 请求模型定义 =====
class EmbeddingRequest(BaseModel):
    text: str

class BatchEmbeddingRequest(BaseModel):
    texts: List[str]

class FileEmbeddingRequest(BaseModel):
    file_path: str
    content_field: str = "content"
    output_path: Optional[str] = None
    overwrite: bool = False

# ===== 模型加载函数 =====
def get_embedding_model(model_path: str = "E:/model/m3e-base"):
    settings = get_settings()
    global _embedding_model
    with _model_lock:
        if _embedding_model is None:
            try:
                _embedding_model = SentenceTransformer(
                    model_path,
                    device=settings.DEVICE or "cpu"
                )
                logging.info("Embedding model loaded successfully")
            except Exception as e:
                logging.error(f"Failed to load embedding model: {e}")
                raise
    return _embedding_model

# ===== 接口实现 =====
@router.post("/generate")
def generate_embedding(request: EmbeddingRequest):
    """
    为单个文本生成嵌入向量
    """
    try:
        model = get_embedding_model()
        embedding = model.encode([request.text]).tolist()[0]
        return {"text": request.text, "embedding": embedding}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embedding: {str(e)}")

@router.post("/batch-generate")
def batch_generate_embedding(request: BatchEmbeddingRequest):
    """
    为多个文本批量生成嵌入向量
    """
    try:
        model = get_embedding_model()
        embeddings = model.encode(request.texts).tolist()
        results = [{"text": text, "embedding": emb} for text, emb in zip(request.texts, embeddings)]
        return {"count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating batch embeddings: {str(e)}")

@router.post("/process-file")
def process_json_file(request: FileEmbeddingRequest):
    """
    处理JSON文件并生成嵌入向量
    """
    try:
        model = get_embedding_model()
        
        # 验证输入文件
        input_path = Path(request.file_path)
        if not input_path.exists():
            raise HTTPException(status_code=404, detail="Input file not found")
        
        # 设置输出路径
        output_path = Path(request.output_path) if request.output_path else \
            input_path.parent / f"{input_path.stem}_with_embeddings.json"
        
        if output_path.exists() and not request.overwrite:
            raise HTTPException(status_code=400, detail="Output file already exists and overwrite=False")
        
        # 读取输入文件
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise HTTPException(status_code=400, detail="Input JSON should be a list of items")
        
        # 处理数据
        processed = []
        for item in tqdm(data, desc="Generating embeddings"):
            if request.content_field not in item:
                continue
            
            try:
                text = item[request.content_field]
                embedding = model.encode(text).tolist()
                item["embedding"] = embedding
                processed.append(item)
            except Exception as e:
                logging.warning(f"Failed to process item: {e}")
                continue
        
        # 保存结果
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(processed, f, ensure_ascii=False, indent=2)
        
        return {
            "input_file": str(input_path),
            "output_file": str(output_path),
            "processed_items": len(processed),
            "skipped_items": len(data) - len(processed)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.post("/upload-process")
async def upload_and_process_file(
    file: UploadFile = File(...),
    content_field: str = "content",
    overwrite: bool = False
):
    """
    上传JSON文件并处理生成嵌入向量
    """
    try:
        model = get_embedding_model()
        
        # 读取上传文件
        contents = await file.read()
        data = json.loads(contents)
        
        if not isinstance(data, list):
            raise HTTPException(status_code=400, detail="Uploaded JSON should be a list of items")
        
        # 处理数据
        processed = []
        for item in tqdm(data, desc="Generating embeddings"):
            if content_field not in item:
                continue
            
            try:
                text = item[content_field]
                embedding = model.encode(text).tolist()
                item["embedding"] = embedding
                processed.append(item)
            except Exception as e:
                logging.warning(f"Failed to process item: {e}")
                continue
        
        # 返回结果而不是保存
        return {
            "filename": file.filename,
            "processed_items": len(processed),
            "skipped_items": len(data) - len(processed),
            "results": processed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing uploaded file: {str(e)}")