<script setup>
import { ref, computed } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  HomeOutlined,
  VideoCameraOutlined,
  SettingOutlined,
  InfoCircleOutlined
} from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()

const collapsed = ref(false)

// 计算当前选中的菜单项
const selectedKeys = computed(() => {
  const path = route.path
  if (path === '/') return ['home']
  if (path.includes('/videos')) return ['videos']
  if (path.includes('/stages')) return ['stages']
  if (path === '/about') return ['about']
  return []
})

// 菜单项配置
const menuItems = [
  {
    key: 'home',
    icon: HomeOutlined,
    label: '项目管理',
    path: '/'
  },
  {
    key: 'about',
    icon: InfoCircleOutlined,
    label: '关于系统',
    path: '/about'
  }
]

const handleMenuClick = ({ key }) => {
  const item = menuItems.find(item => item.key === key)
  if (item) {
    router.push(item.path)
  }
}
</script>

<template>
  <a-layout class="app-layout">
    <!-- 侧边栏 -->
    <a-layout-sider
      v-model:collapsed="collapsed"
      :trigger="null"
      collapsible
      class="app-sider"
    >
      <div class="logo">
        <h2 v-if="!collapsed">视频分析系统</h2>
        <h2 v-else>VA</h2>
      </div>
      
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="inline"
        @click="handleMenuClick"
      >
        <a-menu-item v-for="item in menuItems" :key="item.key">
          <component :is="item.icon" />
          <span>{{ item.label }}</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    
    <!-- 主内容区域 -->
    <a-layout>
      <!-- 顶部导航栏 -->
      <a-layout-header class="app-header">
        <a-button
          type="text"
          @click="collapsed = !collapsed"
          class="trigger"
        >
          <MenuUnfoldOutlined v-if="collapsed" />
          <MenuFoldOutlined v-else />
        </a-button>
        
        <div class="header-right">
          <a-space>
            <a-button type="text" @click="router.push('/')">
              <HomeOutlined />
              首页
            </a-button>
            
            <!-- 面包屑导航 -->
            <a-breadcrumb v-if="route.path !== '/'">
              <a-breadcrumb-item>
                <router-link to="/">
                  <HomeOutlined />
                  首页
                </router-link>
              </a-breadcrumb-item>
              
              <a-breadcrumb-item v-if="route.params.projectId">
                <router-link :to="`/project/${route.params.projectId}/videos`">
                  <VideoCameraOutlined />
                  视频管理
                </router-link>
              </a-breadcrumb-item>
              
              <a-breadcrumb-item v-if="route.params.videoId">
                <SettingOutlined />
                阶段配置
              </a-breadcrumb-item>
            </a-breadcrumb>
          </a-space>
        </div>
      </a-layout-header>
      
      <!-- 主内容 -->
      <a-layout-content class="app-content">
        <RouterView />
      </a-layout-content>
      
      <!-- 底部 -->
      <a-layout-footer class="app-footer">
        <div class="footer-content">
          <p>视频耗时分析系统 © 2024 - 基于 Vue 3 + Ant Design Vue 构建</p>
        </div>
      </a-layout-footer>
    </a-layout>
  </a-layout>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.app-layout {
  min-height: 100vh;
}

.app-sider {
  overflow: auto;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
}

.app-sider .logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #001529;
  border-bottom: 1px solid #303030;
}

.app-sider .logo h2 {
  color: white;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.app-header {
  background: white;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 99;
}

.trigger {
  font-size: 18px;
  line-height: 64px;
  cursor: pointer;
  transition: color 0.3s;
}

.trigger:hover {
  color: #1890ff;
}

.header-right {
  display: flex;
  align-items: center;
}

.app-content {
  min-height: calc(100vh - 64px - 70px);
  background-color: #f0f2f5;
  padding: 0;
}

.app-footer {
  background-color: white;
  border-top: 1px solid #e8e8e8;
}

.footer-content {
  text-align: center;
  color: #666;
  padding: 20px 0;
}

.footer-content p {
  margin: 0;
  font-size: 14px;
}

/* 面包屑样式 */
.ant-breadcrumb {
  margin-left: 16px;
}

.ant-breadcrumb a {
  color: #666;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.ant-breadcrumb a:hover {
  color: #1890ff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-sider {
    position: fixed;
    z-index: 1000;
  }
  
  .header-right .ant-breadcrumb {
    display: none;
  }
}
</style>
