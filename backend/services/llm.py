# backend/services/llm.py

import requests
import json
import re
from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key

    def _safe_parse_json(self, raw_response: str) -> dict:
        after_to = re.split(r'^\s*<think>.*?</think>\s*', raw_response, flags=re.DOTALL | re.IGNORECASE)[-1].lstrip()
        # 步骤2: 移除 Markdown 中的 ```json 开头和 ``` 结尾
        cleaned = re.sub(r'^\s*```json\s*', '', after_to, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*```\s*$', '', cleaned, flags=re.DOTALL)

        # 步骤3: 尝试解析 JSON
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            print("尝试常规清洗失败，正在从 '{' 开始提取...")
            start_idx = cleaned.find('{')
            if start_idx == -1:
                raise ValueError("未找到 JSON 开始符 '{'")
            json_str = cleaned[start_idx:]
            end_idx = json_str.rfind('}') + 1
            if end_idx <= start_idx:
                raise ValueError("无法确定 JSON 结束位置")
            json_str = json_str[:end_idx]
            return json.loads(json_str)

    def generate_table_description(self, table_sql: str) -> dict:
        PROMPT_TEMPLATE = """
请根据以下建表语句，生成一个结构化的 JSON 描述，包含：
1. 表的基本信息（表名、中文名、描述、用途）
2. 关键字段说明（字段名、中文名、数据类型、描述、使用场景）
3. 常用统计指标（指标名、表达式、适用场景、描述）

要求：
- 输出格式必须严格为 JSON，不要包含其他内容
- 不需要思考过程
- 中文描述简洁清晰，避免冗余

示例输出：
{{
  "table_info": {{
    "table_name": "urgency_address",
    "chinese_name": "应急地址信息表",
    "description": "存储应急管理物资、消防设施、集合点等地址信息，包含地点类型、坐标、创建/更新信息。",
    "purpose": "用于应急资源调度、设施定位、灾情响应等场景。"
  }},
  "fields": [
    {{
      "field_name": "id",
      "chinese_name": "地址唯一标识",
      "data_type": "BIGINT",
      "description": "地址的主键，自增唯一标识",
      "usage": "用于关联地址与其他数据（如资源分配、事件记录）"
    }},
    {{
      "field_name": "address",
      "chinese_name": "地点信息",
      "data_type": "VARCHAR(255)",
      "description": "地址的具体描述（如“XX仓库”、“XX消防站”）",
      "usage": "用于模糊查询或精确匹配地址名称"
    }},
    {{
      "field_name": "type",
      "chinese_name": "地点类型",
      "data_type": "INT",
      "description": "地点类型标识：1（资源存储地点）、2（建筑地点）、3（设备点）",
      "usage": "常用于分类查询（如筛选所有资源存储地点）"
    }},
    {{
      "field_name": "lat",
      "chinese_name": "纬度/横坐标",
      "data_type": "DOUBLE(16,6)",
      "description": "地点的纬度或横坐标值（用于地图定位）",
      "usage": "与 `lng` 联合使用，计算地理距离或可视化地图"
    }},
    {{
      "field_name": "lng",
      "chinese_name": "经度/纵坐标",
      "data_type": "DOUBLE(16,6)",
      "description": "地点的经度或纵坐标值（用于地图定位）",
      "usage": "与 `lat` 联合使用，计算地理距离或可视化地图"
    }},
    {{
      "field_name": "del_flag",
      "chinese_name": "删除标记",
      "data_type": "CHAR(1)",
      "description": "标记是否删除：0（未删除）、1（已删除）",
      "usage": "查询时过滤有效数据（如 `WHERE del_flag = '0'`）"
    }}
  ],
  "metrics": [
    {{
      "metric_name": "地址总数",
      "expression": "COUNT(*)",
      "scenario": "数据总量统计",
      "description": "统计表中所有地址记录的数量"
    }},
    {{
      "metric_name": "有效地址数量",
      "expression": "COUNT(CASE WHEN del_flag = '0' THEN 1 END)",
      "scenario": "数据质量分析",
      "description": "统计未被删除的有效地址数量"
    }},
    {{
      "metric_name": "地点类型分布",
      "expression": "SELECT type, COUNT(*) AS count FROM urgency_address GROUP BY type",
      "scenario": "资源分布分析",
      "description": "按地点类型统计数量（如资源存储点、建筑点、设备点的占比）"
    }}
  ]
}}

建表语句：
{table_sql}
"""
        prompt = PROMPT_TEMPLATE.format(table_sql=json.dumps(table_sql, ensure_ascii=False))
        payload = {
            "inputs": {},
            "query": prompt,
            "response_mode": "blocking",
            "conversation_id": "",
            "user": "zhanke",
            "files": []
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=3000)
            response.raise_for_status()

            data = response.json()
            answer = data.get("answer")
            if not answer:
                raise ValueError("响应中未找到 'answer' 字段")

            return self._safe_parse_json(answer)

        except requests.exceptions.RequestException as e:
            logger.error(f"API 请求失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"LLM API 请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"解析响应失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"解析 LLM 响应失败: {str(e)}")
        

def generate_vector_items(metadata: dict) -> list:
    items = []
    # 提取嵌套的 metadata（兼容旧结构）
    actual_metadata = metadata.get('description', metadata)  # 关键修改
    table_info = actual_metadata.get("table_info", {})
    if table_info:
        table_text = (
            f"表名: {table_info['table_name']}; "
            f"中文名: {table_info['chinese_name']}; "
            f"描述: {table_info['description']}; "
            f"用途: {table_info['purpose']}"
        )
        items.append({
            "type": "table",
            "content": table_text,
            "metadata": {
                "name": table_info["table_name"],
                "chinese_name": table_info["chinese_name"]
            }
        })

    for field in actual_metadata.get("fields", []):
        field_text = (
            f"字段名: {field['field_name']}; "
            f"中文名: {field['chinese_name']}; "
            f"类型: {field['data_type']}; "
            f"描述: {field['description']}; "
            f"使用方式: {field['usage']}"
        )
        items.append({
            "type": "column",
            "content": field_text,
            "metadata": {
                "name": field['field_name'],
                "chinese_name": field['chinese_name'],
                "table": table_info.get("table_name", "")
            }
        })

    for metric in actual_metadata.get("metrics", []):
        metric_text = (
            f"指标名: {metric['metric_name']}; "
            f"表达式: {metric['expression']}; "
            f"适用场景: {metric['scenario']}; "
            f"说明: {metric['description']}"
        )
        items.append({
            "type": "metric",
            "content": metric_text,
            "metadata": {
                "name": metric['metric_name'],
                "expression": metric['expression']
            }
        })

    return items