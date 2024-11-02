from flask import Blueprint, request, jsonify
from models import data_collection, fs
import base64
from datetime import datetime, timedelta
import pytz

search = Blueprint('search', __name__)

@search.route('/search', methods=['GET'])
def search_route():
    query = request.args.get('query', '').strip()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    print(f"시작 날짜 {start_date}, 끝 날짜 {end_date}")

    if not query:
        return jsonify({"error": "검색어가 필요합니다."}), 400

    try:
        # 키워드 추출 및 정리
        keywords = [word.strip() for word in query.split('+') if word.strip()]

        # 검색 조건 설정
        match_conditions = {
            "$and": [
                {
                    "$or": [
                        {"filename": {"$regex": keyword, "$options": "i"}},
                        {"ocr_text": {"$regex": keyword, "$options": "i"}},
                        {"summary": {"$regex": keyword, "$options": "i"}},
                        {"formatted_data_keys.v": {"$regex": keyword, "$options": "i"}}
                    ]
                } for keyword in keywords
            ]
        }

        # 날짜 조건 추가
        if start_date:
            start_date_dt = datetime.fromisoformat(start_date).replace(tzinfo=pytz.UTC)
            match_conditions["$and"].append({"upload_date": {"$gte": start_date_dt}})

        if end_date:
            end_date_dt = datetime.fromisoformat(end_date).replace(tzinfo=pytz.UTC)
            end_date_dt = end_date_dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            match_conditions["$and"].append({"upload_date": {"$lt": end_date_dt}})

        # Aggregation Pipeline 설정
        pipeline = [
            {"$addFields": {"formatted_data_keys": {"$objectToArray": "$formatted_data"}}},
            {"$unwind": "$formatted_data_keys"},
            {"$match": match_conditions},
            {
                "$group": {
                    "_id": "$_id",
                    "filename": {"$first": "$filename"},
                    "summary": {"$first": "$summary"},
                    "upload_date": {"$first": "$upload_date"},
                    "image_id": {"$first": "$image_id"},
                    "formatted_data": {"$push": "$formatted_data_keys"}
                }
            },
            {
                "$project": {
                    "filename": 1,
                    "summary": 1,
                    "upload_date": 1,
                    "image_id": 1,
                    "formatted_data": 1
                }
            }
        ]

        results = list(data_collection.aggregate(pipeline))

        search_results = []
        for result in results:
            image_url = fetch_image_url(result.get('image_id'))

            search_results.append({
                "filename": result['filename'],
                "summary": result['summary'],
                "upload_date": result['upload_date'].strftime("%Y-%m-%d %H:%M:%S"),
                "image_url": image_url,
                "formatted_data": result['formatted_data']
            })

        return jsonify({"results": search_results})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def fetch_image_url(image_id):
    """Fetch image from GridFS and return base64 URL."""
    if not image_id:
        return None

    try:
        image_data = fs.get(image_id).read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/jpeg;base64,{image_base64}"
    except Exception as e:
        print(f"Image fetch error: {str(e)}")
        return None
