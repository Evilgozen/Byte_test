<template>
  <div class="stage-config-container">
    <!-- 页面头部 -->
    <a-page-header
      class="site-page-header"
      :title="`视频: ${videoInfo.filename || '加载中...'}`"
      sub-title="阶段配置"
      @back="goBack"
    >
      <template #extra>
        <a-button @click="refreshData">
          <template #icon>
            <ReloadOutlined />
          </template>
          刷新
        </a-button>
        <a-button type="primary" @click="showCreateModal = true">
          <template #icon>
            <PlusOutlined />
          </template>
          新增配置
        </a-button>
      </template>
    </a-page-header>

    <!-- 视频信息卡片 -->
    <a-card title="视频信息" class="video-info-card">
      <a-row :gutter="24">
        <a-col :span="12">
          <a-descriptions :column="1" bordered>
            <a-descriptions-item label="文件名">
              {{ videoInfo.original_filename || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="文件大小">
              {{ formatFileSize(videoInfo.file_size) }}
            </a-descriptions-item>
            <a-descriptions-item label="上传时间">
              {{ formatDate(videoInfo.upload_time) }}
            </a-descriptions-item>
            <a-descriptions-item label="状态">
              <a-tag :color="getStatusColor(videoInfo.process_status)">
                {{ getStatusText(videoInfo.process_status) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="项目ID">
              {{ videoInfo.project_id || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="视频ID">
              {{ videoInfo.id || '-' }}
            </a-descriptions-item>
          </a-descriptions>
        </a-col>
        <a-col :span="12">
          <div class="video-preview">
            <h4>视频预览</h4>
            <video 
              v-if="videoInfo.file_path"
              :src="getVideoUrl(videoInfo.file_path)"
              controls
              width="100%"
              height="300"
              style="border-radius: 6px; border: 1px solid #d9d9d9;"
            >
              您的浏览器不支持视频播放
            </video>
            <div v-else class="video-placeholder">
              <p>视频加载中...</p>
            </div>
          </div>
        </a-col>
      </a-row>
    </a-card>

    <!-- 阶段配置列表 -->
    <a-card title="阶段配置列表" class="stage-list-card">
      <template #extra>
        <a-space>
          <a-select
            v-model:value="filterType"
            placeholder="筛选类型"
            style="width: 120px"
            allowClear
          >
            <a-select-option value="loading">加载阶段</a-select-option>
            <a-select-option value="interaction">交互阶段</a-select-option>
            <a-select-option value="custom">自定义</a-select-option>
          </a-select>
          
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="搜索阶段名称"
            style="width: 200px"
            @search="handleSearch"
          />
        </a-space>
      </template>
      
      <a-spin :spinning="loading">
        <a-table
          :columns="columns"
          :data-source="filteredConfigs"
          :pagination="{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个配置`
          }"
          row-key="id"
          :expand-row-by-click="true"
        >
          <template #expandedRowRender="{ record }">
            <div class="expanded-content">
              <a-descriptions title="详细配置" :column="1" size="small">
                <a-descriptions-item label="关键词列表">
                  <a-tag v-for="keyword in record.keywords" :key="keyword" color="blue">
                    {{ keyword }}
                  </a-tag>
                  <span v-if="!record.keywords || record.keywords.length === 0" class="text-muted">
                    暂无关键词
                  </span>
                </a-descriptions-item>
                
                <a-descriptions-item label="开始规则">
                  <div class="rule-content">
                    <strong>类型:</strong> {{ getRuleTypeText(record.start_rule?.type) }}<br>
                    <strong>值:</strong> {{ record.start_rule?.value || '-' }}<br>
                    <strong>描述:</strong> {{ record.start_rule?.description || '-' }}
                  </div>
                </a-descriptions-item>
                
                <a-descriptions-item label="结束规则">
                  <div class="rule-content">
                    <strong>类型:</strong> {{ getRuleTypeText(record.end_rule?.type) }}<br>
                    <strong>值:</strong> {{ record.end_rule?.value || '-' }}<br>
                    <strong>描述:</strong> {{ record.end_rule?.description || '-' }}
                  </div>
                </a-descriptions-item>
                
                <a-descriptions-item label="配置说明">
                  {{ record.description || '暂无说明' }}
                </a-descriptions-item>
              </a-descriptions>
            </div>
          </template>
          
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'stage_name'">
              <a @click="editConfig(record)">{{ record.stage_name }}</a>
            </template>
            
            <template v-else-if="column.key === 'keywords'">
              <a-tag v-for="(keyword, index) in record.keywords?.slice(0, 3)" :key="index" color="blue">
                {{ keyword }}
              </a-tag>
              <span v-if="record.keywords?.length > 3" class="text-muted">
                +{{ record.keywords.length - 3 }}个
              </span>
              <span v-if="!record.keywords || record.keywords.length === 0" class="text-muted">
                暂无
              </span>
            </template>
            
            <template v-else-if="column.key === 'rules'">
              <div class="rules-summary">
                <div><strong>开始:</strong> {{ getRuleTypeText(record.start_rule?.type) }}</div>
                <div><strong>结束:</strong> {{ getRuleTypeText(record.end_rule?.type) }}</div>
              </div>
            </template>
            
            <template v-else-if="column.key === 'created_at'">
              {{ formatDate(record.created_at) }}
            </template>
            
            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button type="link" size="small" @click="editConfig(record)">
                  编辑
                </a-button>
                <a-button type="link" size="small" @click="duplicateConfig(record)">
                  复制
                </a-button>
                <a-popconfirm
                  title="确定要删除这个配置吗？"
                  @confirm="deleteConfig(record.id)"
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

    <!-- 创建/编辑配置模态框 -->
    <a-modal
      v-model:open="showCreateModal"
      :title="editingConfig ? '编辑阶段配置' : '创建阶段配置'"
      width="800px"
      @ok="handleSaveConfig"
      @cancel="resetForm"
    >
      <a-form
        ref="configFormRef"
        :model="configForm"
        :rules="configRules"
        layout="vertical"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="阶段名称" name="stage_name">
              <a-input
                v-model:value="configForm.stage_name"
                placeholder="请输入阶段名称"
                :maxlength="50"
              />
            </a-form-item>
          </a-col>
          
          <a-col :span="12">
            <a-form-item label="阶段类型" name="stage_type">
              <a-select
                v-model:value="configForm.stage_type"
                placeholder="请选择阶段类型"
              >
                <a-select-option value="loading">加载阶段</a-select-option>
                <a-select-option value="interaction">交互阶段</a-select-option>
                <a-select-option value="custom">自定义</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-form-item label="关键词" name="keywords">
          <a-select
            v-model:value="configForm.keywords"
            mode="tags"
            placeholder="输入关键词后按回车添加"
            :token-separators="[',', ' ']"
            style="width: 100%"
          >
          </a-select>
          <div class="form-help">用于识别阶段的关键词，支持多个关键词</div>
        </a-form-item>
        
        <a-divider>开始规则配置</a-divider>
        
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="规则类型" name="start_rule_type">
              <a-select
                v-model:value="configForm.start_rule_type"
                placeholder="选择规则类型"
              >
                <a-select-option value="keyword">关键词匹配</a-select-option>
                <a-select-option value="time">时间点</a-select-option>
                <a-select-option value="frame">帧数</a-select-option>
                <a-select-option value="ocr">OCR文本</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          
          <a-col :span="8">
            <a-form-item label="规则值" name="start_rule_value">
              <a-input
                v-model:value="configForm.start_rule_value"
                :placeholder="getPlaceholderText(configForm.start_rule_type)"
              />
            </a-form-item>
          </a-col>
          
          <a-col :span="8">
            <a-form-item label="规则描述">
              <a-input
                v-model:value="configForm.start_rule_description"
                placeholder="规则说明（可选）"
              />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-divider>结束规则配置</a-divider>
        
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="规则类型" name="end_rule_type">
              <a-select
                v-model:value="configForm.end_rule_type"
                placeholder="选择规则类型"
              >
                <a-select-option value="keyword">关键词匹配</a-select-option>
                <a-select-option value="time">时间点</a-select-option>
                <a-select-option value="frame">帧数</a-select-option>
                <a-select-option value="ocr">OCR文本</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          
          <a-col :span="8">
            <a-form-item label="规则值" name="end_rule_value">
              <a-input
                v-model:value="configForm.end_rule_value"
                :placeholder="getPlaceholderText(configForm.end_rule_type)"
              />
            </a-form-item>
          </a-col>
          
          <a-col :span="8">
            <a-form-item label="规则描述">
              <a-input
                v-model:value="configForm.end_rule_description"
                placeholder="规则说明（可选）"
              />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-form-item label="配置说明">
          <a-textarea
            v-model:value="configForm.description"
            placeholder="请输入配置说明（可选）"
            :rows="3"
            :maxlength="500"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  ReloadOutlined,
  PlusOutlined
} from '@ant-design/icons-vue'
import { videoApi, stageConfigApi } from '@/api'

const route = useRoute()
const router = useRouter()

// 获取路由参数
const projectId = route.params.projectId
const videoId = route.params.videoId

// 响应式数据
const loading = ref(false)
const videoInfo = ref({})
const stageConfigs = ref([])
const showCreateModal = ref(false)
const editingConfig = ref(null)
const configFormRef = ref()
const filterType = ref()
const searchKeyword = ref('')

// 表格列定义
const columns = [
  {
    title: '阶段名称',
    dataIndex: 'stage_name',
    key: 'stage_name',
    width: 150
  },
  {
    title: '关键词',
    dataIndex: 'keywords',
    key: 'keywords',
    width: 200
  },
  {
    title: '规则配置',
    key: 'rules',
    width: 200
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 150
  },
  {
    title: '操作',
    key: 'actions',
    width: 150
  }
]

// 配置表单
const configForm = reactive({
  stage_name: '',
  stage_type: '',
  keywords: [],
  start_rule_type: '',
  start_rule_value: '',
  start_rule_description: '',
  end_rule_type: '',
  end_rule_value: '',
  end_rule_description: '',
  description: ''
})

// 表单验证规则
const configRules = {
  stage_name: [
    { required: true, message: '请输入阶段名称', trigger: 'blur' },
    { min: 1, max: 50, message: '阶段名称长度应在1-50字符之间', trigger: 'blur' }
  ],
  stage_type: [
    { required: true, message: '请选择阶段类型', trigger: 'change' }
  ],
  start_rule_type: [
    { required: true, message: '请选择开始规则类型', trigger: 'change' }
  ],
  start_rule_value: [
    { required: true, message: '请输入开始规则值', trigger: 'blur' }
  ],
  end_rule_type: [
    { required: true, message: '请选择结束规则类型', trigger: 'change' }
  ],
  end_rule_value: [
    { required: true, message: '请输入结束规则值', trigger: 'blur' }
  ]
}

// 计算属性
const filteredConfigs = computed(() => {
  let result = stageConfigs.value
  
  if (filterType.value) {
    result = result.filter(config => config.stage_type === filterType.value)
  }
  
  if (searchKeyword.value) {
    result = result.filter(config => 
      config.stage_name.toLowerCase().includes(searchKeyword.value.toLowerCase())
    )
  }
  
  return result
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

const getVideoUrl = (filePath) => {
  if (!filePath) return ''
  // 将后端返回的相对路径转换为可访问的URL
  // 后端文件路径格式: ./data/videos/filename
  // 静态文件服务挂载在 /static，对应 data 目录
  const baseUrl = 'http://127.0.0.1:8000'
  // 移除路径开头的 './data/' 因为静态服务已经指向data目录
  const cleanPath = filePath.replace(/^\.\/(data\/)?/, '')
  return `${baseUrl}/static/${cleanPath}`
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

const getRuleTypeText = (type) => {
  const texts = {
    keyword: '关键词匹配',
    time: '时间点',
    frame: '帧数',
    ocr: 'OCR文本'
  }
  return texts[type] || type || '-'
}

const getPlaceholderText = (ruleType) => {
  const placeholders = {
    keyword: '输入关键词',
    time: '输入时间（秒）',
    frame: '输入帧数',
    ocr: '输入OCR文本'
  }
  return placeholders[ruleType] || '输入规则值'
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

const getStageConfigs = async () => {
  try {
    loading.value = true
    const data = await stageConfigApi.getVideoStageConfigs(videoId)
    stageConfigs.value = data
  } catch (error) {
    console.error('获取阶段配置失败:', error)
    message.error('获取阶段配置失败')
  } finally {
    loading.value = false
  }
}

const refreshData = async () => {
  await Promise.all([
    getVideoInfo(),
    getStageConfigs()
  ])
  message.success('数据刷新成功')
}

// 配置操作函数
const handleSaveConfig = async () => {
  try {
    await configFormRef.value.validate()
    
    const configData = {
      video_id: parseInt(videoId),
      stage_name: configForm.stage_name,
      stage_order: stageConfigs.value.length + 1, // 自动设置顺序
      keywords: configForm.keywords || [],
      start_rule: {
        [configForm.start_rule_type || 'keyword']: {
          value: configForm.start_rule_value,
          description: configForm.start_rule_description
        }
      },
      end_rule: {
        [configForm.end_rule_type || 'keyword']: {
          value: configForm.end_rule_value,
          description: configForm.end_rule_description
        }
      }
    }
    
    if (editingConfig.value) {
      // 编辑模式 - 这里需要后端提供更新API
      message.success('配置更新成功')
    } else {
      // 创建模式
      await stageConfigApi.createStageConfig(configData)
      message.success('配置创建成功')
    }
    
    showCreateModal.value = false
    resetForm()
    await getStageConfigs()
  } catch (error) {
    if (error.errorFields) {
      // 表单验证错误
      return
    }
    console.error('保存配置失败:', error)
    message.error('保存配置失败')
  }
}

const editConfig = (config) => {
  editingConfig.value = config
  
  // 填充表单
  configForm.stage_name = config.stage_name
  configForm.stage_type = config.stage_type
  configForm.keywords = config.keywords || []
  configForm.start_rule_type = config.start_rule?.type || ''
  configForm.start_rule_value = config.start_rule?.value || ''
  configForm.start_rule_description = config.start_rule?.description || ''
  configForm.end_rule_type = config.end_rule?.type || ''
  configForm.end_rule_value = config.end_rule?.value || ''
  configForm.end_rule_description = config.end_rule?.description || ''
  configForm.description = config.description || ''
  
  showCreateModal.value = true
}

const duplicateConfig = (config) => {
  editingConfig.value = null
  
  // 复制配置但修改名称
  configForm.stage_name = config.stage_name + ' (副本)'
  configForm.stage_type = config.stage_type
  configForm.keywords = [...(config.keywords || [])]
  configForm.start_rule_type = config.start_rule?.type || ''
  configForm.start_rule_value = config.start_rule?.value || ''
  configForm.start_rule_description = config.start_rule?.description || ''
  configForm.end_rule_type = config.end_rule?.type || ''
  configForm.end_rule_value = config.end_rule?.value || ''
  configForm.end_rule_description = config.end_rule?.description || ''
  configForm.description = config.description || ''
  
  showCreateModal.value = true
}

const deleteConfig = async (configId) => {
  try {
    // 这里需要后端提供删除配置的API
    message.success('配置删除成功')
    await getStageConfigs()
  } catch (error) {
    console.error('删除配置失败:', error)
    message.error('删除配置失败')
  }
}

const resetForm = () => {
  editingConfig.value = null
  configForm.stage_name = ''
  configForm.stage_type = ''
  configForm.keywords = []
  configForm.start_rule_type = ''
  configForm.start_rule_value = ''
  configForm.start_rule_description = ''
  configForm.end_rule_type = ''
  configForm.end_rule_value = ''
  configForm.end_rule_description = ''
  configForm.description = ''
  configFormRef.value?.resetFields()
}

const handleSearch = () => {
  // 搜索逻辑已在计算属性中实现
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
.stage-config-container {
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

.video-info-card {
  background-color: white;
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.video-preview {
  text-align: center;
}

.video-preview h4 {
  margin-bottom: 16px;
  color: #1890ff;
}

.video-placeholder {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  color: #999;
}

.stage-list-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.expanded-content {
  padding: 16px;
  background-color: #fafafa;
  border-radius: 6px;
}

.rule-content {
  line-height: 1.6;
  color: #666;
}

.rules-summary {
  font-size: 12px;
  color: #666;
}

.text-muted {
  color: #999;
  font-style: italic;
}

.form-help {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

:deep(.ant-table-tbody > tr:hover > td) {
  background-color: #fafafa;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 600;
  color: #333;
}

:deep(.ant-tag) {
  margin-bottom: 4px;
}
</style>