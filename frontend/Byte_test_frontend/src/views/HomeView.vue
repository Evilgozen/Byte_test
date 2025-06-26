<template>
  <div class="home-container">
    <!-- 页面头部 -->
    <a-page-header
      class="site-page-header"
      title="视频耗时分析系统"
      sub-title="Video Loading Time Analysis System"
    >
      <template #extra>
        <a-button type="primary" @click="refreshData">
          <template #icon>
            <ReloadOutlined />
          </template>
          刷新
        </a-button>
      </template>
    </a-page-header>

    <!-- 系统状态卡片 -->
    <a-row :gutter="[16, 16]" class="status-cards">
      <a-col :xs="24" :sm="12" :md="6">
        <a-card>
          <a-statistic
            title="项目总数"
            :value="systemInfo.database?.projects || 0"
            :value-style="{ color: '#3f8600' }"
          >
            <template #prefix>
              <FolderOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      
      <a-col :xs="24" :sm="12" :md="6">
        <a-card>
          <a-statistic
            title="视频总数"
            :value="systemInfo.database?.videos || 0"
            :value-style="{ color: '#1890ff' }"
          >
            <template #prefix>
              <VideoCameraOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      
      <a-col :xs="24" :sm="12" :md="6">
        <a-card>
          <a-statistic
            title="配置总数"
            :value="systemInfo.database?.stage_configs || 0"
            :value-style="{ color: '#cf1322' }"
          >
            <template #prefix>
              <SettingOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      
      <a-col :xs="24" :sm="12" :md="6">
        <a-card>
          <a-statistic
            title="系统状态"
            :value="systemInfo.system?.status || 'unknown'"
            :value-style="{ color: systemInfo.system?.status === 'running' ? '#3f8600' : '#cf1322' }"
          >
            <template #prefix>
              <CheckCircleOutlined v-if="systemInfo.system?.status === 'running'" />
              <ExclamationCircleOutlined v-else />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 项目列表 -->
    <a-card title="项目列表" class="project-list-card">
      <template #extra>
        <a-button type="primary" @click="showCreateProject = true">
          <template #icon>
            <PlusOutlined />
          </template>
          新建项目
        </a-button>
      </template>
      
      <a-spin :spinning="loading">
        <a-list
          :data-source="projects"
          :pagination="{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个项目`
          }"
        >
          <template #renderItem="{ item }">
            <a-list-item>
              <template #actions>
                <a-button type="link" @click="goToProject(item.id)">
                  查看详情
                </a-button>
                <a-button type="link" @click="goToVideoManagement(item.id)">
                  视频管理
                </a-button>
              </template>
              
              <a-list-item-meta>
                <template #title>
                  <a @click="goToProject(item.id)">{{ item.name }}</a>
                </template>
                <template #description>
                  {{ item.description || '暂无描述' }}
                </template>
                <template #avatar>
                  <a-avatar>
                    <template #icon>
                      <FolderOutlined />
                    </template>
                  </a-avatar>
                </template>
              </a-list-item-meta>
              
              <div class="project-meta">
                <p><strong>创建时间:</strong> {{ formatDate(item.created_at) }}</p>
                <p><strong>项目ID:</strong> {{ item.id }}</p>
              </div>
            </a-list-item>
          </template>
        </a-list>
      </a-spin>
    </a-card>

    <!-- 创建项目模态框 -->
    <a-modal
      v-model:open="showCreateProject"
      title="创建新项目"
      @ok="handleCreateProject"
      @cancel="resetCreateForm"
    >
      <a-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        layout="vertical"
      >
        <a-form-item label="项目名称" name="name">
          <a-input
            v-model:value="createForm.name"
            placeholder="请输入项目名称"
            :maxlength="100"
          />
        </a-form-item>
        
        <a-form-item label="项目描述" name="description">
          <a-textarea
            v-model:value="createForm.description"
            placeholder="请输入项目描述（可选）"
            :rows="4"
            :maxlength="500"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  ReloadOutlined,
  FolderOutlined,
  VideoCameraOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  PlusOutlined
} from '@ant-design/icons-vue'
import { projectApi, systemApi } from '@/api'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const systemInfo = ref({})
const projects = ref([])
const showCreateProject = ref(false)
const createFormRef = ref()

// 创建项目表单
const createForm = reactive({
  name: '',
  description: ''
})

// 表单验证规则
const createRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 1, max: 100, message: '项目名称长度应在1-100字符之间', trigger: 'blur' }
  ]
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 获取系统信息
const getSystemInfo = async () => {
  try {
    const data = await systemApi.getSystemInfo()
    systemInfo.value = data
  } catch (error) {
    console.error('获取系统信息失败:', error)
    message.error('获取系统信息失败')
  }
}

// 获取项目列表
const getProjects = async () => {
  try {
    loading.value = true
    const data = await projectApi.getProjects()
    projects.value = data
  } catch (error) {
    console.error('获取项目列表失败:', error)
    message.error('获取项目列表失败')
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = async () => {
  await Promise.all([
    getSystemInfo(),
    getProjects()
  ])
  message.success('数据刷新成功')
}

// 创建项目
const handleCreateProject = async () => {
  try {
    await createFormRef.value.validate()
    
    const data = await projectApi.createProject(createForm)
    message.success('项目创建成功')
    
    showCreateProject.value = false
    resetCreateForm()
    await getProjects()
  } catch (error) {
    if (error.errorFields) {
      // 表单验证错误
      return
    }
    console.error('创建项目失败:', error)
    message.error('创建项目失败')
  }
}

// 重置创建表单
const resetCreateForm = () => {
  createForm.name = ''
  createForm.description = ''
  createFormRef.value?.resetFields()
}

// 跳转到项目详情
const goToProject = (projectId) => {
  router.push(`/project/${projectId}`)
}

// 跳转到视频管理
const goToVideoManagement = (projectId) => {
  router.push(`/project/${projectId}/videos`)
}

// 组件挂载时获取数据
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.home-container {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: 100vh;
}

.site-page-header {
  background-color: white;
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.status-cards {
  margin-bottom: 24px;
}

.project-list-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.project-meta {
  text-align: right;
  color: #666;
  font-size: 12px;
}

.project-meta p {
  margin: 0;
  line-height: 1.5;
}

:deep(.ant-list-item) {
  padding: 16px 24px;
}

:deep(.ant-list-item:hover) {
  background-color: #fafafa;
}

:deep(.ant-statistic-title) {
  font-size: 14px;
  color: #666;
}

:deep(.ant-statistic-content) {
  font-size: 24px;
  font-weight: 600;
}
</style>
