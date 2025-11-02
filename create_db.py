import sqlite3
import os

DB_NAME = 'food_db.db'

# 데이터베이스가 이미 존재하면 삭제하고 새로 생성
if os.path.exists(DB_NAME):
    os.remove(DB_NAME)

# 1. DB 연결 및 테이블 생성
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS food_calories (
        id INTEGER PRIMARY KEY,
        food_name TEXT NOT NULL UNIQUE,
        calorie REAL NOT NULL,
        unit TEXT
    )
''')

# 2. 순수 음식 항목 데이터 입력 (YOLO 모델의 COCO 클래스 이름과 매칭)
# *칼로리 값이 있는 음식 항목만 포함합니다.
foods = [
    # 🍎 과일/채소류 (Fruits/Vegetables)
    ('apple', 95.0, '1 piece'),
    ('banana', 105.0, '1 piece'),
    ('orange', 62.0, '1 piece'),
    ('carrot', 41.0, '1 cup'),
    ('broccoli', 55.0, '1 cup'),
    
    # 🍞 식사/간편식류 (Meals/Convenience Food)
    ('sandwich', 400.0, '1 serving'),
    ('pizza', 300.0, '1 slice'),
    ('hot dog', 320.0, '1 piece'),
    ('sushi', 350.0, '1 roll (6 pieces)'),
    
    # 🍰 디저트류 (Desserts)
    ('donut', 260.0, '1 piece'),
    ('cake', 350.0, '1 slice'),
    
    # 🍾 음료류
    ('bottle', 200.0, '1 bottle (Soda assumed)'), # COCO의 bottle은 음료 병일 가능성이 높아 칼로리 부여
]

cursor.executemany("INSERT INTO food_calories (food_name, calorie, unit) VALUES (?, ?, ?)", foods)

# 3. 변경 사항 저장 및 연결 닫기
conn.commit()
conn.close()

print(f"✅ SQLite 데이터베이스 '{DB_NAME}'에 총 {len(foods)}개의 순수 음식 항목이 성공적으로 업데이트되었습니다.")