from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import sqlite3
import uuid  # 고유 파일명 생성을 위한 모듈

# --- YOLOv8 모델 로드 ---
from ultralytics import YOLO
# 'yolov8n.pt'는 가장 작고 빠른 모델입니다. (coco 데이터셋으로 학습된 모델)
MODEL = YOLO('yolov8n.pt') 

# --- 환경 설정 ---
app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads/'
RESULT_FOLDER = 'static/results/'
DB_NAME = 'food_db.db'

# 폴더가 없으면 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- DB 조회 함수 ---
def get_calorie_info(food_name):
    """DB에서 음식 이름으로 칼로리 정보를 조회하는 함수"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 대소문자 구분 없이 조회하거나, 모델 클래스 이름과 DB 이름이 정확히 일치해야 함
    cursor.execute("SELECT calorie, unit FROM food_calories WHERE food_name=?", (food_name,))
    result = cursor.fetchone()
    conn.close()
    
    # DB에 정보가 있으면 반환, 없으면 기본값 반환
    if result:
        return {'calorie': result[0], 'unit': result[1]}
    else:
        # DB에 없는 음식일 경우 0kcal로 처리 (서비스 완성도 측면)
        return {'calorie': 0.0, 'unit': 'N/A (Not Found in DB)'}


# --- 웹 서비스 라우팅 ---

@app.route('/')
def index():
    """메인 페이지 렌더링"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_image():
    """이미지를 업로드하고 YOLO 분석을 수행하는 라우트"""
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file:
        # 1. 파일 저장
        # 고유한 파일명을 사용하여 보안 및 충돌 방지
        unique_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_id + '_' + filename)
        file.save(upload_path)
        
        # 2. YOLO 추론 (Prediction)
        # save=True: 탐지 결과를 바운딩 박스와 함께 이미지에 그려서 저장
        # conf=0.25: 탐지 신뢰도 25% 미만은 무시
        results = MODEL.predict(source=upload_path, save=True, project=RESULT_FOLDER, name=unique_id, exist_ok=True, conf=0.25)

        # 3. 결과 이미지 경로 설정
        # YOLO는 저장 시 폴더/이름 규칙을 따릅니다.
        result_dir = os.path.join(RESULT_FOLDER, unique_id)
        result_image_path = os.path.join(result_dir, os.path.basename(upload_path))
        
        # 웹에서 접근할 경로 (static/results/unique_id/filename)
        web_result_path = url_for('static', filename=f'results/{unique_id}/{os.path.basename(upload_path)}')

        # 4. 칼로리 계산 및 데이터 준비
        total_calorie = 0.0
        food_details = {} # {food_name: {'count': N, 'calorie': C, 'unit': U}}

        # YOLOv8 결과 객체에서 탐지된 객체 정보 추출
        for result in results:
            names = result.names # 클래스 ID와 이름 매핑
            for c in result.boxes.cls: # 탐지된 각 객체의 클래스 ID
                class_id = int(c)
                food_name = names[class_id]
                
                # DB에서 칼로리 정보 조회
                info = get_calorie_info(food_name)
                calorie = info['calorie']
                
                # 총 칼로리 합산
                total_calorie += calorie
                
                # 상세 정보 업데이트
                if food_name not in food_details:
                    food_details[food_name] = {'count': 0, 'calorie': calorie, 'unit': info['unit']}
                food_details[food_name]['count'] += 1
                
        # 5. 결과 페이지 렌더링
        return render_template('result.html', 
                               result_image=web_result_path,
                               total_calorie=round(total_calorie, 2),
                               food_details=food_details)

if __name__ == '__main__':
    # 디버그 모드는 개발 시에만 켜고, 제출 시에는 끄는 것이 좋습니다.
    app.run(debug=True)