import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://192.168.8.101:8000/api/database',
  timeout: 10000,
});

export default {
  // 获取所有数据库列表
  listDatabases() {
    return apiClient.get('/databases');
  },

  // 获取指定数据库中的所有表
  listTables(database) {
    return apiClient.get(`/databases/${database}/tables`);
  },

  // 获取指定数据库中所有表的建表语句
  getAllSchemas(database) {
    return apiClient.get(`/databases/${database}/schema`);
  },

  // 生成指定数据库的 ER 图 JSON 数据
  generateERDiagram(database) {
    return apiClient.get(`/databases/${database}/er`);
  }
};