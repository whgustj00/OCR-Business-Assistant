from flask import Blueprint, request, jsonify
from models import data_collection, call_gpt_api
import chromadb
from bson import ObjectId
import os

search_llm = Blueprint('search_llm', __name__)

# Chroma 클라이언트 설정 (데이터 디렉토리 지정)
chroma_client = chromadb.Client()

def generate_embedding(text):
    """GPT-4o mini API를 사용하여 텍스트 임베딩 생성"""
    try:
        # 텍스트 임베딩 요청 페이로드
        embedding_payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": f"다음 텍스트의 임베딩을 제공해줘:\n\n{text}"
                }
            ]
        }

        # GPT-4o mini API로 임베딩 요청
        embedding = call_gpt_api(embedding_payload)
        return embedding

    except Exception as e:
        print(f"임베딩 처리 중 오류 발생: {str(e)}")
        return "임베딩 실패: 오류 발생"

@search_llm.route('/search_llm', methods=['POST'])
def search_llm_route():
    # 사용자의 요청 데이터 가져오기
    data = request.json
    upload_id = data.get("upload_id")

    print(f"Received upload_id: {upload_id}")  # 요청 ID 출력

    # MongoDB에서 해당 문서 가져오기
    original_doc = data_collection.find_one({"upload_id": upload_id})
    if not original_doc:
        return jsonify({"error": "문서를 찾을 수 없습니다."}), 404

    print("Document found:", original_doc)  # 찾은 문서 정보 출력

    # OCR 텍스트 추출
    ocr_text = original_doc.get("ocr_text")
    if not ocr_text:
        return jsonify({"error": "OCR 텍스트가 없습니다."}), 404

    print("Extracted OCR text:", ocr_text)  # OCR 텍스트 출력

    # 임베딩 생성
    embedding = generate_embedding(ocr_text)
    print("Generated embedding:", embedding)  # 생성된 임베딩 출력

    # Chroma에서 유사한 문서 검색
    results = chroma_client.search(query=embedding, n_results=5)  # 5개의 유사 문서 반환
    print("Search results:", results)  # 검색 결과 출력
    
    # 검색 결과를 기반으로 MongoDB에서 관련 문서들 조회
    related_docs = []
    for result in results:
        doc_id = result['document_id']
        doc = data_collection.find_one({"_id": ObjectId(doc_id)})
        if doc:
            related_docs.append({
                "filename": doc["filename"],
                "summary": doc.get("summary"),
                "formatted_data": doc.get("formatted_data")
            })

    print("Related documents:", related_docs)  # 관련 문서 출력

    # 결과 반환
    return jsonify({"related_docs": related_docs})
