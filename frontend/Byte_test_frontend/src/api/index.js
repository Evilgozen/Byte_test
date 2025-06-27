import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    console.log('发送请求:', config.method?.toUpperCase(), config.url)
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    console.log('响应成功:', response.status, response.config.url)
    return response.data
  },
  error => {
    console.error('响应错误:', error.response?.status, error.response?.data)
    return Promise.reject(error)
  }
)

// 项目管理API
export const projectApi = {
  // 创建项目
  createProject(data) {
    return api.post('/projects/', data)
  },
  
  // 获取项目列表
  getProjects() {
    return api.get('/projects/')
  },
  
  // 获取项目详情
  getProject(projectId) {
    return api.get(`/projects/${projectId}`)
  },
  
  // 获取项目的视频列表
  getProjectVideos(projectId) {
    return api.get(`/projects/${projectId}/videos/`)
  }
}

// 视频管理API
export const videoApi = {
  // 上传视频
  uploadVideo(projectId, file) {
    const formData = new FormData()
    formData.append('file', file)
    
    return api.post(`/videos/upload/${projectId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 300000 // 5分钟超时
    })
  },
  
  // 获取视频详情
  getVideo(videoId) {
    return api.get(`/videos/${videoId}`)
  },
  
  // 获取视频帧列表
  getVideoFrames(videoId) {
    return api.get(`/videos/${videoId}/frames`)
  },
  
  // 提取视频帧
  extractVideoFrames(videoId, params) {
    return api.post(`/videos/${videoId}/extract-frames`, params)
  },
  
  // 删除视频所有帧
  deleteVideoFrames(videoId) {
    return api.delete(`/videos/${videoId}/frames`)
  },
  
  // 获取单个帧信息
  getFrame(frameId) {
    return api.get(`/frames/${frameId}`)
  },
  
  // 获取帧图片URL
  getFrameImageUrl(frameId) {
    return `${api.defaults.baseURL}/frames/${frameId}/image`
  }
}

// 阶段配置API
export const stageConfigApi = {
  // 创建阶段配置
  createStageConfig(data) {
    return api.post('/stage-configs/', data)
  },
  
  // 获取视频的阶段配置
  getVideoStageConfigs(videoId) {
    return api.get(`/videos/${videoId}/stage-configs/`)
  }
}

// OCR处理API
export const ocrApi = {
  // 处理视频OCR
  processVideoOCR(videoId, params) {
    return api.post(`/videos/${videoId}/process-ocr`, params)
  },
  
  // 获取视频OCR结果
  getVideoOCRResults(videoId) {
    return api.get(`/videos/${videoId}/ocr-results`)
  },
  
  // 获取增强OCR结果
  getEnhancedOCRResults(videoId) {
    return api.get(`/videos/${videoId}/enhanced-ocr-results`)
  },
  
  // 查看OCR结果
  viewOCRResults(videoId) {
    return api.get(`/videos/${videoId}/ocr-results/view`)
  },
  
  // 删除视频OCR结果
  deleteVideoOCRResults(videoId) {
    return api.delete(`/videos/${videoId}/ocr-results`)
  },
  
  // 获取OCR存储信息
  getOCRStorageInfo(videoId) {
    return api.get(`/videos/${videoId}/ocr-storage-info`)
  },
  
  // 获取OCR图片列表
  getOCRImages(videoId) {
    return api.get(`/videos/${videoId}/ocr-images`)
  },
  
  // 获取帧OCR结果
  getFrameOCRResult(frameId) {
    return api.get(`/frames/${frameId}/ocr-result`)
  },
  
  // 分析视频关键词
  analyzeVideoKeywords(videoId, keywords) {
    return api.post(`/videos/${videoId}/analyze-keywords`, { keywords })
  },
  
  // 分析阶段关键词
  analyzeStageKeywords(videoId) {
    return api.post(`/videos/${videoId}/analyze-stage-keywords`)
  }
}

// 系统信息API
export const systemApi = {
  // 获取系统信息
  getSystemInfo() {
    return api.get('/system/info')
  },
  
  // 获取根路径信息
  getRoot() {
    return api.get('/')
  }
}

export default api