<template>
  <div class="video-detail-container">
    <!-- 页面头部 -->
    <a-page-header
      class="site-page-header"
      :title="`视频详情: ${videoInfo.original_filename || '加载中...'}`"
      sub-title="视频帧管理"
      @back="goBack"
    >
      <template #extra>
        <a-button @click="refreshData">
          <template #icon>
            <ReloadOutlined />
          </template>
          刷新
        </a-button>
        <a-button type="primary" @click="extractFrames" :loading="extracting">
          <template #icon>
            <ScissorOutlined />
          </template>
          提取帧
        </a-button>
      </template>
    </a-page-header>



    <!-- 视频帧列表 -->
    <a-card title="视频帧列表" class="frames-list-card">
      <template #extra>
        <a-space>
          <span>共 {{ totalFrames }} 帧</span>
          <a-button 
            v-if="frames.length > 0" 
            type="primary" 
            danger 
            @click="deleteAllFrames"
            :loading="deleting"
          >
            <template #icon>
              <DeleteOutlined />
            </template>
            删除所有帧
          </a-button>
        </a-space>
      </template>

      <div v-if="loading" class="loading-container">
        <a-spin size="large" />
        <p>加载中...</p>
      </div>

      <div v-else-if="frames.length === 0" class="empty-container">
        <a-empty description="暂无视频帧数据">
          <a-button type="primary" @click="extractFrames">
            <template #icon>
              <ScissorOutlined />
            </template>
            提取视频帧
          </a-button>
        </a-empty>
      </div>

      <div v-else>
        <!-- 帧图片网格 -->
        <a-row :gutter="[16, 16]" class="frames-grid">
          <a-col 
            v-for="frame in paginatedFrames" 
            :key="frame.id" 
            :xs="24" 
            :sm="12" 
            :md="8" 
            :lg="6" 
            :xl="4"
          >
            <a-card 
              hoverable 
              class="frame-card"
              :body-style="{ padding: '8px' }"
            >
              <div class="frame-image-container">
                <img 
                  :src="getFrameImageUrl(frame.id)"
                  :alt="`帧 ${frame.frame_number}`"
                  class="frame-image"
                  @error="handleImageError"
                />
                <div class="frame-overlay">
                  <a-button-group>
                    <a-button 
                      type="primary" 
                      size="small" 
                      @click="previewFrame(frame)"
                    >
                      <template #icon>
                        <EyeOutlined />
                      </template>
                    </a-button>
                    <a-button 
                      type="primary" 
                      size="small" 
                      @click="downloadFrame(frame)"
                    >
                      <template #icon>
                        <DownloadOutlined />
                      </template>
                    </a-button>
                  </a-button-group>
                </div>
              </div>
              <div class="frame-info">
                <p class="frame-number">帧号: {{ frame.frame_number }}</p>
                <p class="frame-timestamp">时间: {{ formatTimestamp(frame.timestamp_ms) }}</p>
                <p class="frame-size">大小: {{ formatFileSize(frame.file_size) }}</p>
              </div>
            </a-card>
          </a-col>
        </a-row>

        <!-- 分页 -->
        <div class="pagination-container">
          <a-pagination
            v-model:current="currentPage"
            v-model:page-size="pageSize"
            :total="totalFrames"
            :show-size-changer="true"
            :show-quick-jumper="true"
            :show-total="(total, range) => `第 ${range[0]}-${range[1]} 项，共 ${total} 项`"
            :page-size-options="['12', '24', '48', '96']"
          />
        </div>
      </div>
    </a-card>

    <!-- 帧预览模态框 -->
    <a-modal
      v-model:open="previewVisible"
      title="帧预览"
      :footer="null"
      width="80%"
      centered
    >
      <div v-if="selectedFrame" class="frame-preview">
        <div class="preview-image-container">
          <img 
            :src="getFrameImageUrl(selectedFrame.id)"
            :alt="`帧 ${selectedFrame.frame_number}`"
            class="preview-image"
          />
        </div>
        <div class="preview-info">
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="帧号">
              {{ selectedFrame.frame_number }}
            </a-descriptions-item>
            <a-descriptions-item label="时间戳">
              {{ formatTimestamp(selectedFrame.timestamp_ms) }}
            </a-descriptions-item>
            <a-descriptions-item label="文件大小">
              {{ formatFileSize(selectedFrame.file_size) }}
            </a-descriptions-item>
            <a-descriptions-item label="提取时间">
              {{ formatDate(selectedFrame.extracted_at) }}
            </a-descriptions-item>
          </a-descriptions>
          <div class="preview-actions">
            <a-button type="primary" @click="downloadFrame(selectedFrame)">
              <template #icon>
                <DownloadOutlined />
              </template>
              下载图片
            </a-button>
          </div>
        </div>
      </div>
    </a-modal>

    <!-- 提取帧参数模态框 -->
    <a-modal
      v-model:open="extractModalVisible"
      title="提取视频帧"
      @ok="handleExtractFrames"
      :confirm-loading="extracting"
    >
      <a-form :model="extractForm" layout="vertical">
        <a-form-item label="提取频率 (FPS)" name="fps">
          <a-input-number 
            v-model:value="extractForm.fps" 
            :min="0.1" 
            :max="30" 
            :step="0.1"
            style="width: 100%"
          />
          <div class="form-help">每秒提取的帧数，例如 0.5 表示每2秒提取一帧</div>
        </a-form-item>
        <a-form-item label="图片质量" name="quality">
          <a-slider 
            v-model:value="extractForm.quality" 
            :min="1" 
            :max="100" 
            :marks="{ 1: '最低', 50: '中等', 85: '高', 100: '最高' }"
          />
        </a-form-item>
        <a-form-item label="最大帧数" name="maxFrames">
          <a-input-number 
            v-model:value="extractForm.maxFrames" 
            :min="1" 
            :max="1000" 
            style="width: 100%"
          />
          <div class="form-help">限制提取的最大帧数，避免生成过多文件</div>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  ReloadOutlined,
  ScissorOutlined,
  DeleteOutlined,
  EyeOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue'
import { videoApi } from '../api'

// 路由参数
const route = useRoute()
const router = useRouter()
const projectId = route.params.projectId
const videoId = route.params.videoId

// 响应式数据
const loading = ref(false)
const extracting = ref(false)
const deleting = ref(false)
const videoInfo = ref({})
const frames = ref([])
const totalFrames = computed(() => frames.value.length)

// 分页相关
const currentPage = ref(1)
const pageSize = ref(12)
const paginatedFrames = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return frames.value.slice(start, end)
})

// 预览相关
const previewVisible = ref(false)
const selectedFrame = ref(null)

// 提取帧相关
const extractModalVisible = ref(false)
const extractForm = reactive({
  fps: 1.0,
  quality: 85,
  maxFrames: 100
})

// 工具函数
const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatTimestamp = (ms) => {
  if (ms === undefined || ms === null) return '-'
  const totalSeconds = Math.floor(ms / 1000)
  const milliseconds = ms % 1000
  const seconds = totalSeconds % 60
  const minutes = Math.floor(totalSeconds / 60) % 60
  const hours = Math.floor(totalSeconds / 3600)
  
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}.${String(milliseconds).padStart(3, '0')}`
  } else {
    return `${minutes}:${String(seconds).padStart(2, '0')}.${String(milliseconds).padStart(3, '0')}`
  }
}

const getStatusColor = (status) => {
  const colors = {
    'pending': 'orange',
    'processing': 'blue',
    'completed': 'green',
    'failed': 'red'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return texts[status] || status
}

const getVideoUrl = (filePath) => {
  if (!filePath) return ''
  // 移除 ./data/ 前缀，因为静态文件服务挂载在 /static
  const cleanPath = filePath.replace(/^\.\/data\//, '')
  return `http://127.0.0.1:8000/static/${cleanPath}`
}

const getFrameImageUrl = (frameId) => {
  return `http://127.0.0.1:8000/frames/${frameId}/image`
}

const handleImageError = (event) => {
  console.error('图片加载失败:', event.target.src)
  event.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjVmNWY1Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuWbvueJh+WKoOi9veWksei0pTwvdGV4dD48L3N2Zz4='
}

// API调用函数
const getVideoInfo = async () => {
  try {
    const data = await videoApi.getVideo(videoId)
    videoInfo.value = data
  } catch (error) {
    console.error('获取视频信息失败:', error)
    message.error('获取视频信息失败')
  }
}

const getVideoFrames = async () => {
  try {
    loading.value = true
    const response = await fetch(`http://127.0.0.1:8000/videos/${videoId}/frames`)
    if (response.ok) {
      const data = await response.json()
      frames.value = data
    } else {
      throw new Error('获取帧列表失败')
    }
  } catch (error) {
    console.error('获取视频帧失败:', error)
    message.error('获取视频帧失败')
  } finally {
    loading.value = false
  }
}

const refreshData = async () => {
  await Promise.all([
    getVideoInfo(),
    getVideoFrames()
  ])
  message.success('数据刷新成功')
}

// 帧操作函数
const extractFrames = () => {
  extractModalVisible.value = true
}

const handleExtractFrames = async () => {
  try {
    extracting.value = true
    const response = await fetch(`http://127.0.0.1:8000/videos/${videoId}/extract-frames`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        fps: extractForm.fps,
        quality: extractForm.quality,
        max_frames: extractForm.maxFrames
      })
    })
    
    if (response.ok) {
      const result = await response.json()
      message.success(`视频分帧完成，共提取 ${result.total_frames} 帧`)
      extractModalVisible.value = false
      await getVideoFrames()
    } else {
      const error = await response.json()
      throw new Error(error.detail || '分帧失败')
    }
  } catch (error) {
    console.error('提取帧失败:', error)
    message.error(`提取帧失败: ${error.message}`)
  } finally {
    extracting.value = false
  }
}

const deleteAllFrames = () => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除所有视频帧吗？此操作不可恢复。',
    okText: '确定',
    cancelText: '取消',
    onOk: async () => {
      try {
        deleting.value = true
        const response = await fetch(`http://127.0.0.1:8000/videos/${videoId}/frames`, {
          method: 'DELETE'
        })
        
        if (response.ok) {
          message.success('所有帧已删除')
          frames.value = []
          currentPage.value = 1
        } else {
          throw new Error('删除失败')
        }
      } catch (error) {
        console.error('删除帧失败:', error)
        message.error('删除帧失败')
      } finally {
        deleting.value = false
      }
    }
  })
}

const previewFrame = (frame) => {
  selectedFrame.value = frame
  previewVisible.value = true
}

const downloadFrame = async (frame) => {
  try {
    const response = await fetch(getFrameImageUrl(frame.id))
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `frame_${frame.frame_number}_${frame.timestamp_ms}ms.jpg`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      message.success('图片下载成功')
    } else {
      throw new Error('下载失败')
    }
  } catch (error) {
    console.error('下载帧图片失败:', error)
    message.error('下载帧图片失败')
  }
}

const goBack = () => {
  router.push(`/project/${projectId}/videos`)
}

// 组件挂载时获取数据
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.video-detail-container {
  padding: 0;
  background-color: #f0f2f5;
  min-height: 100vh;
}

.site-page-header {
  background-color: white;
  margin: 0 0 0 0;
  border-radius: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}



.frames-list-card {
  background-color: white;
  border-radius: 0;
  box-shadow: none;
  width: 100%;
  height: calc(100vh - 80px);
  margin: 0;
}

.loading-container {
  text-align: center;
  padding: 40px;
}

.empty-container {
  text-align: center;
  padding: 40px;
}

.frames-grid {
  margin-bottom: 24px;
}

.frame-card {
  position: relative;
  transition: all 0.3s;
}

.frame-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.frame-image-container {
  position: relative;
  overflow: hidden;
  border-radius: 4px;
}

.frame-image {
  width: 100%;
  height: 400px;
  object-fit: contain;
  transition: transform 0.3s;
}

.frame-card:hover .frame-image {
  transform: scale(1.05);
}

.frame-overlay {
  position: absolute;
  height: calc(100% - 20px);
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.frame-card:hover .frame-overlay {
  opacity: 1;
}

.frame-info {
  padding: 8px 4px 4px;
}

.frame-info p {
  margin: 2px 0;
  font-size: 12px;
  color: #666;
}

.frame-number {
  font-weight: 600;
  color: #1890ff;
}

.pagination-container {
  text-align: center;
  padding: 24px 0;
}

.frame-preview {
  display: flex;
  gap: 12px;
}

.preview-image-container {
  flex: 1;
  text-align: center;
  display: flex;
  justify-content: center;
  align-items: center;
}

.preview-image {
  max-width: 100%;
  max-height: 80vh;
  width: auto;
  height: auto;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.preview-info {
  flex: 0 0 450px;
}

.preview-actions {
  margin-top: 16px;
  text-align: center;
}

.form-help {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 600;
  color: #333;
}

:deep(.ant-card-body) {
  /* padding: 16px; */
  height: calc(50vh - 280px);
  /* overflow: auto; */
}

@media (max-width: 768px) {
  .frame-preview {
    flex-direction: column;
  }
  
  .preview-info {
    flex: none;
  }
}
</style>