<template>
  <el-card class="insert-view">
    <div slot="header" class="header-wrapper">
      <span>插入数据到集合：<strong>{{ collection }}</strong></span>
      <el-button class="float-right" size="small" @click="goBack">
        <i class="el-icon-back"></i> 返回
      </el-button>
    </div>

    <el-form label-position="top">
      <el-form-item label="文本数据（JSON格式）">
        <el-input
          type="textarea"
          v-model="insertDataText"
          :rows="10"
          placeholder='例如：[{"text": "示例文本1"}, {"text": "示例文本2"}]'
        ></el-input>
      </el-form-item>

      <el-form-item label="或上传文件（.json 或 .txt）">
        <el-upload
          action="#"
          :on-change="handleFileChange"
          :auto-upload="false"
          :show-file-list="false"
          accept=".json,.txt"
        >
          <el-button type="primary">
            <i class="el-icon-upload"></i> 选择文件
          </el-button>
          <span v-if="fileName" class="file-name">已选择：{{ fileName }}</span>
        </el-upload>
      </el-form-item>

      <el-button
        type="success"
        @click="handleInsert"
        :loading="loading"
        icon="el-icon-upload2"
      >
        提交插入
      </el-button>
    </el-form>
  </el-card>
</template>

<script>
import vectorAPI from '@/api/vector';

export default {
  name: 'VectorInsertView',
  data() {
    return {
      insertDataText: '',
      fileContent: '',
      fileName: '',
      loading: false
    };
  },
  computed: {
    collection() {
      return this.$route.params.collection;
    }
  },
  methods: {
    goBack() {
      this.$router.push({ name: 'VectorDB' });
    },
    handleFileChange(file) {
      this.fileName = file.name;
      const reader = new FileReader();
      reader.onload = () => {
        this.fileContent = reader.result;
      };
      reader.readAsText(file.raw);
    },
    async handleInsert() {
      if (!this.insertDataText && !this.fileContent) {
        this.$notify.warning({
          title: '提示',
          message: '请输入文本或上传文件后再提交'
        });
        return;
      }

      let data;
      try {
        const raw = this.fileContent || this.insertDataText;
        data = JSON.parse(raw);

        if (!Array.isArray(data)) {
          data = [data];
        }
      } catch (e) {
        this.$notify.error({
          title: '错误',
          message: '数据格式错误，请输入合法的 JSON 格式'
        });
        return;
      }

      this.loading = true;
      try {
        await vectorAPI.insertData(this.collection, data);
        this.$notify.success({
          title: '成功',
          message: `已成功向集合 "${this.collection}" 插入 ${data.length} 条数据`
        });

        // 重置表单
        this.insertDataText = '';
        this.fileContent = '';
        this.fileName = '';
      } catch (error) {
        this.$notify.error({
          title: '错误',
          message: '插入数据失败: ' + (error.response?.data?.message || error.message)
        });
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.insert-view {
  margin-top: 20px;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.float-right {
  float: right;
}

.header-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-name {
  margin-left: 10px;
  font-size: 14px;
  color: #606266;
}
</style>
