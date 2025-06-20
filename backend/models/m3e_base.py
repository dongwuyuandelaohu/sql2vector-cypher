# backend/models.py

from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

try:
    logger.info("正在加载嵌入模型...")
    model = SentenceTransformer('E:/model/m3e-base')
    logger.info("嵌入模型加载成功。")
except Exception as e:
    logger.error(f"加载嵌入模型失败: {str(e)}")
    raise