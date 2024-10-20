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
uploads_collection = db['uploads']  # 업로드 파일 컬렉션
structured_data_collection = db['structured_data']  # 정형화된 데이터 컬렉션


def preprocess_image(image):
    """이미지 전처리 함수: 대비 조정 및 해상도 향상"""
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
                            "text": "다음 이미지에서 텍스트 그대로 추출 그 외 내용은 출력 금지"
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
                    "content": f"다음 텍스트를 200토큰 안에 요약해줘:\n\n{text}"
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

def process_image(image):
    """이미지를 Base64로 인코딩하고 전처리하는 함수"""
    # 이미지 모드 변환
    if image.mode == 'RGBA':
        image = image.convert('RGB')  # RGBA를 RGB로 변환

    # 이미지를 Base64로 인코딩하여 저장
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # 이미지 전처리
    image = preprocess_image(image)

    return image, image_data


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
        image_data = None  # 이미지를 저장할 변수

        if file.content_type == 'application/pdf':
            # PDF 파일을 이미지로 변환
            images = convert_pdf_to_images(file)

            if pages_to_process:
                for page_number in pages_to_process:
                    if page_number < len(images):  # 페이지 번호 유효성 검사
                        img = images[page_number]

                        # 이미지 처리 및 Base64 인코딩
                        img, image_data = process_image(img)

                        ocr_text += f"=== 페이지 {page_number + 1} ===\n\n"  # 페이지 번호 추가
                        ocr_text += perform_ocr(img) + "\n\n\n"  # OCR 수행 후 결과 구분
            else:
                for i, img in enumerate(images):
                    # 이미지 처리 및 Base64 인코딩
                    img, image_data = process_image(img)

                    ocr_text += f"=== 페이지 {i + 1} ===\n\n"  # 페이지 번호 추가
                    ocr_text += perform_ocr(img) + "\n\n\n"  # OCR 수행 후 결과 구분
        else:
            # JPG, PNG 파일 처리
            img = Image.open(file)
            
            # 이미지 처리 및 Base64 인코딩
            img, image_data = process_image(img)

            ocr_text = perform_ocr(img)  # OCR 수행
            # ocr_text = "123"

        # MongoDB에 업로드된 파일 정보 저장
        result = uploads_collection.insert_one({
            "filename": file.filename,
            "upload_date": datetime.now(),
            "ocr_text": ocr_text,
            "image_data": image_data  # Base64로 인코딩된 이미지 데이터 추가
        })
        print(f"Uploaded file data ID: {result.inserted_id}")  # 추가된 코드

        # 텍스트 요약
        summary = summarize_text(ocr_text)

        # 데이터 정형화
        formatted_data = format_data(ocr_text)

        # summary = "요약 데이터"
        # formatted_data = "정형화 데이터"

        # 정형화된 데이터 MongoDB에 저장
        structured_data_result = structured_data_collection.insert_one({
            "ocr_text": ocr_text,
            "summary": summary,
            "formatted_data": formatted_data,
            "upload_date": datetime.now()
        })
        print(f"Structured data ID: {structured_data_result.inserted_id}")  # 추가된 코드

        # HTML 레이아웃으로 텍스트 구성
        response_html = f"""
        <div>
            <h2>OCR 결과</h2>
            <pre>{ocr_text}</pre>
            <h2>요약 결과</h2>
            <pre>{summary}</pre>
            <h2>정형화된 데이터</h2>
            <pre>{formatted_data}</pre>
        </div>
        """

        return jsonify({"html": response_html})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/search", methods=["GET"])
def search_documents():
    query = request.args.get("query")
    
    if not query:
        return jsonify({"error": "검색어를 입력해야 합니다."}), 400

    # MongoDB에서 모든 정형화된 데이터 검색
    structured_data_list = list(structured_data_collection.find())
    
    # 결과를 저장할 리스트
    results = []
    for data in structured_data_list:
        # 정형화된 데이터에서 텍스트와 요약을 가져옵니다.
        ocr_text = data.get("ocr_text", "")
        summary = data.get("summary", "")
        image_data_id = data.get("image_data")  # 이미지 데이터 ID 가져오기

        # 쿼리가 OCR 텍스트 또는 요약에 포함되어 있는지 확인
        if query.lower() in ocr_text.lower() or query.lower() in summary.lower():
            # 이미지 데이터 검색
            image_data = uploads_collection.find_one({"_id": image_data_id})  # 이미지 데이터 가져오기
            
            image_link = None
            if image_data:
                image_filename = image_data.get("filename")  # filename 필드 가져오기
                image_link = f"/uploads/{image_filename}" if image_filename else None

            results.append({
                "title": f"Document {data['_id']}",
                "summary": summary,
                "downloadLink": f"/path/to/download/{data['_id']}",  # 적절한 다운로드 링크로 수정
                "previewLink": f"/path/to/preview/{data['_id']}",   # 적절한 미리보기 링크로 수정
                "imageLink": image_link  # 이미지 링크 추가
            })

    if not results:
        return jsonify({"message": "검색 결과가 없습니다."}), 404

    return jsonify({"results": results})


if __name__ == '__main__':
    app.run(debug=True)
