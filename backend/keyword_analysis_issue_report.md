# 关键词分析问题诊断报告

## 问题描述

用户反馈关键词分析结果异常：
- API返回显示分析的是"string"关键词
- 数据库中明明存在"加载中"文本
- 但分析结果显示"string"关键词出现0次

## 问题分析

### 1. 数据库验证结果

通过 `check_ocr_data.py` 脚本验证，数据库中确实存在"加载中"文本：

```
=== 包含'加载中'的OCR结果 ===
Video 1, Frame 7 (1166ms): ["加载中", "飞书技术训练营(测试开发)-第二…", ...]
Video 1, Frame 8 (1333ms): ["加载中", "飞书技术训练营(测试开发)-第二…", ...]
...
总共找到84次"加载中"的出现
```

### 2. 关键词分析功能验证

通过 `test_keyword_analysis_real.py` 脚本验证，关键词分析功能本身是正常的：

- **"加载中"关键词**: 出现84次，首次出现时间1166ms ✅
- **"string"关键词**: 出现0次，首次出现时间None ✅
- **"飞书"关键词**: 出现103次，首次出现时间833ms ✅
- **"技术"关键词**: 出现103次，首次出现时间833ms ✅

### 3. 问题根本原因

**问题不在于关键词分析功能，而在于API请求的参数！**

用户看到的API响应：
```json
{
  "message": "关键词分析完成",
  "video_id": 1,
  "analyzed_keywords": 1,
  "analysis_results": [
    {
      "keyword": "string",
      "first_appearance_timestamp": null,
      "first_disappearance_timestamp": null,
      "total_occurrences": 0,
      "frame_occurrences": [],
      "pattern_analysis": {
        "continuous_periods": [],
        "gap_periods": []
      }
    }
  ]
}
```

这说明：
1. API请求中传入的关键词列表是 `["string"]`
2. 而不是 `["加载中"]`
3. 由于数据库中不存在"string"文本，所以返回0次出现

## 解决方案

### 1. 前端检查

检查前端发送的API请求，确保：
- 关键词列表正确传递
- 中文关键词编码正确
- 请求参数格式符合 `KeywordAnalysisRequest` 模型

### 2. API请求示例

正确的API请求应该是：

```bash
curl -X POST "http://localhost:8000/videos/1/analyze-keywords" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["加载中"],
    "analysis_type": "both"
  }'
```

### 3. 调试建议

1. **记录API请求日志**：在 `analyze_video_keywords` 接口中添加请求参数日志
2. **验证请求参数**：确保前端传递的关键词列表正确
3. **编码检查**：确保中文关键词在传输过程中没有编码问题

## 新增功能

### 删除阶段配置接口

已添加两个删除接口：

1. **删除单个阶段配置**
   ```
   DELETE /stage-configs/{config_id}
   ```

2. **删除视频的所有阶段配置**
   ```
   DELETE /videos/{video_id}/stage-configs/
   ```

### 接口特性

- ✅ 支持级联删除（自动删除相关的分析结果）
- ✅ 错误处理（404 当配置或视频不存在时）
- ✅ 返回删除统计信息
- ✅ 事务安全（使用数据库事务）

## 测试验证

可以使用 `test_delete_stage_api.py` 脚本测试删除接口功能。

## 总结

关键词分析功能本身工作正常，问题在于API请求参数。建议：

1. 检查前端代码，确保正确传递关键词参数
2. 添加API请求日志以便调试
3. 使用新增的删除接口管理阶段配置
4. 进行端到端测试验证整个流程