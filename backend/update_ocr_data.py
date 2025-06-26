import json
import os
import sqlite3
from pathlib import Path

def update_ocr_results():
    """更新数据库中的OCR结果，从JSON文件中读取rec_texts"""
    
    # 连接数据库
    conn = sqlite3.connect('video_analysis.db')
    cursor = conn.cursor()
    
    # 获取所有OCR结果
    cursor.execute("SELECT id, frame_id FROM ocr_results")
    ocr_records = cursor.fetchall()
    
    print(f"找到 {len(ocr_records)} 条OCR记录")
    
    updated_count = 0
    
    for ocr_id, frame_id in ocr_records:
        # 查找对应的JSON文件
        video_ocr_dir = Path("data/ocr_results/video_1")  # 假设是video_1
        
        # 查找匹配的JSON文件
        json_file = None
        for filename in os.listdir(video_ocr_dir):
            if filename.endswith("_ocr_res.json"):
                try:
                    with open(video_ocr_dir / filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('frame_id') == frame_id:
                            json_file = video_ocr_dir / filename
                            break
                except Exception as e:
                    print(f"读取文件 {filename} 失败: {e}")
                    continue
        
        if json_file:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 提取rec_texts
                rec_texts = []
                raw_result = data.get('raw_result', [])
                
                for result in raw_result:
                    if isinstance(result, dict) and 'json' in result:
                        json_data = result['json']
                        if isinstance(json_data, dict) and 'res' in json_data:
                            res_data = json_data['res']
                            if isinstance(res_data, dict) and 'rec_texts' in res_data:
                                rec_texts.extend(res_data['rec_texts'])
                
                if rec_texts:
                    # 更新数据库
                    text_content_json = json.dumps(rec_texts, ensure_ascii=False)
                    cursor.execute(
                        "UPDATE ocr_results SET text_content = ? WHERE id = ?",
                        (text_content_json, ocr_id)
                    )
                    updated_count += 1
                    print(f"更新OCR记录 {ocr_id} (frame {frame_id}): {len(rec_texts)} 个文本")
                
            except Exception as e:
                print(f"处理文件 {json_file} 失败: {e}")
        else:
            print(f"未找到frame {frame_id}对应的JSON文件")
    
    # 提交更改
    conn.commit()
    conn.close()
    
    print(f"\n更新完成！共更新了 {updated_count} 条记录")

if __name__ == "__main__":
    update_ocr_results()