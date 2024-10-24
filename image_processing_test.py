from PIL import Image, ImageEnhance, ImageFilter

def preprocess_image(image):
    """이미지 전처리 함수: 대비 조정 및 해상도 향상"""
    # 1. 흑백 변환
    image = image.convert("L")  # 그레이스케일로 변환

    # 2. 대비 증가
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)  # 대비 증가 (값 조정 가능)

    # # 4. 이진화
    # threshold = 128  # 이진화 임계값 조정
    # image = image.point(lambda p: 255 if p > threshold else 0)

    # 5. 해상도 향상
    image = image.resize((image.width * 7, image.height * 7), Image.LANCZOS)  # 해상도 향상

    # 6. 선명도 향상
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(0)  # 선명도 증가 (값 조정 가능)
    return image

if __name__ == "__main__":
    # 이미지 테스트
    input_image_path = "media/감사보고서.png"  # 입력 이미지 경로
    output_image_path = "processed image_test/output_image.png"  # 출력 이미지 경로

    # 이미지 열기
    try:
        image = Image.open(input_image_path)
        # 이미지 전처리 수행
        processed_image = preprocess_image(image)
        # 처리된 이미지 저장
        processed_image.save(output_image_path)
        print(f"Processed image saved as {output_image_path}")
    except Exception as e:
        print(f"Error processing image: {str(e)}")
