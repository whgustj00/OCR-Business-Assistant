from flask import Blueprint, request, jsonify
from models import data_collection, fs
import base64

search = Blueprint('search', __name__)

@search.route('/search', methods=['GET'])
def search_route():
    query = request.args.get('query', '')  # 요청에서 검색 쿼리 가져오기

    if not query:
        return jsonify({"error": "검색어가 필요합니다."}), 400

    try:
        # MongoDB에서 검색 수행
        results = data_collection.find({
            "$or": [
                {"filename": {"$regex": query, "$options": "i"}},
                {"ocr_text": {"$regex": query, "$options": "i"}},
                {"summary": {"$regex": query, "$options": "i"}},
                {"formatted_data": {"$regex": query, "$options": "i"}},
            ]
        })

        search_results = []
        for result in results:
            # GridFS에서 이미지 가져오기
            image_data = fs.get(result['image_id']).read()  # GridFS에서 이미지 읽기
            image_base64 = base64.b64encode(image_data).decode('utf-8')  # Base64 인코딩
            image_url = f"data:image/jpeg;base64,{image_base64}"  # 이미지 URL 생성

            # 결과에 요약, 날짜, 이미지 URL 추가
            search_results.append({
                "filename": result['filename'],
                "summary": result['summary'],
                "upload_date": result['upload_date'].strftime("%Y-%m-%d %H:%M:%S"),  # 날짜 형식 변환
                "image_url": image_url
            })

        return jsonify({"results": search_results})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
