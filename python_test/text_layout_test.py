import json

def load_ocr_result(json_path):
    """JSON 파일에서 OCR 결과를 로드하는 함수"""
    with open(json_path, 'r', encoding='utf-8') as json_file:
        return json.load(json_file)

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
                    extracted_text.append('    ')
                elif x_diff > 35:
                    extracted_text.append('  ')
                elif x_diff > 15:
                    extracted_text.append(' ')

            # 텍스트 추가
            extracted_text.append(text)

            # 이전 좌표 업데이트
            previous_y = current_y
            previous_x_end = field['boundingPoly']['vertices'][2]['x']  # 현재 텍스트 박스 하단 x좌표 업데이트

    return ''.join(extracted_text).strip()

if __name__ == '__main__':
    json_path = './ocr_result_json/ocr_result.json'  # JSON 파일 경로
    ocr_result = load_ocr_result(json_path)  # OCR 결과 로드
    formatted_text = extract_text_with_layout(ocr_result)  # 개행 로직 적용
    print(formatted_text)  # 최종 텍스트 출력
