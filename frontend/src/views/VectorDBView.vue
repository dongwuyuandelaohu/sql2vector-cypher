<template>
  <div class="vector-db-view">
    <h2 class="page-title">向量数据库管理</h2>

    <!-- 主集合列表卡片 -->
    <el-card class="main-card">
      <div slot="header" class="card-header">
        <span class="card-title">集合列表</span>
        <div class="card-actions">
          <el-button-group>
            <el-button 
              type="primary" 
              size="small"
              @click="fetchCollections"
              :loading="loading.collections"
              icon="el-icon-refresh"
            >
              刷新
            </el-button>
            <el-button 
              type="success" 
              size="small"
              @click="showCreateDialog = true"
              icon="el-icon-plus"
            >
              新增集合
            </el-button>
          </el-button-group>
        </div>
      </div>

      <el-table 
        :data="collections" 
        border 
        style="width: 100%"
        v-loading="loading.collections"
        class="collection-table"
      >
        <el-table-column 
          prop="name" 
          label="集合名称" 
          min-width="300"
          align="left"
          header-align="left"
        >
          <template #default="{row}">
            <span class="collection-name">{{ row.name }}</span>
          </template>
        </el-table-column>
        
        <el-table-column 
          label="操作" 
          width="400"
          align="left"
          header-align="left"
        >
          <template #default="{row}">
            <div class="action-buttons">
              <el-button 
                size="mini" 
                @click="goToInsertPage(row.name)"
                icon="el-icon-upload"
                class="action-btn"
              >
                插入数据
              </el-button>
              <el-button 
                size="mini" 
                type="primary" 
                @click="goToSearchPage(row.name)"
                icon="el-icon-search"
                class="action-btn"
              >
                检索
              </el-button>
              <el-button 
                size="mini" 
                type="danger" 
                @click="handleClearCollection(row.name)"
                :loading="loading.clear === row.name"
                icon="el-icon-delete"
                class="action-btn"
              >
                清空
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建集合对话框 -->
    <el-dialog 
      title="新建集合" 
      :visible.sync="showCreateDialog"
      width="500px"
      class="create-dialog"
    >
      <el-form 
        :model="createForm" 
        label-position="top"
        :rules="rules"
        ref="createForm"
      >
        <el-form-item label="集合名称" prop="name">
          <el-input 
            v-model="createForm.name" 
            placeholder="请输入集合名称"
            size="medium"
          ></el-input>
        </el-form-item>
        <el-form-item label="集合类型" prop="type">
          <el-select 
            v-model="createForm.type" 
            style="width: 100%"
            placeholder="请选择集合类型"
            size="medium"
          >
            <el-option 
              label="基础元数据类型" 
              value="create-collection"
            ></el-option>
            <el-option 
              label="QA业务库类型" 
              value="create-qa-collection"
            ></el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="showCreateDialog = false" size="medium">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleCreateCollection"
          :loading="loading.create"
          size="medium"
        >
          确认创建
        </el-button>
      </span>
    </el-dialog>

    <!-- 插入数据对话框 -->
    <el-dialog 
      title="插入数据" 
      :visible.sync="showInsertDialog"
      width="600px"
      class="insert-dialog"
    >
      <el-form 
        :model="insertForm" 
        label-position="top"
        ref="insertForm"
      >
        <el-form-item label="集合名称">
          <el-input 
            v-model="insertForm.collectionName" 
            disabled
          ></el-input>
        </el-form-item>
        <el-form-item label="选择文件">
          <el-upload
            action=""
            :on-change="handleChange"
            :file-list="insertForm.files"
            :auto-upload="false"
            :before-remove="beforeRemove"
            multiple
          >
            <el-button slot="trigger" size="small" type="primary">选取文件</el-button>
            <el-button 
              style="margin-top: 10px;" 
              size="small" 
              type="primary" 
              @click="submitUpload"
              :loading="loading.upload"
            >
              <i class="el-icon-upload"></i> 插入元数据
            </el-button>
            <el-button 
              style="margin-top: 10px; margin-left: 10px;" 
              size="small" 
              type="success" 
              @click="submitQaUpload"
              :loading="loading.qaUpload"
            >
              <i class="el-icon-document"></i> 插入QA数据
            </el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="showInsertDialog = false" size="medium">关闭</el-button>
      </span>
    </el-dialog>

    <router-view></router-view>
  </div>
</template>

<script>
import vectorAPI from '@/api/vector';

export default {
  name: 'VectorDBView',
  data() {
    return {
      collections: [],
      showCreateDialog: false,
      createForm: {
        name: '',
        type: 'create-collection'
      },
      loading: {
        collections: false,
        create: false,
        clear: null,
        upload: false,
        qaUpload: false
      },
      rules: {
        name: [
          { required: true, message: '请输入集合名称', trigger: 'blur' },
          { min: 3, max: 50, message: '长度在 3 到 50 个字符', trigger: 'blur' }
        ]
      },
      showInsertDialog: false,
      insertForm: {
        collectionName: '',
        files: []
      }
    };
  },
  methods: {
    goToInsertPage(collectionName) {
      this.insertForm.collectionName = collectionName;
      this.insertForm.files = [];
      this.showInsertDialog = true;
    },

    goToSearchPage(collectionName) {
      this.$router.push({ name: 'VectorSearch', params: { collection: collectionName } });
    },

    async fetchCollections() {
      this.loading.collections = true;
      try {
        const res = await vectorAPI.listCollections();
        this.collections = res.data.collections.map(name => ({ name }));
      } catch (error) {
        this.$notify.error({
          title: '错误',
          message: '获取集合列表失败: ' + (error.response?.data?.message || error.message)
        });
      } finally {
        this.loading.collections = false;
      }
    },

    async handleCreateCollection() {
      this.$refs.createForm.validate(async (valid) => {
        if (!valid) return;

        this.loading.create = true;
        try {
          if (this.createForm.type === 'create-collection') {
            await vectorAPI.createCollection(this.createForm.name);
          } else {
            await vectorAPI.createQACollection(this.createForm.name);
          }
          this.$notify.success({
            title: '成功',
            message: `集合 ${this.createForm.name} 创建成功`
          });
          this.showCreateDialog = false;
          this.fetchCollections();
        } catch (error) {
          this.$notify.error({
            title: '错误',
            message: '创建集合失败: ' + (error.response?.data?.message || error.message)
          });
        } finally {
          this.loading.create = false;
        }
      });
    },

    async handleClearCollection(collectionName) {
      this.$confirm(`确定要清空集合 "${collectionName}" 吗?`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        this.$set(this.loading, 'clear', collectionName);
        try {
          await vectorAPI.clearCollection(collectionName);
          this.$notify.success({
            title: '成功',
            message: `集合 ${collectionName} 已清空`
          });
          this.fetchCollections();
        } catch (error) {
          this.$notify.error({
            title: '错误',
            message: '清空集合失败: ' + (error.response?.data?.message || error.message)
          });
        } finally {
          this.$delete(this.loading, 'clear');
        }
      }).catch(() => {});
    },

    handleChange(file, fileList) {
      this.insertForm.files = fileList;
    },

    beforeRemove(file, fileList) {
      return this.$confirm(`确定移除 ${file.name}？`);
    },

    async submitUpload() {
      if (!this.insertForm.files.length) {
        this.$notify.warning({
          title: '提示',
          message: '请先选择文件'
        });
        return;
      }

      this.loading.upload = true;

      try {
        const { collectionName } = this.insertForm;
        const results = [];

        for (const file of this.insertForm.files) {
          const reader = new FileReader();

          // 返回 Promise 包装 FileReader
          const content = await new Promise((resolve, reject) => {
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
            reader.readAsText(file.raw);  // 读取文本
          });

          let jsonData;
          try {
            jsonData = JSON.parse(content);  // 解析为 JSON
          } catch (e) {
            this.$notify.error({
              title: '错误',
              message: `文件 ${file.name} 不是有效的 JSON`
            });
            continue;
          }

          // 调用接口插入数据
          await vectorAPI.insertData(collectionName, jsonData);
          results.push(file.name);
        }

        this.$notify.success({
          title: '成功',
          message: `以下文件插入成功: ${results.join(', ')}`
        });

        this.showInsertDialog = false;

      } catch (error) {
        this.$notify.error({
          title: '插入失败',
          message: error.response?.data?.message || error.message
        });
      } finally {
        this.loading.upload = false;
      }
    },
    async submitQaUpload() {
      const files = this.insertForm.files;

      if (!files.length) {
        this.$message.warning('请先选择CSV文件');
        return;
      }

      // 可选：过滤只允许 .csv 文件
      const csvFiles = files.filter(file => file.name.endsWith('.csv'));
      if (csvFiles.length === 0) {
        this.$message.warning('请选择CSV格式的文件');
        return;
      }

      const formData = new FormData();
      const selectedFile = csvFiles[0]; // 假设只允许上传一个 QA 文件

      formData.append("csv_file", selectedFile.raw); // 注意这里使用 raw 获取原始文件对象

      this.loading.qaUpload = true;

      try {
        const res = await vectorAPI.insertQaCsv(
          this.insertForm.collectionName, // 作为第一个参数传递
          formData
        );
        this.$message.success(res.data.message || 'QA数据插入成功');
        this.showInsertDialog = false;
      } catch (err) {
        const msg = err.response?.data?.detail || '插入失败';
        this.$message.error(msg);
      } finally {
        this.loading.qaUpload = false;
      }
    },
  },
  mounted() {
    this.fetchCollections();
  }
};
</script>

<style scoped lang="scss">
.vector-db-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;

  .page-title {
    color: #303133;
    margin-bottom: 24px;
    font-size: 24px;
    font-weight: 500;
    text-align: center;
  }

  .main-card {
    border-radius: 8px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 20px;

      .card-title {
        font-size: 18px;
        font-weight: 500;
        color: #303133;
      }
    }
  }

  .collection-table {
    margin-top: 10px;

    .el-table__header-wrapper {
      th {
        background-color: #f5f7fa;
        font-weight: 600;
        color: #303133;
        padding: 12px 16px;
      }
    }

    .el-table__body-wrapper {
      td {
        padding: 12px 16px;
      }
    }

    .collection-name {
      font-weight: 500;
      color: #409EFF;
    }

    .action-buttons {
      display: flex;
      gap: 8px;

      .action-btn {
        padding: 7px 12px;
      }
    }
  }

  .create-dialog,
  .insert-dialog {
    .el-dialog__header {
      border-bottom: 1px solid #EBEEF5;
      padding: 20px;

      .el-dialog__title {
        font-size: 18px;
        color: #303133;
      }
    }

    .el-form-item {
      margin-bottom: 20px;

      .el-form-item__label {
        padding-bottom: 8px;
        font-weight: 500;
      }
    }

    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      padding-top: 20px;
      border-top: 1px solid #EBEEF5;
    }
  }
}
</style>
