import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://192.168.8.101:8000/api/llm',
  timeout: 1000*30000,
});

export default {
  // 生成表描述接口
  generateTableDescriptions(query) {
    return apiClient.get(`/database/${query.database}`, {
      params: query
    });
  },

  // 格式化向量项接口
  formatVectorItems(metadata) {
    return apiClient.post('/format-vector-items', {
      metadata
    });
  }
};