from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
from PIL import Image, ImageEnhance
from transformers import pipeline

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

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "파일이 없습니다."}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "파일 이름이 비어있습니다."}), 400

        # 파일을 메모리에서 직접 처리 (저장하지 않음)
        img = Image.open(file)

        # 이미지 전처리 적용
        img = preprocess_image(img)

        # OCR 수행
        ocr_text = perform_ocr(img)

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
    
        # return jsonify({"ocr_text": ocr_text, "summary": summary})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
