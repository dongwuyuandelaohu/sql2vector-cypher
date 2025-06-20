<template>
  <div class="database-manager">
    <!-- 数据库连接设置 -->
    <el-card class="connection-form">
      <h3>数据库连接设置</h3>
      <el-form class="elForm" size="small">
        <el-form-item label="用户名：">
          <el-input v-model="dbConfig.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码：">
          <el-input v-model="dbConfig.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="IP地址：">
          <el-input v-model="dbConfig.host" placeholder="请输入IP地址" />
        </el-form-item>
        <el-form-item label="端口：">
          <el-input v-model="dbConfig.port" placeholder="请输入端口号" />
        </el-form-item>
        <el-form-item style="width: 100%;">
          <div class="footer">
            <el-button type="primary" @click="connectDatabase">连接</el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 第一列：数据库和表选择 -->
      <div class="content-column" v-if="databases.length > 0">
        <el-card class="database-section">
          <h3>知识库</h3>
          <div class="header">
            <div class="name">数据库：</div>
            <el-select v-model="selectedDatabase" placeholder="请选择数据库" size="small" @change="loadTables" class="elSelect">
              <el-option v-for="db in databases" :key="db" :label="db" :value="db" />
            </el-select>
            <el-button v-if="selectedDatabase" type="success" size="small" :loading="knowledgeLoading" @click="generateAndSaveKnowledgeBase">生成知识库并保存</el-button>
          </div>
          <el-table :data="tables" border style="width: 100%">
            <el-table-column prop="name" width="150" label="表名列表"></el-table-column>
            <el-table-column prop="sql" label="建表语句"></el-table-column>
            <el-table-column prop="des" label="LLM描述">
              <template slot-scope="scope">
                <div class="desBox">{{ scope.row.des }}</div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template slot-scope="scope">
                <el-button  type="primary" size="small" :loading="scope.row.status" @click="generateTableDescription(scope.row)">生成LLM描述</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
      <div class="content-column" v-if="databases.length > 0">
        <el-card class="result-section">
          <h3>向量库</h3>
          <div class="header">
            <div class="name">生成向量库:</div>
            <el-upload action="" :auto-upload="false" :on-change="handleFileUpload" :show-file-list="false">
              <el-button type="primary" size="small">上传知识库文件</el-button>
            </el-upload>
            <el-button type="success" size="small" @click="saveAsText(tableDescriptionResult, 'table-description.txt')" style="margin-left: 10px;">下载向量库文件</el-button>
          </div>
          <div class="title">生成结果</div>
          <pre class="json-output">{{ tableDescriptionResult }}</pre>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script>
import llmApi from '@/api/llm' 
import databaseApi from '@/api/database'
export default {
  data() {
    return {
      dbConfig: {
        username: '',
        password: '',
        host: '',
        port: ''
      },
      databases: [],
      selectedDatabase: '',
      tables: [],
      tableDescriptionResult: '',
      knowledgeLoading: false,
    }
  },
  methods: {
    async connectDatabase() {
      if (!this.dbConfig.username || !this.dbConfig.host || !this.dbConfig.port) {
        this.$message.warning('请填写完整连接信息')
        return
      }
      try {
        const res = await databaseApi.listDatabases() // 假设你用了 axios
        this.databases = res.data
        this.$message.success('连接成功')
      } catch (e) {
        this.$message.error('连接失败，请检查配置')
      }
    },
    async loadTables() {
      if (!this.selectedDatabase) return
        
      try {
        const [response1, response2] = await Promise.all([
          databaseApi.listTables(this.selectedDatabase),
          databaseApi.getAllSchemas(this.selectedDatabase)
        ]);
        this.tables = response1.data.map(item => {
          return {
            name: item,
            sql: response2.data[item] ? response2.data[item] : '',
            des: '',
            status: false
          }
        });
      } catch (e) {
        this.$message.error('获取表列表失败')
      }
    },
    async generateTableDescription(row) {
      try {
        row.status = true;
        const res = await llmApi.generateTableDescriptions({
          database: this.selectedDatabase,
          tables: [row.name]
        })
        this.tables = this.tables.map(item => {
          if (item.name == row.name) {
            return {
              ...item,
              des: JSON.stringify(res.data, null, 2)
            }
          } else {
            return item
          }
        });
        row.status = false;
        this.$message.success('表描述生成成功')
      } catch (e) {
        row.status = false;
        this.$message.error('生成表描述失败')
      }
    },
    async generateAndSaveKnowledgeBase() {
      try {
        this.knowledgeLoading = true;
        const res = await llmApi.generateTableDescriptions({
          database: this.selectedDatabase,
        })
        this.knowledgeLoading = false;
        this.saveAsJSON(res.data, 'knowledge-base-alltable.json')
        this.$message.success('知识库已保存')
      } catch (e) {
        this.knowledgeLoading = false;
        this.$message.error('生成知识库失败')
      }
    },
    async handleFileUpload(file) {
      try {
        const reader = new FileReader()
        reader.onload = async (e) => {
          const content = e.target.result
          try {
            const res = await llmApi.formatVectorItems(JSON.parse(content));
            this.tableDescriptionResult = JSON.stringify(res.data, null, 2)
            this.$message.success('向量库生成成功')
          } catch (e) {
            this.$message.error('处理文件内容失败')
          }
        }
        reader.readAsText(file.raw)
      } catch (e) {
        this.$message.error('文件读取失败')
      }
    },
    saveAsJSON(data, filename) {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = filename
      link.click()
    },
    saveAsText(data, filename) {
      const blob = new Blob([data], { type: 'text/plain;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = filename
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click()
      setTimeout(() => {
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
      }, 100);
    }
  }
}
</script>
<style lang="scss" scoped>
.database-manager {
  padding: 0 20px;
  .connection-form {
    width: 80%;
    margin: 0 auto;
    h3 {
      margin: 0;
      margin-bottom: 10px;
    }
    .elForm {
      display: flex;
        flex-wrap: wrap;
      ::v-deep .el-form-item {
        display: flex;
        width: 50%;
        .el-form-item__label {
          width: 100px;
          text-align: right;
          padding-right: 20px;
        }
        .el-form-item__content {
          flex: 1;
        }
      }
      .footer{
        text-align: center;
      }
    }
  }
  .main-content {
    margin-top: 20px;
    .content-column {
      width: 80%;
      margin: 0 auto;
      margin-top: 10px;
      h3 {
        margin: 0;
      }
      .header {
        display: flex;
        align-items: center;
        text-align: left;
        margin-bottom: 20px;
        .name {
          margin: 0;
          text-align: left;
          margin-right: 10px;
        }
        .elSelect{
          width: 200px;
          margin-right: 10px;
        }
      }
      .desBox {
        max-height: 400px;
        overflow: auto;
      }
      .title {
        text-align: left;
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
        text-align: left;
        min-height: 50px;
        max-height: 800px;
        overflow: auto;
      }
    }
  }
}
</style>