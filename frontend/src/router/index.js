import Vue from 'vue'
import VueRouter from 'vue-router'
import HomeView from '../views/HomeView.vue'
import DatabaseView from '../views/DatabaseView.vue'
import LLMDescriptionView from '../views/LLMDescriptionView.vue'
import VectorDBView from '../views/VectorDBView.vue'
import VectorInsertView from '../views/VectorInsertView.vue'
import VectorSearchView from '../views/VectorSearchView.vue'
import GraphDBView from '../views/GraphDBView.vue'

Vue.use(VueRouter)

const routes = [
  { path: '/', name: 'Home', component: HomeView },
  { path: '/database', name: 'Database', component: DatabaseView },
  { path: '/llm', name: 'LLM Description', component: LLMDescriptionView },
  { 
    path: '/vector', 
    name: 'Vector DB', 
    component: VectorDBView,
    children: [
      {
        path: 'insert/:collection',
        name: 'VectorInsert',
        component: VectorInsertView,
        props: true
      },
      {
        path: 'search/:collection',
        name: 'VectorSearch',
        component: VectorSearchView,
        props: true
      }
    ]
  },
  { path: '/graph', name: 'Graph DB', component: GraphDBView }
]

// 创建路由实例
const router = new VueRouter({
  mode: 'history', // 对应 createWebHistory()
  routes
})

export default router