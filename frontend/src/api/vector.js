// src/api/vector.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://192.168.8.101:8000/api/vector',
  timeout: 10000*200,
});

export default {
  generateEmbedding(text) {
    return apiClient.post('/generate-embedding', { text });
  },
  searchVector(vquery, collections, top_k) {
    return apiClient.post('/search', {
      vquery,
      collections,
      top_k
    });
  },
  searchQAVector(vquery, collections, top_k) {
    return apiClient.post('/search-qa', {
      vquery,
      collections,
      top_k
    });
  },
  listCollections() {
    return apiClient.get('/collections');
  },
  createCollection(collection_name) {
    return apiClient.post('/create-collection', { collection_name });
  },
  createQACollection(collection_name) {
    return apiClient.post('/create-qa-collection', { collection_name });
  },
  clearCollection(collection_name) {
    return apiClient.post('/clear-collection', {
      collection_name,
      confirm: true
    });
  },
  insertData(collection_name, data) {
    return apiClient.post('/insert-data', {
      collection_name,
      data
    });
  },
  insertQaCsv(collection_name, formData) {
    return apiClient.post(`/insert-qa-csv?collection_name=${encodeURIComponent(collection_name)}`, 
      formData, 
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );
  },
  createIndex(collection_name) {
    return apiClient.post('/create-index', {}, {
      params: { collection_name }
    });
  }
};