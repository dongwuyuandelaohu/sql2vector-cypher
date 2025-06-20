from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Neo4j 配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # Milvus 配置
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: str = "19530"

    # 嵌入模型配置（可选）
    EMBEDDING_MODEL_NAME: str = "text-embedding-ada-002"
    EMBEDDING_DIMENSION: int = 768
    
    DB_HOST: str = "localhost"
    DB_PORT: str = "3306"
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    LLM_API_URL: str = "填入你的llm调用地址"
    LLM_API_KEY: str = "填入你的key"

    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: str = "19530"
    DEVICE: str = "cpu"  
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    print("Loading settings from environment variables or .env file")
    return Settings()