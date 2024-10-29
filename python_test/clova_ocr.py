import requests
import uuid
import time
import json
import os
from dotenv import load_dotenv

load_dotenv()  # 환경 변수 로드

secret_key = os.getenv("api")
api_url = 'https://mfpxhmwxm2.apigw.ntruss.com/custom/v1/35426/9ce749152d8f697b1dde8d90136d7443f3ee7b7038574145809c266e3f416d80/general'

def perform_ocr(image_file, api_url, secret_key):
    """네이버 클로바 OCR을 사용하여 이미지에서 텍스트를 추출하는 함수"""
    try:
        # 요청 JSON 구성
        request_json = {
            'images': [
                {
                    'format': 'png',
                    'name': 'demo'
                }
            ],
            'requestId': str(uuid.uuid4()),
            'version': 'V2',
            'timestamp': int(round(time.time() * 1000))
        }

        payload = {'message': json.dumps(request_json).encode('UTF-8')}
        files = [
            ('file', open(image_file, 'rb'))
        ]
        headers = {
            'X-OCR-SECRET': secret_key
        }

        # POST 요청
        response = requests.post(api_url, headers=headers, data=payload, files=files)

        # 응답 처리
        if response.status_code == 200:
            ocr_result = response.json()
            extracted_text = []
            previous_y = None
            
            for image in ocr_result.get('images', []):
                for field in image.get('fields', []):
                    current_y = field['boundingPoly']['vertices'][0]['y']
                    text = field.get('inferText', '') + ' '

                    # y값이 같으면 같은 줄에 추가, 다르면 줄바꿈
                    if previous_y is None or abs(previous_y - current_y) > 3:  # 5px 이상 차이가 나면 줄바꿈
                        extracted_text.append('\n' + text)
                    elif previous_y is None or abs(previous_y - current_y) > 6:  # 5px 이상 차이가 나면 한번 더 줄바꿈
                        extracted_text.append('\n\n' + text)
                    else:
                        extracted_text.append(text)

                    previous_y = current_y
            
            return ''.join(extracted_text).strip()  # 추출한 텍스트 반환
        else:
            print(f"API 요청 실패: {response.status_code}, {response.text}")
            return "OCR 실패: API 요청 오류 발생"
        

    except Exception as e:
        print(f"OCR 처리 중 오류 발생: {str(e)}")
        return "OCR 실패: 오류 발생"

# 사용 예
result = perform_ocr('media/111.png', api_url, secret_key)
print(result)
