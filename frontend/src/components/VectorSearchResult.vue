<template>
  <div class="vector-result">
    <h3>检索结果</h3>
    <div v-for="(results, collection) in searchResults" :key="collection">
      <h4>集合: {{ collection }}</h4>
      <el-table :data="results" border style="width: 100%">
        <el-table-column prop="score" label="相似度" width="100"></el-table-column>
        <el-table-column prop="metadata.content" label="内容"></el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    searchResults: {
      type: Object,
      required: true,
      default: () => ({})
    }
  }
};
</script>

<style scoped>
.vector-result {
  margin-top: 20px;
}
</style>