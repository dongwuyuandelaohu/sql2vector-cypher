import json
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self, model_path: str, device: str = "cpu"):
        """
        初始化嵌入模型
        :param model_path: 模型路径
        :param device: 计算设备 (cuda/cpu)
        """
        self.model = self._load_model(model_path, device)
    
    def _load_model(self, model_path: str, device: str) -> SentenceTransformer:
        """加载嵌入模型"""
        logger.info(f"Loading model from {model_path}...")
        try:
            model = SentenceTransformer(
                model_path,
                device=device,
                tokenizer_kwargs={"padding_side": "left"}
            )
            logger.info("Model loaded successfully")
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def generate_embeddings(self, items: List[Dict], content_field: str = "content") -> List[Dict]:
        """
        为JSON数据生成嵌入向量
        :param items: 包含文本的字典列表
        :param content_field: 包含文本内容的字段名
        :return: 添加了嵌入向量的字典列表
        """
        if not items:
            logger.warning("No items to process")
            return []
        
        results = []
        for item in tqdm(items, desc="Generating embeddings"):
            try:
                if content_field not in item:
                    logger.warning(f"Item missing '{content_field}' field: {item.get('name', 'unnamed')}")
                    continue
                
                text = item[content_field]
                embedding = self.model.encode(text).tolist()
                item["embedding"] = embedding
                results.append(item)
            except Exception as e:
                logger.error(f"Error processing item {item.get('name', 'unnamed')}: {e}")
        
        logger.info(f"Generated embeddings for {len(results)} items")
        return results
    
    def process_file(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        content_field: str = "content",
        overwrite: bool = False
    ) -> bool:
        """
        处理输入文件并保存带嵌入向量的结果
        :param input_path: 输入JSON文件路径
        :param output_path: 输出JSON文件路径 (None则自动生成)
        :param content_field: 包含文本内容的字段名
        :param overwrite: 是否覆盖已存在的输出文件
        :return: 是否成功
        """
        input_path = Path(input_path)
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return False
        
        # 设置默认输出路径
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_with_embeddings.json"
        output_path = Path(output_path)
        
        if output_path.exists() and not overwrite:
            logger.error(f"Output file already exists: {output_path}")
            return False
        
        try:
            # 读取输入文件
            logger.info(f"Reading input file: {input_path}")
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                logger.error("Input JSON should be a list of items")
                return False
            
            # 生成嵌入向量
            processed_data = self.generate_embeddings(data, content_field)
            
            # 保存结果
            logger.info(f"Saving results to: {output_path}")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
            logger.info("Processing completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return False


if __name__ == "__main__":
    # 配置参数
    MODEL_PATH = "E:/model/qwen3-embed-0.6B"
    INPUT_FILE = "E:/AIpro/T2Sql/carbon_metadata_kb.json"
    OUTPUT_FILE = "E:/AIpro/T2Sql/carbon_metadata_kb_with_Q3_embedding.json"
    
    # 创建实例并处理文件
    generator = EmbeddingGenerator(MODEL_PATH)
    success = generator.process_file(
        input_path=INPUT_FILE,
        output_path=OUTPUT_FILE,
        content_field="content",
        overwrite=True
    )
    
    if success:
        logger.info("Embedding generation completed successfully")
    else:
        logger.error("Embedding generation failed")