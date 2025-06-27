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

    <!-- OCR功能模块 -->
    <a-card title="OCR文字识别" class="ocr-card" style="margin-bottom: 16px;">
      <template #extra>
        <a-space>
          <a-tag v-if="ocrStats.database_records_count > 0" color="green">
            已识别 {{ ocrStats.database_records_count }} 帧
          </a-tag>
          <a-button 
            type="primary" 
            @click="startOCRProcessing" 
            :loading="ocrProcessing"
            :disabled="frames.length === 0"
          >
            <template #icon>
              <FileTextOutlined />
            </template>
            开始OCR识别
          </a-button>
          <a-button 
            v-if="ocrStats.database_records_count > 0"
            @click="viewOCRResults"
            :loading="ocrLoading"
          >
            <template #icon>
              <EyeOutlined />
            </template>
            查看结果
          </a-button>
          <a-button 
            v-if="ocrStats.database_records_count > 0"
            type="primary" 
            danger 
            @click="deleteOCRResults"
            :loading="ocrDeleting"
          >
            <template #icon>
              <DeleteOutlined />
            </template>
            删除OCR结果
          </a-button>
        </a-space>
      </template>

      <div v-if="ocrProcessing" class="ocr-processing">
        <a-progress 
          :percent="ocrProgress" 
          status="active"
          :show-info="true"
        />
        <p style="margin-top: 8px; text-align: center;">正在进行OCR识别，请稍候...</p>
      </div>

      <div v-else-if="frames.length === 0" class="ocr-empty">
        <a-empty description="请先提取视频帧，然后进行OCR识别" />
      </div>

      <div v-else>
        <a-row :gutter="16">
          <a-col :span="8">
            <a-statistic title="总帧数" :value="totalFrames" />
          </a-col>
          <a-col :span="8">
            <a-statistic title="已识别帧数" :value="ocrStats.database_records_count || 0" />
          </a-col>
          <a-col :span="8">
            <a-statistic title="识别进度" :value="ocrProgressPercent" suffix="%" />
          </a-col>
        </a-row>

        <!-- OCR配置 -->
        <a-divider>OCR配置</a-divider>
        <a-form layout="inline" :model="ocrConfig">
          <a-form-item label="使用GPU">
            <a-switch v-model:checked="ocrConfig.use_gpu" />
          </a-form-item>
          <a-form-item label="识别语言">
            <a-select v-model:value="ocrConfig.lang" style="width: 120px;">
              <a-select-option value="ch">中文</a-select-option>
              <a-select-option value="en">英文</a-select-option>
              <a-select-option value="ch_en">中英文</a-select-option>
            </a-select>
          </a-form-item>
        </a-form>
      </div>
    </a-card>

    <!-- 阶段关键词分析模块 -->
    <a-card title="阶段关键词分析" class="stage-analysis-card" style="margin-bottom: 16px;">
      <template #extra>
        <a-space>
          <a-tag v-if="stageConfigs.length > 0" color="blue">
            {{ stageConfigs.length }} 个阶段配置
          </a-tag>
          <a-button 
            type="primary" 
            @click="analyzeStageKeywords" 
            :loading="stageAnalyzing"
            :disabled="stageConfigs.length === 0 || ocrStats.database_records_count === 0"
          >
            <template #icon>
              <SearchOutlined />
            </template>
            分析阶段关键词
          </a-button>
          <a-button 
            v-if="stageAnalysisResults.length > 0"
            @click="viewStageAnalysisResults"
          >
            <template #icon>
              <EyeOutlined />
            </template>
            查看分析结果
          </a-button>
        </a-space>
      </template>

      <div v-if="stageConfigs.length === 0" class="stage-empty">
        <a-empty description="暂无阶段配置，请先在阶段配置页面创建阶段">
          <a-button type="primary" @click="goToStageConfig">
            <template #icon>
              <SettingOutlined />
            </template>
            配置阶段
          </a-button>
        </a-empty>
      </div>

      <div v-else-if="ocrStats.database_records_count === 0" class="stage-no-ocr">
        <a-empty description="请先完成OCR识别，然后进行阶段关键词分析" />
      </div>

      <div v-else>
        <a-row :gutter="16">
          <a-col :span="8">
            <a-statistic title="阶段配置数" :value="stageConfigs.length" />
          </a-col>
          <a-col :span="8">
            <a-statistic title="已分析阶段" :value="stageAnalysisResults.length" />
          </a-col>
          <a-col :span="8">
            <a-statistic title="分析状态" :value="stageAnalyzing ? '分析中' : '就绪'" />
          </a-col>
        </a-row>

        <!-- 阶段配置列表 -->
        <a-divider>阶段配置</a-divider>
        <a-list 
          :data-source="stageConfigs" 
          size="small"
          :pagination="false"
        >
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta
                :title="`阶段 ${item.stage_order}: ${item.stage_name}`"
                :description="`关键词: ${item.keywords.join(', ')}`"
              >
                <template #avatar>
                  <a-avatar :style="{ backgroundColor: '#1890ff' }">
                    {{ item.stage_order }}
                  </a-avatar>
                </template>
              </a-list-item-meta>
            </a-list-item>
          </template>
        </a-list>
      </div>
    </a-card>

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
                    <a-button 
                      type="default" 
                      size="small" 
                      @click="viewFrameOCR(frame)"
                      title="查看OCR结果"
                    >
                      <template #icon>
                        <FileTextOutlined />
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

    <!-- OCR结果查看模态框 -->
    <a-modal
      v-model:open="ocrResultsVisible"
      title="OCR识别结果"
      :footer="null"
      width="90%"
      centered
    >
      <div v-if="ocrLoading" class="loading-container">
        <a-spin size="large" />
        <p>加载OCR结果中...</p>
      </div>
      
      <div v-else-if="ocrResultsData">
        <!-- 统计信息 -->
        <a-card size="small" style="margin-bottom: 16px;">
          <a-row :gutter="16">
            <a-col :span="6">
              <a-statistic title="视频ID" :value="ocrResultsData.stats.video_id" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="数据库记录" :value="ocrResultsData.stats.database_records_count" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="JSON文件" :value="ocrResultsData.stats.json_files_count" />
            </a-col>
            <a-col :span="6">
              <a-tag :color="ocrResultsData.stats.data_consistency ? 'green' : 'red'">
                数据一致性: {{ ocrResultsData.stats.data_consistency ? '正常' : '异常' }}
              </a-tag>
            </a-col>
          </a-row>
        </a-card>

        <!-- 结果选项卡 -->
        <a-tabs v-model:activeKey="ocrResultsTab">
          <a-tab-pane key="database" tab="数据库结果">
            <div v-if="ocrResultsData.database_results.length === 0">
              <a-empty description="暂无数据库OCR结果" />
            </div>
            <div v-else>
              <a-table 
                :dataSource="ocrResultsData.database_results" 
                :columns="databaseColumns"
                :pagination="{ pageSize: 10 }"
                size="small"
                :scroll="{ x: 800 }"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'text_content'">
                    <div class="text-content-cell">
                      <div v-if="Array.isArray(record.text_content) && record.text_content.length > 0">
                        <a-tag v-for="(text, index) in record.text_content.slice(0, 3)" :key="index" style="margin: 2px;">
                          {{ text }}
                        </a-tag>
                        <span v-if="record.text_content.length > 3">...</span>
                      </div>
                      <span v-else class="text-muted">无文本</span>
                    </div>
                  </template>
                  <template v-else-if="column.key === 'confidence'">
                    <span v-if="record.confidence !== null">{{ (record.confidence * 100).toFixed(1) }}%</span>
                    <span v-else class="text-muted">-</span>
                  </template>
                  <template v-else-if="column.key === 'processed_at'">
                    {{ formatDate(record.processed_at) }}
                  </template>
                </template>
              </a-table>
            </div>
          </a-tab-pane>
          
          <a-tab-pane key="json" tab="JSON文件结果">
            <div v-if="ocrResultsData.json_results.length === 0">
              <a-empty description="暂无JSON文件OCR结果" />
            </div>
            <div v-else>
              <a-table 
                :dataSource="ocrResultsData.json_results" 
                :columns="jsonColumns"
                :pagination="{ pageSize: 10 }"
                size="small"
                :scroll="{ x: 800 }"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'processing_time'">
                    {{ record.processing_time }}s
                  </template>
                  <template v-else-if="column.key === 'has_raw_result'">
                    <a-tag :color="record.has_raw_result ? 'green' : 'red'">
                      {{ record.has_raw_result ? '有' : '无' }}
                    </a-tag>
                  </template>
                </template>
              </a-table>
            </div>
          </a-tab-pane>
        </a-tabs>
      </div>
    </a-modal>

    <!-- 单个帧OCR结果查看模态框 -->
    <a-modal
      v-model:open="frameOCRVisible"
      :title="`帧 ${selectedFrameForOCR?.frame_number} OCR识别结果`"
      :footer="null"
      width="80%"
      centered
    >
      <div v-if="frameOCRLoading" class="loading-container">
        <a-spin size="large" />
        <p>加载OCR结果中...</p>
      </div>
      
      <div v-else-if="frameOCRData">
        <!-- 帧信息 -->
        <a-card size="small" style="margin-bottom: 16px;">
          <a-row :gutter="16">
            <a-col :span="6">
              <a-statistic title="帧ID" :value="frameOCRData.frame_id" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="帧号" :value="selectedFrameForOCR?.frame_number" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="时间戳" :value="formatTimestamp(selectedFrameForOCR?.timestamp_ms)" />
            </a-col>
            <a-col :span="6">
              <div v-if="frameOCRData.confidence">
                <a-statistic title="置信度" :value="formatConfidence(frameOCRData.confidence)" />
              </div>
            </a-col>
          </a-row>
        </a-card>

        <!-- OCR识别文本 -->
        <a-card title="识别文本" size="small" style="margin-bottom: 16px;">
          <div v-if="frameOCRData.text_content">
            <div v-if="Array.isArray(frameOCRData.text_content) && frameOCRData.text_content.length > 0">
              <a-space direction="vertical" style="width: 100%;">
                <a-tag 
                  v-for="(text, index) in frameOCRData.text_content" 
                  :key="index" 
                  color="blue"
                  style="margin: 4px; padding: 8px; font-size: 14px;"
                >
                  {{ text }}
                </a-tag>
              </a-space>
            </div>
            <div v-else>
              <p>{{ frameOCRData.text_content }}</p>
            </div>
          </div>
          <div v-else>
            <a-empty description="该帧未识别到文本" />
          </div>
        </a-card>

        <!-- 边界框信息 -->
        <a-card title="边界框信息" size="small" v-if="frameOCRData.bbox">
          <pre style="background: #f5f5f5; padding: 12px; border-radius: 4px; overflow-x: auto;">{{ frameOCRData.bbox }}</pre>
        </a-card>

        <!-- 处理时间 -->
        <div v-if="frameOCRData.processed_at" style="margin-top: 16px; text-align: center; color: #666;">
          <small>处理时间: {{ formatDate(frameOCRData.processed_at) }}</small>
        </div>
      </div>
    </a-modal>

    <!-- 阶段分析结果模态框 -->
    <a-modal
      v-model:open="stageAnalysisVisible"
      title="阶段关键词分析结果"
      :footer="null"
      width="90%"
      centered
    >
      <div v-if="stageAnalysisLoading" class="loading-container">
        <a-spin size="large" />
        <p>加载分析结果中...</p>
      </div>
      
      <div v-else-if="stageAnalysisData">
        <!-- 分析摘要 -->
        <a-card size="small" style="margin-bottom: 16px;">
          <a-row :gutter="16">
            <a-col :span="6">
              <a-statistic title="视频ID" :value="stageAnalysisData?.video_id || '-'" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="总阶段数" :value="stageAnalysisData?.total_stages || 0" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="分析时间" :value="stageAnalysisData?.analysis_timestamp ? formatDate(stageAnalysisData.analysis_timestamp) : '-'" />
            </a-col>
            <a-col :span="6">
              <a-tag color="green">分析完成</a-tag>
            </a-col>
          </a-row>
        </a-card>

        <!-- 阶段分析结果 -->
        <a-collapse v-model:activeKey="activeStageKeys" ghost>
          <a-collapse-panel 
            v-for="stage in (stageAnalysisData.stage_analysis_results || [])" 
            :key="stage.stage_id"
            :header="`阶段 ${stage.stage_order}: ${stage.stage_name}`"
          >
            <template #extra>
              <a-space>
                <a-tag color="blue">{{ (stage.keywords || []).length }} 个关键词</a-tag>
                <a-tag color="green" v-if="(stage.keyword_analysis || []).length > 0">
                  {{ (stage.keyword_analysis || []).filter(k => (k.appearances || []).length > 0).length }} 个找到
                </a-tag>
              </a-space>
            </template>
            
            <!-- 关键词分析结果 -->
            <a-table 
              :dataSource="stage.keyword_analysis || []" 
              :columns="keywordAnalysisColumns"
              :pagination="false"
              size="small"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'keyword'">
                  <a-tag color="blue">{{ record.keyword }}</a-tag>
                </template>
                <template v-else-if="column.key === 'found'">
                  <a-tag :color="(record.total_occurrences || 0) > 0 ? 'green' : 'red'">
                    {{ (record.total_occurrences || 0) > 0 ? '是' : '否' }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'appearances_count'">
                  <a-tag color="blue">
                    {{ record.total_occurrences || 0 }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'first_appearance'">
                  <span v-if="record.first_appearance_timestamp">
                    {{ formatTimestamp(record.first_appearance_timestamp) }}
                  </span>
                  <span v-else class="text-muted">-</span>
                </template>
                <template v-else-if="column.key === 'last_disappearance'">
                  <span v-if="record.first_disappearance_timestamp">
                    {{ formatTimestamp(record.first_disappearance_timestamp) }}
                  </span>
                  <span v-else class="text-muted">-</span>
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-button 
                    v-if="(record.total_occurrences || 0) > 0" 
                    size="small" 
                    @click="viewKeywordDetails(record)"
                  >
                    查看详情
                  </a-button>
                </template>
              </template>
            </a-table>
          </a-collapse-panel>
        </a-collapse>
      </div>
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
  DownloadOutlined,
  FileTextOutlined,
  SearchOutlined,
  SettingOutlined
} from '@ant-design/icons-vue'
import { videoApi, ocrApi, stageConfigApi } from '../api'

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

// OCR相关
const ocrProcessing = ref(false)
const ocrLoading = ref(false)
const ocrDeleting = ref(false)
const ocrProgress = ref(0)
const ocrStats = ref({
  database_records_count: 0,
  json_files_count: 0,
  data_consistency: false
})
const ocrConfig = reactive({
  use_gpu: false,
  lang: 'ch'
})
const ocrResultsVisible = ref(false)
const ocrResultsData = ref(null)
const ocrResultsTab = ref('database')

// 单个帧OCR结果相关
const frameOCRVisible = ref(false)
const frameOCRLoading = ref(false)
const frameOCRData = ref(null)
const selectedFrameForOCR = ref(null)

// 阶段分析相关
const stageAnalysisLoading = ref(false)
const stageAnalysisVisible = ref(false)
const stageAnalysisData = ref(null)
const activeStageKeys = ref([])
const stageConfigs = ref([])
const stageAnalyzing = ref(false)
const stageAnalysisResults = ref([])

// OCR计算属性
const ocrProgressPercent = computed(() => {
  if (totalFrames.value === 0) return 0
  return Math.round((ocrStats.value.database_records_count / totalFrames.value) * 100)
})

// OCR表格列定义
const databaseColumns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '帧ID', dataIndex: 'frame_id', key: 'frame_id', width: 80 },
  { title: '识别文本', dataIndex: 'text_content', key: 'text_content', width: 300 },
  { title: '置信度', dataIndex: 'confidence', key: 'confidence', width: 100 },
  { title: '处理时间', dataIndex: 'processed_at', key: 'processed_at', width: 150 }
]

const jsonColumns = [
  { title: '帧ID', dataIndex: 'frame_id', key: 'frame_id', width: 80 },
  { title: '帧路径', dataIndex: 'frame_path', key: 'frame_path', width: 200 },
  { title: 'OCR版本', dataIndex: 'ocr_version', key: 'ocr_version', width: 100 },
  { title: '处理时间', dataIndex: 'processing_time', key: 'processing_time', width: 100 },
  { title: '文本块数量', dataIndex: 'text_blocks_count', key: 'text_blocks_count', width: 100 },
  { title: '原始结果', dataIndex: 'has_raw_result', key: 'has_raw_result', width: 100 }
]

// 关键词分析表格列定义
const keywordAnalysisColumns = [
  { title: '关键词', dataIndex: 'keyword', key: 'keyword', width: 120 },
  { title: '状态', dataIndex: 'found', key: 'found', width: 80 },
  { title: '出现次数', dataIndex: 'appearances_count', key: 'appearances_count', width: 100 },
  { title: '首次出现', dataIndex: 'first_appearance', key: 'first_appearance', width: 120 },
  { title: '最后消失', dataIndex: 'last_disappearance', key: 'last_disappearance', width: 120 },
  { title: '操作', dataIndex: 'actions', key: 'actions', width: 100 }
]

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
    getVideoFrames(),
    getOCRStats()
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

// OCR相关方法
const getOCRStats = async () => {
  try {
    const data = await ocrApi.viewOCRResults(videoId)
    ocrStats.value = {
      database_records_count: data.stats?.database_records_count || 0,
      json_files_count: data.stats?.json_files_count || 0,
      data_consistency: data.stats?.data_consistency || false
    }
  } catch (error) {
    console.error('获取OCR统计信息失败:', error)
    // 不显示错误消息，因为可能是还没有OCR结果
  }
}

const startOCRProcessing = async () => {
  try {
    ocrProcessing.value = true
    ocrProgress.value = 0
    
    const response = await ocrApi.processVideoOCR(videoId, ocrConfig)
    message.success('OCR识别已开始')
    
    // 开始轮询进度
    const pollProgress = setInterval(async () => {
      try {
        await getOCRStats()
        if (ocrStats.value.database_records_count >= totalFrames.value) {
          clearInterval(pollProgress)
          ocrProcessing.value = false
          message.success('OCR识别完成')
        }
      } catch (error) {
        console.error('轮询OCR进度失败:', error)
      }
    }, 2000)
    
    // 设置超时
    setTimeout(() => {
      clearInterval(pollProgress)
      ocrProcessing.value = false
    }, 300000) // 5分钟超时
    
  } catch (error) {
    console.error('启动OCR识别失败:', error)
    message.error(`启动OCR识别失败: ${error.message}`)
    ocrProcessing.value = false
  }
}

const viewOCRResults = async () => {
  try {
    ocrLoading.value = true
    ocrResultsVisible.value = true
    
    const data = await ocrApi.viewOCRResults(videoId)
    ocrResultsData.value = data
    
  } catch (error) {
    console.error('获取OCR结果失败:', error)
    message.error('获取OCR结果失败')
    ocrResultsVisible.value = false
  } finally {
    ocrLoading.value = false
  }
}

const deleteOCRResults = () => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除所有OCR识别结果吗？此操作不可恢复。',
    okText: '确定',
    cancelText: '取消',
    onOk: async () => {
      try {
        ocrDeleting.value = true
        await ocrApi.deleteVideoOCRResults(videoId)
        message.success('OCR结果删除成功')
        await getOCRStats()
      } catch (error) {
        console.error('删除OCR结果失败:', error)
        message.error('删除OCR结果失败')
      } finally {
        ocrDeleting.value = false
      }
    }
  })
}

// 查看单个帧的OCR结果
const viewFrameOCR = async (frame) => {
  try {
    frameOCRLoading.value = true
    selectedFrameForOCR.value = frame
    frameOCRVisible.value = true
    
    const data = await ocrApi.getFrameOCRResult(frame.id)
    frameOCRData.value = data
    
  } catch (error) {
    console.error('获取帧OCR结果失败:', error)
    if (error.response?.status === 404) {
      message.warning('该帧还没有OCR识别结果，请先进行OCR识别')
    } else {
      message.error('获取帧OCR结果失败')
    }
    frameOCRVisible.value = false
  } finally {
    frameOCRLoading.value = false
  }
}

const formatTextContent = (textContent) => {
  if (!textContent) return '-'
  if (Array.isArray(textContent)) {
    return textContent.join(', ')
  }
  return textContent
}

// 格式化置信度
const formatConfidence = (confidence) => {
  if (confidence === null || confidence === undefined) return '-'
  return `${(confidence * 100).toFixed(1)}%`
}

const formatProcessingTime = (processingTime) => {
  if (!processingTime) return '-'
  return `${processingTime.toFixed(3)}s`
}

// 阶段分析相关方法
const getStageConfigs = async () => {
  try {
    const data = await stageConfigApi.getVideoStageConfigs(videoId)
    stageConfigs.value = data
  } catch (error) {
    console.error('获取阶段配置失败:', error)
  }
}

const analyzeStageKeywords = async () => {
  try {
    stageAnalyzing.value = true
    stageAnalysisLoading.value = true
    const data = await ocrApi.analyzeStageKeywords(videoId)
    stageAnalysisData.value = data
    stageAnalysisResults.value = data.stage_analysis_results || []
    stageAnalysisVisible.value = true
    // 默认展开第一个阶段
    if (data.stage_analysis_results && data.stage_analysis_results.length > 0) {
      activeStageKeys.value = [data.stage_analysis_results[0].stage_id]
    }
    message.success('阶段关键词分析完成')
  } catch (error) {
    console.error('阶段关键词分析失败:', error)
    if (error.response?.status === 404) {
      message.warning('未找到阶段配置或OCR结果，请先配置阶段并完成OCR识别')
    } else {
      message.error('阶段关键词分析失败')
    }
  } finally {
    stageAnalyzing.value = false
    stageAnalysisLoading.value = false
  }
}

const viewStageAnalysisResults = () => {
  if (stageAnalysisData.value) {
    stageAnalysisVisible.value = true
  } else {
    message.warning('暂无分析结果，请先进行阶段关键词分析')
  }
}

const viewKeywordDetails = (keywordRecord) => {
  // 可以在这里实现查看关键词详细信息的功能
  console.log('查看关键词详情:', keywordRecord)
  message.info('关键词详情功能待实现')
}

const goToStageConfig = () => {
  router.push(`/project/${projectId}/video/${videoId}/stages`)
}

// 组件挂载时获取数据
onMounted(() => {
  refreshData()
  getStageConfigs()
})
</script>

<style scoped>
.video-detail-container {
  padding: 0;
  background-color: #f0f2f5;
  min-height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
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
  flex: 1;
  margin: 0;
  display: flex;
  flex-direction: column;
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

.pagination-container {
  margin-top: auto;
  padding: 16px 24px;
  background-color: white;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: center;
  position: sticky;
  bottom: 0;
  z-index: 10;
}

@media (max-width: 768px) {
  .frame-preview {
    flex-direction: column;
  }
  
  .preview-info {
    flex: none;
  }
  
  .app-content {
    margin-left: 0;
  }
}
</style>