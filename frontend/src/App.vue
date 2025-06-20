<template>
  <div id="app">
    <nav class="navbar">
      <router-link to="/">首页</router-link> |
      <router-link to="/database">数据库</router-link> |
      <router-link to="/llm">LLM描述</router-link> |
      <router-link to="/vector">向量检索</router-link> |
      <router-link to="/graph">图数据库</router-link>
    </nav>
    <keep-alive>
      <router-view />
    </keep-alive>
    
  </div>
</template>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 20px;
}

.navbar {
  margin-bottom: 20px;
}

a {
  text-decoration: none;
  color: #3498db;
  padding: 0 10px;
}

a.router-link-exact-active {
  color: #e74c3c;
}
</style>
