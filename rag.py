from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from models import data_collection, api_key
from langchain.schema import Document
from datetime import datetime
from flask import Blueprint, request, jsonify
import os

rag = Blueprint('rag', __name__)

# Chroma 데이터 저장 디렉토리 설정
CHROMA_DIR = "/chroma_data"

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

# Chroma 벡터 저장소 생성 또는 로드 함수
def get_or_create_chroma_index():
    # Chroma 데이터 디렉토리가 존재하고 비어 있지 않으면 로드
    if os.path.exists(CHROMA_DIR) and os.listdir(CHROMA_DIR):
        embeddings_model = OpenAIEmbeddings(openai_api_key=api_key)
        chroma_db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings_model)
    else:
        # 없을 경우 새로 생성 및 저장
        documents = load_from_data_collection()
        if not documents:
            raise ValueError("No documents found in the data collection to index.")
        
        embeddings_model = OpenAIEmbeddings(openai_api_key=api_key)
        chroma_db = Chroma.from_documents(documents, embeddings_model, persist_directory=CHROMA_DIR)
        chroma_db.persist()  # 데이터를 디스크에 저장
    return chroma_db

# 쿼리 처리 및 검색 함수
def query_data_collection(query):
    chroma_db = get_or_create_chroma_index()

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
    except ValueError as e:
        return jsonify({"error": str(e)}), 500

    # 'result'와 'source_documents'가 모두 유효한 경우에만 처리
    answer = result.get('result')
    source_documents = result.get('source_documents')

    if not answer or not source_documents or not isinstance(source_documents, list) or len(source_documents) == 0:
        return jsonify({"error": "Incomplete response generated. Please try again."}), 500

    # 문서 내용과 메타데이터가 반환될 수 있도록 변환
    formatted_results = []
    for doc in source_documents:
        formatted_results.append({
            "filename": doc.metadata.get("filename", "Unknown filename"),
            "upload_date": doc.metadata.get("upload_date", "Unknown date"),
            "page_content": doc.page_content,
            "metadata": doc.metadata,
        })

    # 결과 출력
    print("Formatted Results:", formatted_results)
    print("Answer:", answer)

    return jsonify({
        "results": answer,  # 'result'는 항상 유효함
        "sources": formatted_results,  # 'sources'도 항상 유효함
    })
