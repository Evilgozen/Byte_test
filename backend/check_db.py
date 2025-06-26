import sqlite3

# 连接数据库
conn = sqlite3.connect('video_analysis.db')
cursor = conn.cursor()

# 查看所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('数据库中的表:')
for table in tables:
    print(f'  {table[0]}')

# 查看OCR相关表的结构
for table in tables:
    table_name = table[0]
    if 'ocr' in table_name.lower():
        print(f'\n表 {table_name} 的结构:')
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            print(f'  {col[1]} ({col[2]})')
        
        # 查看前几条数据
        print(f'\n表 {table_name} 的前5条数据:')
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f'  {row}')

conn.close()