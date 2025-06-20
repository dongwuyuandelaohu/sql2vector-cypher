<template>
  <el-card class="search-view">
    <div slot="header" class="clearfix">
      <span>在集合 {{ collection }} 中检索向量</span>
      <el-button 
        class="float-right" 
        size="small" 
        @click="goBack"
      >
        返回
      </el-button>
    </div>

    <el-form :model="searchForm" label-position="top">
      <el-form-item label="查询文本">
        <el-input 
          v-model="searchForm.query" 
          placeholder="请输入查询文本"
        />
      </el-form-item>
      
      <el-form-item label="返回结果数量">
        <el-input-number 
          v-model="searchForm.top_k" 
          :min="1" 
          :max="100"
        />
      </el-form-item>

      <!-- <el-button 
        type="primary" 
        @click="handleSearch"
        :loading="loading"
      >
        检索
      </el-button> -->
      <el-button-group>
        <el-button 
          type="primary" 
          @click="handleSearch"
          :loading="loading.search"
        >
          元数据检索
        </el-button>
        <el-button 
          type="success" 
          @click="handleQASearch"
          :loading="loading.qaSearch"
        >
          QA检索
        </el-button>
      </el-button-group>
    </el-form>

    <el-divider />

    <!-- 动态表格 -->
    <el-table 
      :data="currentResults" 
      border 
      style="width: 100%"
      v-loading="loading.search || loading.qaSearch"
      v-show="currentResults.length > 0"
    >
      <!-- 元数据检索列 -->
      <template v-if="currentSearchType === 'metadata'">
        <el-table-column prop="name" label="名称" width="200">
          <template slot-scope="scope">
            <pre>{{ scope.row.name }}</pre>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="150">
          <template slot-scope="scope">
            <pre>{{ scope.row.type }}</pre>
          </template>
        </el-table-column>
        <el-table-column prop="distance" label="相似度得分" width="150">
          <template slot-scope="scope">
            {{ (scope.row.distance || 0).toFixed(4) }}
          </template>
        </el-table-column>
        <el-table-column label="描述">
          <template slot-scope="scope">
            <pre>{{ scope.row.description }}</pre>
          </template>
        </el-table-column>
      </template>

      <!-- QA检索列 -->
      <template v-else-if="currentSearchType === 'qa'">
        <el-table-column prop="question" label="问题" width="300">
          <template slot-scope="scope">
            <pre>{{ scope.row.question }}</pre>
          </template>
        </el-table-column>
        <el-table-column prop="answer" label="答案">
          <template slot-scope="scope">
            <pre>{{ scope.row.answer }}</pre>
          </template>
        </el-table-column>
        <el-table-column prop="distance" label="相似度得分" width="150">
          <template slot-scope="scope">
            {{ (scope.row.distance || 0).toFixed(4) }}
          </template>
        </el-table-column>
      </template>
    </el-table>
  </el-card>
</template>

<script>
import vectorAPI from '@/api/vector'
export default {
  name: 'VectorSearch',
  data() {
    return {
      searchForm: {
        query: '',
        top_k: 5
      },
      metadataResults: [], // 存储元数据检索结果
      qaResults: [],       // 存储QA检索结果
      loading: {
        search: false,
        qaSearch: false
    },
    currentSearchType: ''
    }
  },
  computed: {
    collection() {
      return this.$route.params.collection
    },
    currentResults() {
      // 根据当前搜索类型返回对应结果
      return this.currentSearchType === 'metadata' 
        ? this.metadataResults 
        : this.currentSearchType === 'qa'
          ? this.qaResults
          : []
    }
  },
  methods: {
    goBack() {
      this.$router.push({ name: 'VectorDB' })
    },
    handleSearch() {
      if (!this.searchForm.query.trim()) {
        this.$notify({
          title: '提示',
          message: '请输入查询文本',
          type: 'warning'
        });
        return;
      }

      this.loading.search = true;
      this.currentSearchType = 'metadata';
      vectorAPI.searchVector(
        this.searchForm.query,
        [this.collection],
        this.searchForm.top_k
      )
      .then(res => {
        this.metadataResults = res.data.results[this.collection] || [];
      })
      .catch(error => {
        this.$notify.error({
          title: '错误',
          message: '检索失败: ' + (error.response?.data?.message || error.message)
        });
      })
      .finally(() => {
        this.loading.search = false;
      });
    },
    handleQASearch() {
      if (!this.searchForm.query.trim()) {
        this.$notify({
          title: '提示',
          message: '请输入查询文本',
          type: 'warning'
        });
        return;
      }

      this.loading.qaSearch = true;
      this.currentSearchType = 'qa';
      // this.isQASearch = true;

      vectorAPI.searchQAVector(
        this.searchForm.query,
        [this.collection],
        this.searchForm.top_k
      )
      .then(res => {
        this.qaResults  = res.data.results[this.collection] || [];
      })
      .catch(error => {
        this.$notify.error({
          title: '错误',
          message: 'QA检索失败: ' + (error.response?.data?.message || error.message)
        });
      })
      .finally(() => {
        this.loading.qaSearch = false;
      });
    }
  }
}
</script>

<style scoped>
.search-view {
  margin-top: 20px;
}

.float-right {
  float: right;
}

.clearfix::after {
  content: "";
  display: table;
  clear: both;
}

pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>