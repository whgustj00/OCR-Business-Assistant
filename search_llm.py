from flask import Blueprint, request, jsonify
from models import data_collection, call_gpt_api
from sentence_transformers import SentenceTransformer, util
import os
import json

search_llm = Blueprint('search_llm', __name__)

# 임베딩 모델 로드 (적절한 모델 선택)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')


def generate_query_embedding(query):
    """검색 쿼리의 임베딩 생성 함수"""
    return embedding_model.encode(query)


def retrieve_similar_documents(query_embedding, threshold=0.5, top_k=5):
    """MongoDB에서 유사한 문서 검색"""
    # 모든 문서 임베딩을 가져오기
    documents = list(data_collection.find({}, {"_id": 1, "filename": 1, "ocr_text": 1, "summary": 1}))
    results = []

    for doc in documents:
        text = doc.get("ocr_text", "") or doc.get("summary", "")
        if text:
            # 각 문서의 임베딩 생성
            doc_embedding = embedding_model.encode(text)
            similarity_score = util.cos_sim(query_embedding, doc_embedding).item()

            # 유사도가 임계값을 넘는 경우 결과에 추가
            if similarity_score >= threshold:
                results.append({
                    "document_id": str(doc["_id"]),
                    "filename": doc["filename"],
                    "similarity_score": similarity_score,
                    "text": text
                })

    # 유사도에 따라 상위 K개의 문서를 정렬
    results = sorted(results, key=lambda x: x["similarity_score"], reverse=True)[:top_k]
    return results


@search_llm.route('/search_llm', methods=['GET'])
def search_llm_route():
    query = request.args.get('query', '')

    if not query:
        return jsonify({"error": "검색어가 필요합니다."}), 400

    try:
        # 쿼리 임베딩 생성
        query_embedding = generate_query_embedding(query)

        # 유사한 문서 검색
        similar_docs = retrieve_similar_documents(query_embedding)

        if not similar_docs:
            return jsonify({"message": "검색 결과가 없습니다."})

        # 유사한 문서를 결합하여 GPT에 전달할 텍스트 생성
        combined_text = "\n\n".join([doc["text"] for doc in similar_docs])

        # GPT API로 요약 및 응답 생성
        response_payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": f"다음 문서와 유사한 검색 결과를 요약하고 추가 정보가 있다면 제공해줘:\n\n{combined_text}"
                }
            ],
            "max_tokens": 200
        }

        # GPT API 호출
        gpt_response = call_gpt_api(response_payload)
        
        # 최종 결과 구성
        search_results = {
            "query": query,
            "results": similar_docs,
            "summary": gpt_response
        }

        return jsonify(search_results)

    except Exception as e:
        print(f"Error during LLM search: {str(e)}")
        return jsonify({"error": "검색 처리 중 오류가 발생했습니다."}), 500
