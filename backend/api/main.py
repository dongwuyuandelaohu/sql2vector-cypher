from fastapi import FastAPI, HTTPException
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from backend.models.m3e_base import model
from sentence_transformers import SentenceTransformer
# 导入各模块的路由
from .database import router as database_router
from .vector_db import router as vector_db_router
from backend.api.graph_db import router as graph_db_router
from .llm_description import router as llm_description_router
# from .embedding import router as embed_router
# 创建 FastAPI 实例
app = FastAPI(
    title="Text2SQL Backend API",
    description="API for managing database connections, embedding knowledge into vector DB, and building Neo4j graphs.",
    version="0.1.0"
)
logger = logging.getLogger(__name__)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，可根据需要限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理器：处理请求参数错误
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation Error", "details": exc.errors()}
    )

# 健康检查接口
@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok"}

# 注册子路由
app.include_router(llm_description_router, prefix="/api/llm", tags=["LLM Description"])
app.include_router(database_router, prefix="/api/database", tags=["Database"])
app.include_router(vector_db_router, prefix="/api/vector", tags=["VectorDB"])
app.include_router(graph_db_router, prefix="/api/graph", tags=["GraphDB"])
# app.include_router(embed_router, prefix="/api/embed", tags=["Embed"])

# 启动说明：
# 使用 uvicorn 运行：uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload