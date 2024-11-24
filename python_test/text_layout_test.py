import json

def load_ocr_result(json_path):
    """JSON 파일에서 OCR 결과를 로드하는 함수"""
    with open(json_path, 'r', encoding='utf-8') as json_file:
        return json.load(json_file)

def extract_text_with_layout(ocr_result):
    """OCR 결과에서 원래 문서 레이아웃을 최대한 유지하며 텍스트를 추출하는 함수"""
    extracted_text = []
    previous_x_end = None  # 이전 단어의 x 끝 좌표
    previous_y_bottom = None  # 이전 단어의 y 하단 좌표

    for image in ocr_result.get('images', []):
        # 각 필드에서 텍스트 추출
        for field in image.get('fields', []):
            # 텍스트 정보와 lineBreak 값 추출
            text = field.get('inferText', '')  # 텍스트 내용
            current_x_start = field['boundingPoly']['vertices'][0]['x']  # 현재 단어의 좌상단 x좌표
            current_x_end = field['boundingPoly']['vertices'][1]['x']  # 현재 단어의 우상단 x좌표
            current_y_top = field['boundingPoly']['vertices'][1]['y']  # 현재 단어의 우상단 y좌표
            current_y_bottom = field['boundingPoly']['vertices'][2]['y']  # 현재 단어의 우하단 y좌표
            line_break = field.get('lineBreak', False)  # lineBreak 여부

            # 개행 전 수직 간격 체크
            if previous_y_bottom is not None and not line_break:
                y_diff = current_y_top - previous_y_bottom
                # 수직 간격이 일정 값 이상일 경우 개행
                if y_diff > 50:
                    extracted_text.append('\n')  # 개행 추가

            # 이전 단어의 끝 x 값과 현재 단어의 첫 x 값 차이 계산
            if previous_x_end is not None:
                x_diff = current_x_start - previous_x_end
                # x 차이가 클 경우 탭 추가
                if x_diff > 70:
                    extracted_text.append('\t')  # 탭 추가

            # 텍스트 추가 (lineBreak가 True일 경우 공백 추가하지 않음)
            if line_break:
                extracted_text.append(text.strip())  # 공백을 추가하지 않고 텍스트만 추가
                extracted_text.append('\n')  # 개행 추가
            else:
                extracted_text.append(text + ' ')  # 공백 추가 후 텍스트 추가

            # 이전 단어의 끝 x 값 갱신
            previous_x_end = current_x_end
            previous_y_bottom = current_y_bottom

    return ''.join(extracted_text).strip()


if __name__ == '__main__':
    json_path = './ocr_result_json/ocr_result.json'  # JSON 파일 경로
    ocr_result = load_ocr_result(json_path)  # OCR 결과 로드
    formatted_text = extract_text_with_layout(ocr_result)  # 개행 로직 적용
    print(formatted_text)  # 최종 텍스트 출력
    # for image in ocr_result.get("images", []):  # "images" 목록 탐색
    #     for field in image.get("fields", []):  # 각 "fields" 항목 탐색
    #         print(field.get("inferText", " "))  # "inferText" 값 출력
