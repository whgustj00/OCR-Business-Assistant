from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageEnhance
import fitz  # PyMuPDF
import io
import base64
import requests
from dotenv import load_dotenv
import os
from pymongo import MongoClient
from datetime import datetime
import gridfs

load_dotenv()  # 환경 변수 로드

api_key = os.getenv("api_key")

app = Flask(__name__)
CORS(app)

headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

# MongoDB Atlas 연결 설정
MONGO_URI = os.getenv("MONGODB_URL")
client = MongoClient(MONGO_URI)
db = client['OCR_DB']  # 데이터베이스 이름
data_collection = db['data']  # 정형화된 데이터 컬렉션
fs = gridfs.GridFS(db)  # GridFS 객체 생성

def preprocess_image(image):
    """이미지 전처리 함수: 대비 조정 및 해상도 향상"""

    # 이미지 모드 변환
    if image.mode == 'RGBA':
        image = image.convert('RGB')  # RGBA를 RGB로 변환

    # 흑백 변환
    image = image.convert("L")  # 그레이스케일로 변환

    # 대비 증가
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)  # 대비 증가 (값 조정 가능)

    # 해상도 향상
    image = image.resize((image.width * 7, image.height * 7), Image.LANCZOS)  # 해상도 향상

    # 선명도 향상
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.5)  # 선명도 증가 (값 조정 가능)
    return image

def call_gpt_api(payload):
    # GPT-4o mini API로 OCR 요청
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()  # 응답 상태 코드 확인
        return response.json()['choices'][0]['message']['content'].strip()

def perform_ocr(image):
    """GPT-4o mini API를 사용하여 OCR 수행"""
    try:
        # 이미지를 base64 인코딩
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
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
                            "text": "이 이미지에서 문서 포맷에 맞게 텍스트를 추출해서 요약하지 말고 OCR 수행해줘. 그 외 내용은 출력 금지."
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
            "max_tokens": 500
        }

        # GPT-4o mini API로 OCR 요청
        ocr_text = call_gpt_api(payload)
        return ocr_text 

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
                    "content": f"다음 텍스트의 중요 내용을 200토큰 안에 요약해줘:\n\n{text}"
                }
            ],
            "max_tokens": 200
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
            "max_tokens": 300
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

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # 파일 존재 여부 확인
        if 'file' not in request.files:
            return jsonify({"error": "파일이 없습니다."}), 400

        file = request.files['file']
        # 파일 이름 확인
        if file.filename == '':
            return jsonify({"error": "파일 이름이 비어있습니다."}), 400

        page_range = request.form.get('pageRange', '')  # 페이지 범위 가져오기
        pages_to_process = parse_page_range(page_range) if page_range else None  # 페이지 범위 파싱

        ocr_text = ""

        if file.content_type == 'application/pdf':
            # PDF 파일을 이미지로 변환
            images = convert_pdf_to_images(file)

            if pages_to_process:
                for page_number in pages_to_process:
                    if page_number < len(images):  # 페이지 번호 유효성 검사
                        img = images[page_number]

                        # GridFS에 이미지 저장 (전처리 전에)
                        image_id = save_image_to_gridfs(img)

                        # 이미지 처리
                        img = preprocess_image(img)

                        ocr_text += f"=== 페이지 {page_number + 1} ===\n\n"  # 페이지 번호 추가
                        ocr_text += perform_ocr(img) + "\n\n\n"  # OCR 수행 후 결과 구분
            else:
                for i, img in enumerate(images):
                    # GridFS에 이미지 저장 (전처리 전에)
                    image_id = save_image_to_gridfs(img)
                    
                    # 이미지 처리
                    img = preprocess_image(img)

                    ocr_text += f"=== 페이지 {i + 1} ===\n\n"  # 페이지 번호 추가
                    ocr_text += perform_ocr(img) + "\n\n\n"  # OCR 수행 후 결과 구분
        else:
            # JPG, PNG 파일 처리
            img = Image.open(file)

            # GridFS에 이미지 저장 (전처리 전에)
            image_id = save_image_to_gridfs(img)
            
            # 이미지 처리
            img = preprocess_image(img)

            ocr_text = perform_ocr(img)  # OCR 수행
            # ocr_text = "123"

        # 텍스트 요약
        summary = summarize_text(ocr_text)

        # 데이터 정형화
        formatted_data_str = format_data(ocr_text)
        formatted_data = parse_formatted_data(formatted_data_str)  # 문자열을 사전으로 변환

        # summary = "요약 데이터"
        # formatted_data = "정형화 데이터"

        # MongoDB에 저장
        data_result = data_collection.insert_one({
            "filename": file.filename,
            "upload_date": datetime.now(),
            "ocr_text": ocr_text,
            "summary": summary,
            "formatted_data": formatted_data,
            "image_id": image_id  # GridFS 이미지 ID 추가
        })
        print(f"data ID: {data_result.inserted_id}")  # 추가된 코드

        # HTML 레이아웃으로 텍스트 구성
        response_html = f"""
        <div>
            <h2>OCR 결과</h2>
            <pre>{ocr_text}</pre>
            <h2>요약 결과</h2>
            <pre>{summary}</pre>
            <h2>정형화된 데이터</h2>
            <pre>{formatted_data_str}</pre>
        </div>
        """

        return jsonify({"html": response_html})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')  # 요청에서 검색 쿼리 가져오기

    if not query:
        return jsonify({"error": "검색어가 필요합니다."}), 400

    try:
        # MongoDB에서 검색 수행
        results = data_collection.find({
            "$or": [
                {"filename": {"$regex": query, "$options": "i"}},
                {"ocr_text": {"$regex": query, "$options": "i"}},
                {"summary": {"$regex": query, "$options": "i"}},
                {"formatted_data": {"$regex": query, "$options": "i"}},
            ]
        })

        search_results = []
        for result in results:
            # GridFS에서 이미지 가져오기
            image_data = fs.get(result['image_id']).read()  # GridFS에서 이미지 읽기
            image_base64 = base64.b64encode(image_data).decode('utf-8')  # Base64 인코딩
            image_url = f"data:image/jpeg;base64,{image_base64}"  # 이미지 URL 생성

            # 결과에 요약, 날짜, 이미지 URL 추가
            search_results.append({
                "filename" : result['filename'],
                "summary": result['summary'],
                "upload_date": result['upload_date'].strftime("%Y-%m-%d %H:%M:%S"),  # 날짜 형식 변환
                "image_url": image_url
            })

        return jsonify({"results": search_results})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
