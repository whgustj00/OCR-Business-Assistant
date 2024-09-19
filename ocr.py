import pytesseract
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import fonts
from reportlab.lib.units import inch
import cv2
import numpy as np

# Tesseract 경로 설정 (Windows일 경우)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 한글 폰트 등록 (폰트 경로를 지정)
#pdfmetrics.registerFont(TTFont('gulim', 'C:\Windows\Fonts\gulim.ttf'))

# 이미지 파일을 열어서 텍스트 추출
image = Image.open('111.png')
custom_config = r'--oem 3 --psm 3'

# large_image = image.resize((image.width * 3, image.height * 3), Image.LANCZOS)

text = pytesseract.image_to_string(image, lang='kor')

print(text)

# PDF 생성
#pdf_file = "output_file.pdf"
#pdf = canvas.Canvas(pdf_file, pagesize=letter)
#width, height = letter
#
## 텍스트를 PDF에 추가
#pdf.setFont("gulim", 12)
#text_lines = text.split('\n')
#y = height - 40  # 상단 여백 설정
#
#for line in text_lines:
#    pdf.drawString(30, y, line)
#    y -= 14  # 줄 간격
#
#pdf.save()
#print(f"PDF 생성 완료: {pdf_file}")