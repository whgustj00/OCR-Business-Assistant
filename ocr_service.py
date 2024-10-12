import requests
import pytesseract
from PIL import Image, ImageFilter, ImageOps
import numpy as np
from transformers import pipeline

# Vision API를 통해 이미지에서 텍스트를 인식
# def gpt_vision_api(file_path):
#     vision_api_url = "https://api.openai.com/v1/images/generations"  # Vision API의 URL
#     headers = {
#         "Authorization": "",
#         "Content-Type": "application/json"
#     }

#     with open(file_path, 'rb') as file:
#         response = requests.post(vision_api_url, headers=headers, files={"file": file})

#     if response.status_code == 200:
#         data = response.json()
#         ocr_text = data['ocr_text']  # Vision API에서 인식한 텍스트
#         return ocr_text
#     else:
#         return "Vision 처리 실패"

# 이미지 전처리 함수
def preprocess_image(file_path):
    img = Image.open(file_path)

    # 1. 흑백으로 변환
    img = img.convert("L")

    # 2. 노이즈 제거를 위한 블러 적용
    img = img.filter(ImageFilter.MedianFilter(size=3))

    # 3. 이진화 (Adaptive Thresholding 사용)
    img = img.point(lambda x: 255 if x > 128 else 0, '1')

    # 4. 크기 조정 (필요에 따라)
    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)

    return img

# Tesseract를 통해 이미지에서 텍스트를 인식
def tesseract_ocr(file_path):
    # Tesseract 실행 경로를 설정합니다 (Windows 사용자)
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # 자신의 Tesseract 설치 경로로 변경

    # 이미지를 열고 OCR 처리
    img = preprocess_image(file_path)
    ocr_text = pytesseract.image_to_string(img, lang='kor+eng')  # 언어 설정: 'kor'는 한국어
    return ocr_text

# # GPT API를 통해 텍스트 요약
# def gpt_summary_api(text):
#     summary_api_url = "https://api.openai.com/v1/completions"  # GPT 요약 API의 URL
#     headers = {
#         "Authorization": "",
#         "Content-Type": "application/json"
#     }

#     data = {
#         "model": "gpt-4o-mini",  # 사용할 모델
#         "prompt": f"다음 내용을 요약해 주세요: {text}",
#         "max_tokens": 100  # 요약의 최대 토큰 수
#     }

#     response = requests.post(summary_api_url, headers=headers, json=data)

#     if response.status_code == 200:
#         summary = response.json()['choices'][0]['text'].strip()  # 요약된 텍스트
#         return summary
#     else:
#         return "요약 처리 실패"
# 요약 파이프라인 생성
summarizer = pipeline("summarization")

def summarize_text(text):
    # 입력 텍스트의 길이를 체크하고 필요한 경우 분할
    max_input_length = 1024  # 모델에 따라 입력 길이가 다를 수 있음
    if len(text.split()) > max_input_length:
        # 입력 텍스트가 너무 긴 경우, 모델이 처리할 수 있는 길이로 나눔
        text = text[:max_input_length]

    # 요약 생성
    summary = summarizer(text, max_length=150, min_length=30, do_sample=False)
    return summary[0]['summary_text']


summary = summarize_text(summarizer)
print("Summary:", summary)
# 최종적으로 이미지에서 텍스트를 추출하고 요약하는 함수
def process_document(file_path):
    ocr_text = tesseract_ocr(file_path)
    if "실패" not in ocr_text:
        summary = summarize_text(ocr_text) 
        print("OCR Text:", ocr_text)  # OCR 결과 출력
        print("Summary:", summary)      # 요약 결과 출력
    else:
        print("OCR 실패:", ocr_text)

# 사용 예시
file_path = "123.jpg"
process_document(file_path)
# ocr_text, summary = process_document(file_path)
# print("OCR Text:", ocr_text)
# print("Summary:", summary)
