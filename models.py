from pymongo import MongoClient
import requests
from datetime import datetime
import gridfs
import os
from dotenv import load_dotenv
import fitz
import io
from PIL import Image, ImageEnhance
import base64
from bson import ObjectId
import uuid
import time
import json

load_dotenv()  # 환경 변수 로드


# 클로바 OCR
secret_key = os.getenv("api")
api_url = 'https://mfpxhmwxm2.apigw.ntruss.com/custom/v1/35426/9ce749152d8f697b1dde8d90136d7443f3ee7b7038574145809c266e3f416d80/general'

# MongoDB Atlas 연결 설정
MONGO_URI = os.getenv("MONGODB_URL")
client = MongoClient(MONGO_URI)
db = client['OCR_DB']  # 데이터베이스 이름
upload_collection = db['upload'] # 업로드 된 문서 컬렉션
data_collection = db['data']  # 정형화된 데이터 컬렉션
fs = gridfs.GridFS(db)  # GridFS 객체 생성

api_key = os.getenv("api_key")

headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

def call_gpt_api(payload):
    # GPT-4o mini API로 OCR 요청
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()  # 응답 상태 코드 확인
        return response.json()['choices'][0]['message']['content'].strip()


def preprocess_image(image):
    """이미지 전처리 함수: 대비 조정 및 해상도 향상"""

    # 이미지 모드 변환
    if image.mode == 'RGBA':
        image = image.convert('RGB')  # RGBA를 RGB로 변환

    # 흑백 변환
    image = image.convert("L")  # 그레이스케일로 변환

    # 대비 증가
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)  # 대비 증가 (값 조정 가능)

    # 해상도 향상
    resize_num = 2
    image = image.resize((image.width * resize_num, image.height * resize_num))  # 해상도 향상

    # # 3. 이진화 (Adaptive Thresholding)
    # image_array = np.array(image)
    # threshold_value = image_array.mean()  # 평균값을 임계값으로 사용
    # binary_image = (image_array > threshold_value) * 255  # 이진화
    # image = Image.fromarray(binary_image.astype(np.uint8))

    # 선명도 향상
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2)  # 선명도 증가 (값 조정 가능)

    image.save(os.path.join("processed_image/output_image.png"))
    return image

def perform_ocr(image):
    """GPT-4o mini API를 사용하여 OCR 수행"""
    try:
        # 이미지를 base64 인코딩
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # OCR 요청 페이로드
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "이 이미지의 모든 텍스트를 정확히 추출하세요. 요약이나 재구성은 하지 마세요."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 700
        }

        # GPT-4o mini API로 OCR 요청
        ocr_text = call_gpt_api(payload)
        return ocr_text 

    except Exception as e:
        print(f"OCR 처리 중 오류 발생: {str(e)}")
        return "OCR 실패: 오류 발생"

def extract_text_with_layout(ocr_result):
    """OCR 결과를 기반으로 개행과 공백을 조절하여 텍스트를 추출하는 함수"""
    extracted_text = []

    for image in ocr_result.get('images', []):
        previous_y = None
        previous_x_end = None

        for index, field in enumerate(image.get('fields', [])):
            current_y = field['boundingPoly']['vertices'][2]['y']  # 현재 텍스트 박스 하단 y좌표
            current_x = field['boundingPoly']['vertices'][0]['x']  # 현재 텍스트 박스 첫 부분 x좌표
            text = field.get('inferText', '') + ' '

            # 이미지 높이 가져오기
            img_height = image.get("convertedImageInfo", {}).get("height", 1)

            # y 좌표 비율 계산
            if previous_y is not None:
                y_diff = abs(current_y - previous_y) / img_height  # 비율 계산
                if y_diff > 0.15: 
                    extracted_text.append('\n\n\n')  # 세 줄 개행
                    previous_x_end = None
                elif y_diff > 0.06: 
                    extracted_text.append('\n\n')  # 두 줄 개행
                    previous_x_end = None
                elif y_diff > 0.03:  
                    extracted_text.append('\n')  # 한 줄 개행
                    previous_x_end = None

            # x 좌표 비율 계산
            if previous_x_end is not None:
                x_diff = abs(current_x - previous_x_end)  # 현재 텍스트 박스 첫 부분과 이전 텍스트 박스 끝 부분 간의 차이
                if x_diff > 60:
                    extracted_text.append('    ')  # 공백 4개 추가
                elif x_diff > 35:
                    extracted_text.append('  ')  # 공백 2개 추가
                elif x_diff > 15:
                    extracted_text.append(' ')  # 공백 1개 추가

            # 텍스트 추가
            extracted_text.append(text)

            # 이전 좌표 업데이트
            previous_y = current_y
            previous_x_end = field['boundingPoly']['vertices'][2]['x']  # 현재 텍스트 박스 하단 x좌표 업데이트

    return ''.join(extracted_text).strip()

def perform_clova_ocr(image_file, api_url, secret_key):
    """네이버 클로바 OCR을 사용하여 이미지에서 텍스트를 추출하는 함수"""
    try:
        # 요청 JSON 구성
        request_json = {
            'images': [
                {
                    'format': 'png',
                    'name': 'demo'
                }
            ],
            'requestId': str(uuid.uuid4()),
            'version': 'V2',
            'timestamp': int(round(time.time() * 1000))
        }

        payload = {'message': json.dumps(request_json).encode('UTF-8')}

        # PIL 이미지 객체를 바이트로 변환
        img_byte_arr = io.BytesIO()
        image_file.save(img_byte_arr, format='PNG')  # 또는 필요한 형식으로 변경
        img_byte_arr.seek(0)  # 바이트 배열의 시작으로 이동

        # 파일 객체를 사용하여 POST 요청
        files = [
            ('file', img_byte_arr)  # 바이트로 변환된 파일 객체
        ]
        headers = {
            'X-OCR-SECRET': secret_key
        }

        # POST 요청
        response = requests.post(api_url, headers=headers, data=payload, files=files)

        # 응답 처리
        if response.status_code == 200:
            ocr_result = response.json()

            output_json_path = './ocr_result_json/ocr_result.json'

            with open(output_json_path, 'w', encoding='utf-8') as json_file:
                json.dump(ocr_result, json_file, ensure_ascii=False, indent=4)

            print(f"OCR 결과가 {output_json_path}에 저장되었습니다.")

            # OCR 결과를 기반으로 텍스트 추출
            formatted_text = extract_text_with_layout(ocr_result)  # 개행 및 공백 조절
            return formatted_text  # 추출한 텍스트 반환
        else:
            print(f"API 요청 실패: {response.status_code}, {response.text}")
            return "OCR 실패: API 요청 오류 발생"

    except Exception as e:
        print(f"OCR 처리 중 오류 발생: {str(e)}")
        return "OCR 실패: 오류 발생"
    

def summarize_text(text):
    """GPT-4o mini API를 사용하여 텍스트 요약"""
    if len(text.split()) < 50:
        return "텍스트가 너무 짧아 요약할 수 없습니다."

    try:
        # 텍스트 요약 요청 페이로드
        summary_payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": f"다음 텍스트의 중요 내용을 300토큰 안에 요약해줘:\n\n{text}"
                }
            ],
            "max_tokens": 300
        }

        # GPT-4o mini API로 요약 요청
        summary = call_gpt_api(summary_payload)
        return summary

    except Exception as e:
        print(f"요약 처리 중 오류 발생: {str(e)}")
        return "요약 실패: 오류 발생"
    
def format_data(text):
    """GPT-4o mini API를 사용하여 텍스트를 정형화"""
    try:
        # 데이터 정형화 요청 페이로드
        format_payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": f"다음 텍스트에서 문서 형식, 기업명, 관리자, 대표자, 전화번호, 날짜, 금액 그 외 등등 문서의 중요한 데이터들을 추출해서 '키 : 값' 형식으로 정형화해줘.:\n\n{text}\n\n 그 외 너의 말은 출력하지마"
                }
            ],
            "max_tokens": 400
        }

        # GPT-4o mini API로 데이터 정형화 요청
        formatted_data = call_gpt_api(format_payload)
        return formatted_data

    except Exception as e:
        print(f"데이터 정형화 처리 중 오류 발생: {str(e)}")
        return "정형화 실패: 오류 발생"

def convert_pdf_to_images(file):
    """PDF 파일을 이미지로 변환하는 함수"""
    pdf_document = fitz.open(stream=file.read(), filetype="pdf")  # PDF 문서 열기
    images = []

    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)  # 페이지 로드
        pix = page.get_pixmap()  # 페이지를 이미지로 변환
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)  # PIL 이미지로 변환
        images.append(image)

    return images  # 변환된 이미지 리스트 반환

def parse_page_range(range_str):
    """페이지 범위를 문자열로 받아 리스트로 변환하는 함수"""
    pages = []
    ranges = range_str.split(',')
    for r in ranges:
        if '-' in r:
            start, end = map(int, r.split('-'))
            pages.extend(range(start - 1, end))  # Python은 0부터 시작하므로 1을 빼줌
        else:
            pages.append(int(r) - 1)  # 단일 페이지도 0으로 맞추기
    return pages

def save_image_to_gridfs(image):
    """이미지를 GridFS에 저장하고 ID를 반환하는 함수"""
    buffered = io.BytesIO()

    # 이미지 모드가 RGBA일 경우 RGB로 변환
    if image.mode == 'RGBA':
        image = image.convert('RGB')  # RGBA를 RGB로 변환

    image.save(buffered, format="JPEG")  # 이미지를 JPEG 포맷으로 저장
    image_id = fs.put(buffered.getvalue(), filename="uploaded_image.jpg")  # GridFS에 저장
    return image_id

def parse_formatted_data(formatted_data_str):
    """정형화된 데이터 문자열을 사전으로 변환하는 함수"""
    formatted_data = {}
    lines = formatted_data_str.strip().split('\n')
    
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)  # ':' 기준으로 분리
            formatted_data[key.strip()] = value.strip()  # 키와 값을 저장
            
    return formatted_data

def save_db_upload(filename, ocr_text, image_id):
    """업로드 정보를 upload 컬렉션에 저장하는 함수"""
    try:
        upload_result = db['upload'].insert_one({
            "filename": filename,
            "ocr_text": ocr_text,
            "upload_date": datetime.now(),
            "image_id": image_id
        })
        return str(upload_result.inserted_id)  # 데이터 ID 반환
    except Exception as e:
        print(f"Error in save_db_upload: {str(e)}")
        return None

def save_db_data(upload_id, filename, ocr_text, summary, formatted_data, upload_date, image_id):
    """처리된 데이터를 data 컬렉션에 저장하는 함수"""
    try:
        data_result = data_collection.insert_one({
            "upload_id": upload_id,  # 업로드 ID 연결
            "filename": filename,
            "ocr_text": ocr_text,
            "summary": summary,
            "formatted_data": formatted_data,
            "upload_date": upload_date,
            "image_id": image_id
        })
        return str(data_result.inserted_id)  # 데이터 ID 반환
    except Exception as e:
        print(f"Error in save_db_data: {str(e)}")
        return None
    
def get_ocr_text_from_upload(upload_id):
    # MongoDB 쿼리 예시
    original = upload_collection.find_one({"_id": ObjectId(upload_id)})
    if original:
        original_text = original["ocr_text"]  # ocr_text 키에서 값 반환
        return original_text

def get_ocr_text_from_data(upload_id):
    # MongoDB 쿼리 예시
    data = data_collection.find_one({"upload_id": upload_id})
    if data:
        data_text = data["ocr_text"]
        return data_text
