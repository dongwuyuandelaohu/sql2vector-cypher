<template>
  <el-card class="table-metadata">
    <h3>表结构信息</h3>
    <el-table :data="columns" border style="width: 100%">
      <el-table-column prop="name" label="字段名" width="150"></el-table-column>
      <el-table-column prop="type" label="类型" width="150"></el-table-column>
      <el-table-column prop="comment" label="注释"></el-table-column>
    </el-table>
  </el-card>
</template>

<script>
export default {
  props: {
    columns: {
      type: Array,
      required: true,
      default: () => []
    }
  }
};
</script>

<style scoped>
.table-metadata {
  margin-top: 20px;
}
</style>