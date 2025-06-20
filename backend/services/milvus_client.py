# milvus_client.py

from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

class MilvusClient:
    def __init__(self, host="localhost", port="19530"):
        self.host = host
        self.port = port
        self.connected = False
        self.collections = {}

    def connect(self):
        """连接到 Milvus"""
        try:
            connections.connect(host=self.host, port=self.port)
            self.connected = True
            logger.info("成功连接到 Milvus")
        except Exception as e:
            logger.error(f"连接 Milvus 失败: {e}")
            raise

    def create_collection(self, collection_name, dim=768):
        """创建默认结构的集合"""
        if not self.connected:
            self.connect()

        if utility.has_collection(collection_name):
            logger.warning(f"集合 {collection_name} 已存在，跳过创建")
            return

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="type", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
        ]
        schema = CollectionSchema(fields, "数据库元数据知识库")
        collection = Collection(collection_name, schema)
        # collection.load()
        logger.info(f"集合 {collection_name} 创建完成")
        return collection
    
    def create_qa_collection(self, collection_name, dim=768):
        """创建默认结构的集合"""
        if not self.connected:
            self.connect()

        if utility.has_collection(collection_name):
            logger.warning(f"集合 {collection_name} 已存在，跳过创建")
            return

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="question", dtype=DataType.VARCHAR, max_length=2048),
            FieldSchema(name="answer", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768)
        ]
        schema = CollectionSchema(fields, "业务知识库")
        collection = Collection(collection_name, schema)
        # collection.load()
        logger.info(f"集合 {collection_name} 创建完成")
        return collection

    def load_collection(self, collection_name):
        """加载集合"""
        if not self.connected:
            self.connect()
        try:
            collection = Collection(collection_name)
            collection.load()
            self.collections[collection_name] = collection
            logger.info(f"集合 {collection_name} 已加载")
            return collection
        except Exception as e:
            logger.error(f"加载集合失败: {e}")
            raise

    def clear_collection_data(self, collection_name):
        """清空集合数据与索引，安全处理无索引、无数据情况"""
        try:
            # 只获取集合引用，不 load
            collection = Collection(collection_name)

            # # 如果集合为空，跳过 delete
            # if collection.num_entities > 0:
            #     expr = "id > 0"
            #     collection.delete(expr)
            #     collection.flush()

            # # 释放内存（可选）
            # try:
            #     collection.release()
            # except Exception as e:
            #     print("release 失败，可能是未 load", e)

            # # 删除索引（如果有）
            # if len(collection.indexes) > 0:
            #     collection.drop_index()
            #     print(f"集合 {collection_name} 索引已删除")

            # 删除集合
            collection.drop()
            print(f"集合 {collection_name} 已被完全清除")

        except Exception as e:
            logger.error(f"清空集合数据失败: {e}")
            raise

    def get_collection(self, collection_name):
        """获取集合对象"""
        if collection_name in self.collections:
            return self.collections[collection_name]
        return self.load_collection(collection_name)

    def insert_and_create_index(self, collection_name, data):
        """
        插入数据并创建索引
        :param collection_name: 集合名称
        :param data: 要插入的数据，格式如：
            [
                {
                    "type": "table",
                    "name": "user",
                    "description": "用户信息表",
                    "embedding": [0.1, 0.2, ..., 0.768]
                },
                ...
            ]
        """
        # Step 1: 获取集合引用（不 load）
        if not utility.has_collection(collection_name):
            raise ValueError(f"集合 {collection_name} 不存在")

        collection = Collection(collection_name)

        # Step 2: 准备数据
        types = []
        names = []
        descriptions = []
        embeddings = []

        for item in data:
            if "type" not in item or "metadata" not in item:
                logger.warning(f"跳过无效项: {item}")
                continue
            if "name" not in item["metadata"] or "content" not in item or "embedding" not in item:
                logger.warning(f"跳过无效项: {item}")
                continue
            if not isinstance(item["embedding"], list) or len(item["embedding"]) != 768:
                logger.warning(f"跳过无效嵌入向量: {item['embedding']}")
                continue

            types.append(item["type"])
            names.append(item["metadata"]["name"])
            descriptions.append(item["content"])
            embeddings.append(item["embedding"])

        if not types:
            logger.warning("没有有效数据可供插入")
            return

        # Step 3: 插入数据
        collection.insert([
            types,
            names,
            descriptions,
            embeddings
        ])
        collection.flush()
        logger.info(f"已插入 {len(types)} 条数据到集合 {collection_name}")

        # Step 4: 创建索引
        index_params = {
            "index_type": "IVF_FLAT",
            "params": {"nlist": 100},
            "metric_type": "L2"
        }

        try:
            collection.create_index(field_name="embedding", index_params=index_params)
            utility.wait_for_index_building_complete(collection_name)
            logger.info(f"集合 {collection_name} 索引创建完成")
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            raise

    def insert_qa_and_create_index(self, collection_name, qa_data):
        """
        插入QA数据并创建索引
        :param collection_name: 集合名称
        :param qa_data: QA数据列表，格式如：
            [
                {
                    "question": "问题文本",
                    "answer": "答案文本",
                    "embedding": [0.1, 0.2, ..., 0.768]  # 基于问题生成的嵌入向量
                },
                ...
            ]
        """
        # Step 1: 获取集合引用（不 load）
        if not utility.has_collection(collection_name):
            raise ValueError(f"集合 {collection_name} 不存在")

        collection = Collection(collection_name)

        # Step 2: 准备数据
        questions = []
        answers = []
        embeddings = []

        for item in qa_data:
            if not all(key in item for key in ["question", "answer", "embedding"]):
                logger.warning(f"跳过无效QA项，缺少必要字段: {item}")
                continue

            if not isinstance(item["embedding"], list) or len(item["embedding"]) != 768:
                logger.warning(f"跳过无效嵌入向量: {item['embedding']}")
                continue

            questions.append(item["question"])
            answers.append(item["answer"])
            embeddings.append(item["embedding"])

        if not questions:
            logger.warning("没有有效的QA数据可供插入")
            return

        # Step 3: 插入数据
        collection.insert([
            questions,
            answers,
            embeddings
        ])
        collection.flush()
        logger.info(f"已插入 {len(questions)} 条QA数据到集合 {collection_name}")

        # Step 4: 创建索引
        index_params = {
            "index_type": "IVF_FLAT",
            "params": {"nlist": 100},
            "metric_type": "L2"
        }

        try:
            collection.create_index(field_name="embedding", index_params=index_params)
            utility.wait_for_index_building_complete(collection_name)
            logger.info(f"集合 {collection_name} QA索引创建完成")
        except Exception as e:
            logger.error(f"创建QA索引失败: {e}")
            raise


    def search(self, collection_name, query_embedding, top_k=5):
        """在指定集合中搜索相似向量"""
        collection = self.get_collection(collection_name)
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "L2", "nprobe": 10},
            limit=top_k,
            output_fields=["type", "description", "name"]
        )
        matched_results = []
        for hits in results:
            for hit in hits:
                matched_results.append({
                    "distance": hit.distance,
                    "name": hit.entity.get('name'),
                    "type": hit.entity.get('type'),
                    "description": hit.entity.get('description')
                })
        return matched_results

    def search_qa(self, collection_name, query_embedding, top_k=5):
        """在QA集合中搜索相似问题"""
        collection = self.get_collection(collection_name)
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "L2", "nprobe": 10},
            limit=top_k,
            output_fields=["question", "answer"]  # 只返回问题和答案字段
        )
        
        matched_results = []
        for hits in results:
            for hit in hits:
                matched_results.append({
                    "distance": hit.distance,
                    "question": hit.entity.get('question'),
                    "answer": hit.entity.get('answer')
                })
        return matched_results

    def list_collections(self):
        """列出所有集合名称"""
        return utility.list_collections()

    def create_index(self, collection_name):
        """为集合创建索引"""
        collection = self.get_collection(collection_name)
        index_params = {
            "index_type": "IVF_FLAT",
            "params": {"nlist": 100},
            "metric_type": "L2"
        }
        try:
            collection.create_index(field_name="embedding", index_params=index_params)
            utility.wait_for_index_building_complete(collection_name)
            logger.info(f"集合 {collection_name} 索引创建完成")
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            raise