<template>
  <div class="database-view">
    <h2>数据库管理</h2>

    <!-- 数据库选择 -->
    <el-card class="mb-4">
      <h3>选择数据库</h3>
      <el-select v-model="selectedDatabase" placeholder="请选择数据库" @change="loadTables">
        <el-option
          v-for="db in databases"
          :key="db"
          :label="db"
          :value="db"
        />
      </el-select>
    </el-card>

    <!-- 表结构展示 -->
    <el-card v-if="selectedDatabase" class="mb-4">
      <h3>表结构</h3>
      <el-table :data="tables" border style="width: 100%">
        <el-table-column prop="table_name" label="表名" width="200" />
        <el-table-column prop="schema_sql" label="建表语句" />
      </el-table>
    </el-card>

    <!-- ER 图生成 -->
    <el-card v-if="selectedDatabase">
      <h3>ER 图生成</h3>
      <el-button type="primary" @click="generateERDiagram">生成 ER 图 JSON</el-button>
      <pre v-if="erDiagramJson" class="json-output">{{ erDiagramJson }}</pre>
    </el-card>
  </div>
</template>

<script>
import dbApi from '@/api/database';

export default {
  data() {
    return {
      databases: [],           // 所有数据库列表
      selectedDatabase: '',     // 当前选中的数据库
      tables: [],               // 表结构列表
      erDiagramJson: null       // ER 图 JSON 数据
    };
  },
  mounted() {
    this.loadDatabases();
  },
  methods: {
    async loadDatabases() {
      try {
        const res = await dbApi.listDatabases();
        this.databases = res.data;
      } catch (error) {
        console.error('获取数据库列表失败:', error);
        this.$message.error('获取数据库列表失败');
      }
    },
    async loadTables() {
      if (!this.selectedDatabase) return;

      try {
        const res = await dbApi.getAllSchemas(this.selectedDatabase);

        // 确保 res.data 是对象且不为空
        if (typeof res.data !== 'object' || res.data === null) {
          console.error('接口返回数据格式异常:', res.data);
          this.$message.error('接口返回数据格式异常');
          return;
        }

        // 将对象转换为数组
        const tableArray = Object.entries(res.data).map(([tableName, schemaSql]) => ({
          table_name: tableName,
          schema_sql: schemaSql
        }));

        this.tables = tableArray;
      } catch (error) {
        console.error('获取表结构失败:', error);
        this.$message.error('获取表结构失败');
      }
    },
    async generateERDiagram() {
      if (!this.selectedDatabase) return;

      try {
        const res = await dbApi.generateERDiagram(this.selectedDatabase);
        this.erDiagramJson = JSON.stringify(res.data, null, 2);
      } catch (error) {
        console.error('生成 ER 图失败:', error);
        this.$message.error('生成 ER 图失败');
      }
    }
  }
};
</script>

<style scoped>
.mb-4 {
  margin-bottom: 24px;
}

.json-output {
  background-color: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  white-space: pre-wrap; /* 保留换行和空格，自动换行 */
  word-break: break-word; /* 长单词/长URL强制换行 */
  font-family: 'Courier New', monospace; /* 等宽字体，对齐整齐 */
  line-height: 1.5; /* 行高更清晰 */
  tab-size: 2; /* 缩进显示为2个空格 */
  text-align: left; /* 强制左对齐 */
}
</style>