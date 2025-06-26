<template>
  <div class="video-management-container">
    <!-- 页面头部 -->
    <a-page-header
      class="site-page-header"
      :title="`项目: ${projectInfo.name || '加载中...'}`"
      sub-title="视频管理"
      @back="goBack"
    >
      <template #extra>
        <a-button @click="refreshData">
          <template #icon>
            <ReloadOutlined />
          </template>
          刷新
        </a-button>
        <a-button type="primary" @click="showUploadModal = true">
          <template #icon>
            <UploadOutlined />
          </template>
          上传视频
        </a-button>
      </template>
    </a-page-header>

    <!-- 统计信息 -->
    <a-row :gutter="[16, 16]" class="stats-cards">
      <a-col :xs="24" :sm="8">
        <a-card>
          <a-statistic
            title="视频总数"
            :value="videos.length"
            :value-style="{ color: '#1890ff' }"
          >
            <template #prefix>
              <VideoCameraOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      
      <a-col :xs="24" :sm="8">
        <a-card>
          <a-statistic
            title="总大小"
            :value="totalSize"
            suffix="MB"
            :value-style="{ color: '#3f8600' }"
          >
            <template #prefix>
              <FileOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      
      <a-col :xs="24" :sm="8">
        <a-card>
          <a-statistic
            title="配置数量"
            :value="totalConfigs"
            :value-style="{ color: '#cf1322' }"
          >
            <template #prefix>
              <SettingOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 视频列表 -->
    <a-card title="视频列表" class="video-list-card">
      <template #extra>
        <a-space>
          <a-select
            v-model:value="filterStatus"
            placeholder="筛选状态"
            style="width: 120px"
            allowClear
          >
            <a-select-option value="uploaded">已上传</a-select-option>
            <a-select-option value="processing">处理中</a-select-option>
            <a-select-option value="completed">已完成</a-select-option>
            <a-select-option value="error">错误</a-select-option>
          </a-select>
          
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="搜索视频名称"
            style="width: 200px"
            @search="handleSearch"
          />
        </a-space>
      </template>
      
      <a-spin :spinning="loading">
        <a-table
          :columns="columns"
          :data-source="filteredVideos"
          :pagination="{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个视频`
          }"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <a @click="viewVideoDetail(record.id)">{{ record.original_filename }}</a>
            </template>
            
            <template v-else-if="column.key === 'size'">
              {{ formatFileSize(record.file_size) }}
            </template>
            
            <template v-else-if="column.key === 'status'">
              <a-tag :color="getStatusColor(record.process_status)">
                {{ getStatusText(record.process_status) }}
              </a-tag>
            </template>
            
            <template v-else-if="column.key === 'upload_time'">
              {{ formatDate(record.upload_time) }}
            </template>
            
            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button type="link" size="small" @click="viewVideoDetail(record.id)">
                  详情
                </a-button>
                <a-button type="link" size="small" @click="configureStages(record.id)">
                  配置阶段
                </a-button>
                <a-popconfirm
                  title="确定要删除这个视频吗？"
                  @confirm="deleteVideo(record.id)"
                >
                  <a-button type="link" size="small" danger>
                    删除
                  </a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-spin>
    </a-card>

    <!-- 上传视频模态框 -->
    <a-modal
      v-model:open="showUploadModal"
      title="上传视频文件"
      width="600px"
      :footer="null"
    >
      <a-upload-dragger
        v-model:file-list="fileList"
        name="file"
        multiple
        :before-upload="beforeUpload"
        :custom-request="customUpload"
        accept="video/*"
        :show-upload-list="{ showRemoveIcon: true }"
      >
        <p class="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p class="ant-upload-text">点击或拖拽视频文件到此区域上传</p>
        <p class="ant-upload-hint">
          支持单个或批量上传。支持常见视频格式：MP4、AVI、MOV、WMV等
        </p>
      </a-upload-dragger>
      
      <div class="upload-progress" v-if="uploadProgress.length > 0">
        <h4>上传进度</h4>
        <div v-for="progress in uploadProgress" :key="progress.uid" class="progress-item">
          <div class="progress-info">
            <span>{{ progress.name }}</span>
            <span>{{ progress.percent }}%</span>
          </div>
          <a-progress
            :percent="progress.percent"
            :status="progress.status"
            :stroke-color="progress.status === 'exception' ? '#ff4d4f' : '#1890ff'"
          />
        </div>
      </div>
      
      <div class="upload-actions">
        <a-button @click="clearUpload">清空</a-button>
        <a-button type="primary" @click="startUpload" :disabled="fileList.length === 0">
          开始上传
        </a-button>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  ReloadOutlined,
  UploadOutlined,
  VideoCameraOutlined,
  FileOutlined,
  SettingOutlined,
  InboxOutlined
} from '@ant-design/icons-vue'
import { projectApi, videoApi } from '@/api'

const route = useRoute()
const router = useRouter()

// 获取项目ID
const projectId = route.params.projectId

// 响应式数据
const loading = ref(false)
const projectInfo = ref({})
const videos = ref([])
const showUploadModal = ref(false)
const fileList = ref([])
const uploadProgress = ref([])
const filterStatus = ref()
const searchKeyword = ref('')

// 表格列定义
const columns = [
  {
    title: '视频名称',
    dataIndex: 'original_filename',
    key: 'name',
    ellipsis: true
  },
  {
    title: '文件大小',
    dataIndex: 'file_size',
    key: 'size',
    width: 120
  },
  {
    title: '状态',
    dataIndex: 'process_status',
    key: 'status',
    width: 100
  },
  {
    title: '上传时间',
    dataIndex: 'upload_time',
    key: 'upload_time',
    width: 180
  },
  {
    title: '操作',
    key: 'actions',
    width: 200
  }
]

// 计算属性
const filteredVideos = computed(() => {
  let result = videos.value
  
  if (filterStatus.value) {
    result = result.filter(video => video.status === filterStatus.value)
  }
  
  if (searchKeyword.value) {
    result = result.filter(video => 
      video.filename.toLowerCase().includes(searchKeyword.value.toLowerCase())
    )
  }
  
  return result
})

const totalSize = computed(() => {
  const bytes = videos.value.reduce((sum, video) => sum + (video.file_size || 0), 0)
  return (bytes / (1024 * 1024)).toFixed(2)
})

const totalConfigs = computed(() => {
  return videos.value.reduce((sum, video) => sum + (video.stage_configs_count || 0), 0)
})

// 工具函数
const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

const getStatusColor = (status) => {
  const colors = {
    pending: 'blue',
    processing: 'orange',
    completed: 'green',
    error: 'red',
    uploaded: 'blue'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    error: '错误',
    uploaded: '已上传'
  }
  return texts[status] || status
}

// API调用函数
const getProjectInfo = async () => {
  try {
    const data = await projectApi.getProject(projectId)
    projectInfo.value = data
  } catch (error) {
    console.error('获取项目信息失败:', error)
    message.error('获取项目信息失败')
  }
}

const getVideos = async () => {
  try {
    loading.value = true
    const data = await projectApi.getProjectVideos(projectId)
    videos.value = data
  } catch (error) {
    console.error('获取视频列表失败:', error)
    message.error('获取视频列表失败')
  } finally {
    loading.value = false
  }
}

const refreshData = async () => {
  await Promise.all([
    getProjectInfo(),
    getVideos()
  ])
  message.success('数据刷新成功')
}

// 上传相关函数
const beforeUpload = (file) => {
  const isVideo = file.type.startsWith('video/')
  if (!isVideo) {
    message.error('只能上传视频文件！')
    return false
  }
  
  const isLt500M = file.size / 1024 / 1024 < 500
  if (!isLt500M) {
    message.error('视频文件大小不能超过500MB！')
    return false
  }
  
  return false // 阻止自动上传
}

const customUpload = () => {
  // 自定义上传逻辑，阻止默认行为
}

const startUpload = async () => {
  if (fileList.value.length === 0) {
    message.warning('请选择要上传的视频文件')
    return
  }
  
  // 初始化进度
  uploadProgress.value = fileList.value.map(file => ({
    uid: file.uid,
    name: file.name,
    percent: 0,
    status: 'active'
  }))
  
  // 逐个上传文件
  for (let i = 0; i < fileList.value.length; i++) {
    const file = fileList.value[i]
    const progressItem = uploadProgress.value.find(p => p.uid === file.uid)
    
    try {
      progressItem.status = 'active'
      
      // 模拟上传进度
      const uploadInterval = setInterval(() => {
        if (progressItem.percent < 90) {
          progressItem.percent += Math.random() * 20
        }
      }, 200)
      
      await videoApi.uploadVideo(projectId, file.originFileObj || file)
      
      clearInterval(uploadInterval)
      progressItem.percent = 100
      progressItem.status = 'success'
      
      message.success(`${file.name} 上传成功`)
    } catch (error) {
      progressItem.status = 'exception'
      console.error(`上传 ${file.name} 失败:`, error)
      message.error(`上传 ${file.name} 失败`)
    }
  }
  
  // 上传完成后刷新列表
  setTimeout(() => {
    showUploadModal.value = false
    clearUpload()
    getVideos()
  }, 1000)
}

const clearUpload = () => {
  fileList.value = []
  uploadProgress.value = []
}

// 操作函数
const handleSearch = () => {
  // 搜索逻辑已在计算属性中实现
}

const viewVideoDetail = (videoId) => {
  router.push(`/project/${projectId}/video/${videoId}`)
}

const configureStages = (videoId) => {
  router.push(`/project/${projectId}/video/${videoId}/stages`)
}

const deleteVideo = async (videoId) => {
  try {
    // 这里需要后端提供删除视频的API
    message.success('视频删除成功')
    await getVideos()
  } catch (error) {
    console.error('删除视频失败:', error)
    message.error('删除视频失败')
  }
}

const goBack = () => {
  router.push('/')
}

// 组件挂载时获取数据
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.video-management-container {
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

.stats-cards {
  margin-bottom: 24px;
}

.video-list-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.upload-progress {
  margin-top: 16px;
  padding: 16px;
  background-color: #fafafa;
  border-radius: 6px;
}

.progress-item {
  margin-bottom: 12px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 12px;
  color: #666;
}

.upload-actions {
  margin-top: 16px;
  text-align: right;
}

.upload-actions .ant-btn {
  margin-left: 8px;
}

:deep(.ant-upload-drag) {
  background-color: #fafafa;
}

:deep(.ant-upload-drag:hover) {
  border-color: #1890ff;
}

:deep(.ant-table-tbody > tr:hover > td) {
  background-color: #fafafa;
}
</style>