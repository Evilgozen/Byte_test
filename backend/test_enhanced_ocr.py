import sys
sys.path.append('.')

from ocr_module import OCRProcessor

# 创建OCR处理器实例
ocr_processor = OCRProcessor()

# 测试获取增强OCR结果
try:
    results = ocr_processor.get_enhanced_ocr_results(1)
    print(f"获取到 {len(results)} 条增强OCR结果")
    
    if results:
        print("\n第一条结果示例:")
        first_result = results[0]
        print(f"Frame ID: {first_result.frame_id}")
        print(f"Frame Path: {first_result.frame_path}")
        print(f"OCR Version: {first_result.ocr_version}")
        print(f"Processing Time: {first_result.processing_time}")
        print(f"Text Count: {first_result.text_count}")
        print(f"Full Text: {first_result.full_text[:100]}...")
    
except Exception as e:
    print(f"获取增强OCR结果失败: {e}")
    import traceback
    traceback.print_exc()