// src/api/graph.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://192.168.8.101:8000/api/graph',
  timeout: 10000,
});

export default {
  // SQL 转 Cypher
  sqlToCypher(content) {
    return apiClient.post('/sql-to-cypher', { content });
  },

  // 插入 Cypher 内容
  insertCypher(cypherContent) {
    return apiClient.post('/insert', { cypher_content: cypherContent });
  },

  // 查询图数据库
  queryGraph(inputString, limit = 100, returnData = true) {
    return apiClient.post('/query', {
      input_string: inputString,
      limit,
      return_data: returnData
    });
  },

  // 清空图数据库
  clearGraph(confirm = true) {
    return apiClient.post('/clear', { confirm });
  }
}