import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/project/:projectId',
      name: 'project-detail',
      component: HomeView, // 暂时重定向到首页
      beforeEnter: (to, from, next) => {
        // 重定向到项目的视频管理页面
        next(`/project/${to.params.projectId}/videos`)
      }
    },
    {
      path: '/project/:projectId/videos',
      name: 'video-management',
      component: () => import('../views/VideoManagement.vue'),
    },
    {
      path: '/project/:projectId/video/:videoId',
      name: 'video-detail',
      component: () => import('../views/VideoDetail.vue'),
    },
    {
      path: '/project/:projectId/video/:videoId/stages',
      name: 'stage-configuration',
      component: () => import('../views/StageConfiguration.vue'),
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue'),
    },
  ],
})

export default router
