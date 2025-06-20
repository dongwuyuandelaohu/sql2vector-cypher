<template>
  <el-card class="cypher-display">
    <h3>Cypher 脚本</h3>
    <el-button @click="copyToClipboard" icon="document-copy">复制</el-button>
    <pre ref="cypherText">{{ cypherScript }}</pre>
  </el-card>
</template>

<script>
export default {
  props: {
    cypherScript: {
      type: String,
      required: true,
      default: ''
    }
  },
  methods: {
    async copyToClipboard() {
      try {
        await navigator.clipboard.writeText(this.cypherScript);
        this.$message.success('已复制到剪贴板');
      } catch (err) {
        this.$message.error('复制失败');
      }
    }
  }
};
</script>

<style scoped>
.cypher-display pre {
  white-space: pre-wrap;
  word-break: break-word;
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  max-height: 400px;
  overflow-y: auto;
}
</style>