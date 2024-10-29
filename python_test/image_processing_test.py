from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

def preprocess_image(image):
    """이미지 전처리 함수: 대비 조정 및 해상도 향상"""
    # 1. 흑백 변환
    image = image.convert("L")  # 그레이스케일로 변환

    # 2. 대비 증가
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(3)  # 대비 증가 (값 조정 가능)

    # # 3. 이진화 (Adaptive Thresholding)
    # image_array = np.array(image)
    # threshold_value = image_array.mean()  # 평균값을 임계값으로 사용
    # binary_image = (image_array > threshold_value) * 255  # 이진화
    # image = Image.fromarray(binary_image.astype(np.uint8))

    # 5. 해상도 향상
    resize_num = 2
    image = image.resize((image.width * resize_num, image.height * resize_num), Image.LANCZOS)  # 해상도 향상

    # 6. 선명도 향상
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(3)  # 선명도 증가 (값 조정 가능)

    return image

if __name__ == "__main__":
    # 이미지 테스트
    input_image_path = "media/111.PNG"  # 입력 이미지 경로
    output_image_path = "python_test/processed_image_test/output_image.png"  # 출력 이미지 경로

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
