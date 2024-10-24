import requests
from PIL import Image, ImageEnhance
import pytesseract
from transformers import pipeline

# Tesseract OCR 설정
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Tesseract 경로 설정

# 요약 파이프라인 생성
summarizer = pipeline("summarization")

def preprocess_image(image_path):
    """이미지 전처리 함수: 대비 조정 및 해상도 향상"""
    image = Image.open(image_path)

    # 이미지 대비 조정
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)  # 대비 증가

    # 이미지 크기 조정 (필요 시)
    image = image.resize((image.width * 2, image.height * 2))  # 해상도 향상

    return image

def perform_ocr(image):
    """OCR 수행 함수"""
    ocr_text = pytesseract.image_to_string(image, lang='kor+eng')  # 한글과 영어 인식
    return ocr_text

def summarize_text(text):
    """텍스트 요약 함수"""
    # 텍스트가 너무 짧은 경우 요약을 하지 않음
    if len(text.split()) < 50:  # 요약할 텍스트가 50단어 미만일 경우
        return "텍스트가 너무 짧아 요약할 수 없습니다."

    try:
        max_input_length = 1024  # 모델에 따라 입력 길이가 다를 수 있음
        if len(text.split()) > max_input_length:
            text = text[:max_input_length]

        # 요약 생성
        summary = summarizer(text, max_length=150, min_length=30, do_sample=False)

        # 요약이 정상적으로 생성되었는지 확인
        if len(summary) > 0 and 'summary_text' in summary[0]:
            return summary[0]['summary_text']
        else:
            return "요약 처리 실패"

    except IndexError:
        return "요약 처리 중 오류 발생 (IndexError)"
    except Exception as e:
        return f"요약 처리 중 오류 발생: {str(e)}"

def main(image_path):
    # 이미지 전처리
    processed_image = preprocess_image(image_path)

    # OCR 수행
    ocr_text = perform_ocr(processed_image)
    print("OCR Text:", ocr_text)

    # 텍스트 요약
    summary = summarize_text(ocr_text)
    print("Summary:", summary)

# 사용 예시
image_path = '111.png'  # 이미지 파일 경로 설정
main(image_path)
