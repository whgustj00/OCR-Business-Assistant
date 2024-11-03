from models import data_collection, api_key, call_gpt_api
import chromadb
import requests
from bson import ObjectId
from datetime import datetime
import pytz

collection_name = "ocr-vector"

# Chroma 클라이언트 설정
chroma_client = chromadb.PersistentClient(path="chroma_data")

# 컬렉션 생성 또는 가져오기
collection = chroma_client.get_or_create_collection(name=collection_name)
print(chroma_client.list_collections())

def generate_embedding(text):
    """OpenAI API를 사용하여 텍스트 임베딩 생성""" 
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "input": text,
        "model": "text-embedding-ada-002",
        "encoding_format": "float"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # 응답 오류가 있는 경우 예외 발생
        embedding = response.json()
        return embedding['data'][0]['embedding']  # 임베딩 값 반환
    
    except Exception as e:
        print(f"임베딩 처리 중 오류 발생: {str(e)}")
        return None

def save_document(upload_id):
    """문서를 컬렉션에 저장"""
    original_doc = data_collection.find_one({"upload_id": upload_id})
    if not original_doc:
        print("문서를 찾을 수 없습니다.")
        return

    ocr_text = original_doc.get("ocr_text")

    # 텍스트 임베딩 생성
    ocr_embedding = generate_embedding(ocr_text)

    if ocr_embedding is not None:
        # 문서 저장
        collection.add(
            documents=[ocr_text],
            embeddings=[ocr_embedding],
            metadatas=[{"upload_id": upload_id}],
            ids=[str(original_doc["_id"])],
        )
        print(f"Document with upload_id {upload_id} saved successfully.")
    else:
        print("임베딩 생성 실패")

def query_documents(query_text):
    """쿼리 텍스트로 유사 문서 검색"""
    query_embedding = generate_embedding(query_text)
    if query_embedding is None:
        print("쿼리 임베딩 생성 실패")
        return
    
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=2  # 결과 수
        )
        print("Search results:", results)
        return(results)
    except Exception as e:
        print(f"Chroma 검색 중 오류 발생: {str(e)}")

def generate_query(query_text):
    """GPT API를 사용하여 자연어 쿼리를 특정 쿼리로 변환"""
    try:
        # 현재 한국 표준시(KST) 시간 가져오기
        now = datetime.now(pytz.timezone('Asia/Seoul'))
        datenow = now.strftime("%Y년 %m월 %d일 %H:%M:%S")

        # 쿼리문 생성 페이로드
        query_payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"다음 내용을 ChromaDB 쿼리 작성을 위해 쉽게 임베딩 할 수 있도록 개조식으로 표현해줘. "
                        f"시간 관련 내용이 있다면 {datenow} 현재 시간을 참고하여 절대 시각으로 표현해줘. "
                        f"예를 들어, '지난달 문서'는 '2024년 10월에 업로드된 문서'로 변환될 수 있어. "
                        f"최종 텍스트 이외에 출력 금지 :\n\n{query_text}"
                        )
                }
            ],
            "max_tokens": 100
        }

        # GPT-4o mini API로 요약 요청
        query = call_gpt_api(query_payload)
        return query
    
    except Exception as e:
        print(f"쿼리 변환 중 오류 발생: {str(e)}")
        return None

def generate_answer(results, user_query):
    """검색된 문서와 사용자 질문을 바탕으로 GPT API를 사용하여 답변 생성"""
    if not results or 'documents' not in results or not results['documents']:
        print("문서가 없습니다.")
        return None

    # 문서 내용을 결합
    documents = results['documents']  # 문서 데이터 가져오기
    # 각 문서에서 내용을 결합
    combined_text = "\n".join(["\n".join(doc) for doc in documents])  # 각 문서의 내용 결합

    print('\n문서 내용:', combined_text)

    # GPT API에 요청할 페이로드 생성
    response_payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": (
                    f"다음 정보를 바탕으로 사용자의 질문에 대답해줘:\n\n"
                    f"{combined_text}\n\n"
                    f"질문: {user_query}"
                )
            }
        ],
        "max_tokens": 100  # 필요한 길이 설정
    }

    # GPT API 호출
    answer = call_gpt_api(response_payload)
    return answer

if __name__ == "__main__":
    # 테스트할 upload_id를 입력하세요
    upload_id = "672265dd988431d78fc1efdf"  # 예시 업로드 ID로 대체하세요
    # save_document(upload_id)  # 문서 저장
    query = generate_query("지난달 업로드한 헌혈 문서")
    print(query)
    results = query_documents(query)  # 쿼리 검색
    user_question="봉사를 한 사람이 누구고 주소가 어떻게 돼?"
    answer = generate_answer(results, user_question)
    print("GPT 응답 : ", answer)

    