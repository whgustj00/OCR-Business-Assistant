from flask import Blueprint, request, jsonify
from models import get_ocr_text_from_upload, get_ocr_text_from_data
import Levenshtein

accuracy = Blueprint('accuracy', __name__)

@accuracy.route('/accuracy', methods=['POST'])
def accuracy_route():
    data = request.json
    upload_id = data.get('upload_id')  # 요청 본문에서 upload_id 받기

    if not upload_id:
        return jsonify({"error": "upload_id가 필요합니다."}), 400

    # MongoDB에서 원본 텍스트 및 수정된 텍스트 가져오기
    original_text = get_ocr_text_from_upload(upload_id)
    ocr_text = get_ocr_text_from_data(upload_id)

    if original_text is None or ocr_text is None:
        return jsonify({"error": "텍스트를 찾을 수 없습니다."}), 404

    # Levenshtein 거리 계산을 통한 정확도 계산
    distance = Levenshtein.distance(original_text, ocr_text)
    max_len = max(len(original_text), len(ocr_text))
    accuracy = (1 - distance / max_len) * 100

    return jsonify({"accuracy": accuracy, "original_text" : original_text, "ocr_text": ocr_text})

