from flask import Blueprint, request, jsonify
from models import upload_collection, save_db_data
from bson import ObjectId
from models import summarize_text, format_data, parse_formatted_data

summarize_and_format = Blueprint('summarize_and_format', __name__)

@summarize_and_format.route('/summarize_and_format', methods=['POST'])
def summarize_and_format_route():
    try:
        data = request.json
        ocr_text = data.get('ocr_text', '')
        upload_id = data.get('upload_id', '')  # 업로드 ID 추가

        if not ocr_text:
            return jsonify({"error": "OCR 텍스트가 필요합니다."}), 400
        if not upload_id:
            return jsonify({"error": "업로드 ID가 필요합니다."}), 400

        summary = summarize_text(ocr_text)
        formatted_data_str = format_data(ocr_text)
        formatted_data = parse_formatted_data(formatted_data_str)

        # upload 컬렉션에서 정보 가져오기
        upload_info = upload_collection.find_one({"_id": ObjectId(upload_id)})
        if upload_info:
            filename = upload_info['filename']
            image_id = upload_info['image_id']
            upload_date = upload_info['upload_date']

            # data 컬렉션에 데이터 저장
            save_db_data(upload_id, filename, ocr_text, summary, formatted_data, upload_date, image_id)

            response_html = f"""
            <div>
                <h3>요약 결과</h3>
                <pre>{summary}</pre>
                <h3>정형화된 데이터</h3>
                <pre>{formatted_data_str}</pre>
            </div>
            """

            return jsonify({"html": response_html})

    except Exception as e:
        print(f"Error in summarize_and_format: {str(e)}")
        return jsonify({"error": str(e)}), 500
