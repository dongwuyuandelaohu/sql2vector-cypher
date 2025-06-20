<template>
  <div class="graph-view">
    <h2>SQL 转图数据库</h2>

    <!-- SQL 文件上传与转换 -->
    <el-card class="mb-4">
      <h3>1. 输入或上传 SQL 内容</h3>
      
      <!-- 文本输入框 -->
      <el-input
        v-model="inputSqlContent"
        type="textarea"
        :rows="6"
        placeholder="请输入 SQL 内容"
        style="width: 100%; margin-bottom: 16px;"
      />

      <!-- 文件上传 -->
      <el-upload
        drag
        action="#"
        :on-change="handleFileChange"
        :auto-upload="false"
      >
        <i class="el-icon-upload"></i>
        <div class="el-upload__text">将 SQL 文件拖到此处，或 <em>点击上传</em></div>
      </el-upload>

      <el-button 
        @click="convertToGraph" 
        type="primary" 
        :disabled="!hasValidSqlContent"
        style="margin-top: 16px;"
      >
        转换为 Cypher
      </el-button>
    </el-card>

    <!-- Cypher 脚本展示 -->
    <el-card v-if="cypherResult" class="mb-4">
      <h3>2. 生成的 Cypher 脚本</h3>
      <pre class="json-output">{{ cypherResult }}</pre>
      <el-button 
        @click="saveCypherToFile" 
        type="success" 
        :disabled="!cypherResult"
        style="margin-right: 16px;"
      >
        保存为文件
      </el-button>
      <el-button 
        @click="insertCypherToGraph" 
        type="success" 
        :disabled="!cypherResult"
      >
        插入到图数据库
      </el-button>
    </el-card>

    <!-- 查询图数据库 -->
    <el-card class="mb-4">
      <h3>3. 查询图数据库</h3>
      <el-input
        v-model="queryInput"
        placeholder="输入表名或字段名进行查询"
        style="width: 300px; margin-right: 16px;"
      />
      <el-button @click="queryGraphData">查询</el-button>
      <el-button @click="clearGraphData" type="danger" style="margin-left: 16px;">清空图数据库</el-button>

      <el-card v-if="queryResult" class="mt-4">
        <h4>查询结果</h4>
        <pre class="json-output">{{ queryResult }}</pre>
      </el-card>
    </el-card>
  </div>
</template>
<script>
import graphApi from '@/api/graph';

export default {
  data() {
    return {
      inputSqlContent: '',  // 新增：用户输入的 SQL 内容
      sqlContent: '',       // 上传的 SQL 文件内容（保持原字段）
      cypherResult: '',
      queryInput: '',
      queryResult: ''
    };
  },
  computed: {
    // 判断是否有有效 SQL 内容（优先使用输入框内容）
    hasValidSqlContent() {
      return this.inputSqlContent.trim() || this.sqlContent.trim();
    }
  },
  methods: {
    handleFileChange(file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        this.sqlContent = e.target.result;
      };
      reader.readAsText(file.raw);
    },
    async convertToGraph() {
      try {
        // 优先使用 inputSqlContent，否则使用上传的 sqlContent
        const sqlContent = this.inputSqlContent || this.sqlContent;
        const response = await graphApi.sqlToCypher(sqlContent);
        this.cypherResult = response.data.cypher;
        this.$message.success('SQL 转 Cypher 成功');
      } catch (error) {
        console.error('转换失败:', error);
        this.$message.error('转换失败，请检查文件内容');
      }
    },
    async saveCypherToFile() {
      if (!this.cypherResult) return;

      const blob = new Blob([this.cypherResult], { type: 'text/plain' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'generated_cypher.cypher';  // 保存的文件名
      link.click();
      URL.revokeObjectURL(link.href); // 释放内存
    },
    async insertCypherToGraph() {
      if (!this.cypherResult) return;

      try {
        await graphApi.insertCypher(this.cypherResult);
        this.$message.success('Cypher 插入成功');
      } catch (error) {
        console.error('插入失败:', error);
        this.$message.error('插入失败，请重试');
      }
    },
    async queryGraphData() {
      if (!this.queryInput) return;

      try {
        const response = await graphApi.queryGraph(this.queryInput);
        this.queryResult = JSON.stringify(response.data, null, 2);
        this.$message.success('查询成功');
      } catch (error) {
        console.error('查询失败:', error);
        this.$message.error('查询失败，请检查输入');
      }
    },
    async clearGraphData() {
      try {
        await this.$confirm('此操作将清空图数据库，是否继续？', '警告', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        });

        await graphApi.clearGraph(true);
        this.$message.success('图数据库已清空');
        this.queryResult = '';
      } catch (error) {
        console.error('清空失败:', error);
        this.$message.error('清空失败，请重试');
      }
    }
  }
};
</script>

<style scoped>
.mb-4 {
  margin-bottom: 24px;
}
.mt-4 {
  margin-top: 16px;
}
.json-output {
  background-color: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Courier New', monospace;
  line-height: 1.5;
  tab-size: 2;
  text-align: left !important;
}
</style>