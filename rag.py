from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from models import data_collection, api_key
from langchain.schema import Document
from datetime import datetime
from flask import Blueprint, request, jsonify

rag = Blueprint('rag', __name__)

# 데이터 로딩 함수
def load_from_data_collection():
    documents = []
    for doc in data_collection.find():
        page_content = doc.get('ocr_text')
        upload_date = doc.get('upload_date')
        filename = doc.get('filename')

        if isinstance(upload_date, datetime):
            upload_date = upload_date.isoformat()
        
        metadata = {"upload_date": upload_date, "filename": filename}
        documents.append(Document(page_content=page_content, metadata=metadata))
    return documents

# Chroma 벡터 저장소 생성 함수
def create_chroma_index_from_data_collection():
    documents = load_from_data_collection()
    embeddings_model = OpenAIEmbeddings(openai_api_key=api_key)
    chroma_db = Chroma.from_documents(documents, embeddings_model)
    return chroma_db

# 쿼리 처리 및 검색 함수
def query_data_collection(query):
    chroma_db = create_chroma_index_from_data_collection()

    openai = ChatOpenAI(
        model_name="gpt-4o-mini",
        openai_api_key=api_key,
        streaming=True,
        callbacks=[StreamingStdOutCallbackHandler()],
        temperature=0
    )

    qa = RetrievalQA.from_chain_type(
        llm=openai,
        chain_type="stuff",
        retriever=chroma_db.as_retriever(search_type="mmr", search_kwargs={'k': 3, 'fetch_k': 10}),
        return_source_documents=True
    )

    result = qa(query)
    return result

@rag.route('/rag', methods=['GET'])
def rag_route():
    query = request.args.get('query', type=str)
    print(f"Received query: {query}")  # 쿼리 로그 확인

    if not query:
        return jsonify({"error": "Query parameter is missing"}), 400

    try:
        result = query_data_collection(query)
        
        # 문서 내용과 메타데이터가 반환될 수 있도록 변환
        formatted_results = []
        for doc in result['source_documents']:
            formatted_results.append({
                "filename": doc.metadata.get("filename", "Unknown filename"),  # filename 필드 추가
                "upload_date": doc.metadata.get("upload_date", "Unknown date"),  # upload_date 필드 추가
                "page_content": doc.page_content,
                "metadata": doc.metadata
            })

        # 결과 출력
        print("Formatted Results:", formatted_results)
        print("Answer:", result.get('result', 'No result found'))

        return jsonify({
            "results": result.get('result', 'No result found'),  # 'result'가 없을 경우 기본값 설정
            "sources": formatted_results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500