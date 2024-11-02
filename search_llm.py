from flask import Blueprint, request, jsonify
from models import call_gpt_api, data_collection
import json

search_llm = Blueprint('search_llm', __name__)

@search_llm.route('/search_llm', methods=['GET'])
def search_llm_route():
    user_query = request.args.get('query', '')

    if not user_query:
        return jsonify({"error": "검색어가 필요합니다."}), 400

    try:
        # GPT API를 통해 MongoDB 쿼리문 생성
        search_payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": f"다음 요청에 대한 MongoDB 쿼리문을 작성해줘: '{user_query}'. 반환 형식은 JSON이어야 하며, 올바른 쿼리문을 작성해야 합니다."
                }
            ],
            "max_tokens": 300
        }

        # GPT API 호출
        gpt_res = call_gpt_api(search_payload)
        print("GPT API 응답:", gpt_res)  # GPT 응답을 출력하여 확인

        # 응답 형식이 JSON 형식인지 확인하고 MongoDB 쿼리 추출
        if not isinstance(gpt_res, dict) or 'choices' not in gpt_res:
            print("GPT API 응답 형식이 잘못되었습니다.")
            return jsonify({"error": "GPT API 응답 형식이 잘못되었습니다."}), 500

        # 'query' 키로 MongoDB 쿼리 가져오기
        gpt_query = gpt_res['choices'][0]['message']['content'].strip()
        mongo_query = json.loads(gpt_query)
        
        # 'query' 키가 포함된 경우 실제 쿼리로 사용
        if 'query' in mongo_query:
            mongo_query = mongo_query['query']

        print("MongoDB 쿼리:", mongo_query)

        # MongoDB에서 검색 수행
        results = list(data_collection.find(mongo_query))
        print("검색 결과:", results)

        # 검색 결과에서 문서의 정보를 추출
        documents = []
        for result in results:
            documents.append({
                "filename": result['filename'],
                "summary": result['summary'],
                "upload_date": result['upload_date'].strftime("%Y-%m-%d %H:%M:%S"),
                "image_id": result.get('image_id', '')  # image_id가 없을 경우를 대비
            })

        return jsonify({"results": documents})

    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {str(e)}")  # JSON 오류 상세 출력
        return jsonify({"error": f"쿼리문이 올바르지 않습니다: {str(e)}"}), 400
    except Exception as e:
        print(f"Unhandled Error: {str(e)}")  # 예상치 못한 오류 상세 출력
        return jsonify({"error": str(e)}), 500
