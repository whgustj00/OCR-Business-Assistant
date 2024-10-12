from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
from PIL import Image, ImageEnhance
from transformers import pipeline
import fitz  # PyMuPDF

app = Flask(__name__)
CORS(app)

# Tesseract 경로 설정
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Hugging Face의 텍스트 요약 모델 로드
summarizer = pipeline("summarization")

def preprocess_image(image):
    """이미지 전처리 함수: 대비 조정 및 해상도 향상"""
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)  # 대비 증가
    image = image.resize((image.width * 2, image.height * 2))  # 해상도 향상
    return image

def perform_ocr(image):
    """OCR 수행 (한글과 영어 텍스트 인식)"""
    ocr_text = pytesseract.image_to_string(image, lang='kor+eng', config='--psm 6')
    return ocr_text.strip()  # 공백 제거

def summarize_text(text):
    """텍스트 요약"""
    if len(text.split()) < 50:
        return "텍스트가 너무 짧아 요약할 수 없습니다."

    # 요약 모델에 맞게 입력 텍스트 길이 조정
    max_input_length = 512  # Hugging Face 모델에 따라 조정 필요
    text = text[:max_input_length]

    summary = summarizer(text, max_length=150, min_length=30, do_sample=False)
    return summary[0]['summary_text']

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
                        img = preprocess_image(img)  # 이미지 전처리
                        ocr_text += perform_ocr(img) + "\n"  # OCR 수행
            else:
                for img in images:
                    img = preprocess_image(img)  # 이미지 전처리
                    ocr_text += perform_ocr(img) + "\n"  # OCR 수행
        else:
            # JPG, PNG 파일 처리
            img = Image.open(file)
            img = preprocess_image(img)  # 이미지 전처리
            ocr_text = perform_ocr(img)  # OCR 수행

        # 텍스트 요약
        summary = summarize_text(ocr_text)

        # HTML 레이아웃으로 텍스트 구성
        response_html = f"""
        <div>
            <h2>OCR 결과</h2>
            <pre>{ocr_text}</pre>
            <h2>요약 결과</h2>
            <pre>{summary}</pre>
        </div>
        """

        return jsonify({"html": response_html})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
