from pymongo import MongoClient
import os
import gridfs
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO

load_dotenv()

# MongoDB Atlas 연결 문자열
MONGO_URI = os.getenv("MONGODB_URL")  # 환경 변수에서 MongoDB URI 가져오기
client = MongoClient(MONGO_URI)
db = client['OCR_DB']  # 데이터베이스 이름
uploads_collection = db['uploads']  # 업로드 파일 컬렉션
data_collection = db['data']  # 정형화된 데이터 컬렉션

# GridFS 인스턴스 생성
fs = gridfs.GridFS(db)

# 이미지 파일 저장 함수
def save_image_to_mongodb(file_path):
    with open(file_path, 'rb') as f:
        file_data = f.read()  # 이미지 파일을 바이너리로 읽기
        file_id = fs.put(file_data, filename=os.path.basename(file_path))  # GridFS에 저장
        print(f"이미지 저장 성공: {file_id}")
        return file_id

# 저장된 이미지 파일 꺼내서 출력하는 함수
def get_image_from_mongodb(file_id):
    file_data = fs.get(file_id)  # GridFS에서 파일 가져오기
    image = Image.open(BytesIO(file_data.read()))  # 이미지를 바이너리에서 PIL 이미지로 변환
    image.show()  # 이미지 출력 (이미지 뷰어로 출력)

# 예시: 로컬 파일을 MongoDB에 저장
image_file_path = './media/123.jpg'  # 이미지 파일 경로
file_id = save_image_to_mongodb(image_file_path)

# 파일 메타데이터를 uploads_collection에 삽입
document = {
    "file_id": file_id,  # 저장된 파일의 ID
    "file_name": os.path.basename(image_file_path),
    "description": "Example image file",
    "tags": ["image", "example", "mongodb"]
}

result = uploads_collection.insert_one(document)
print(f"메타데이터 삽입 성공: {result.inserted_id}")

# 저장된 이미지를 MongoDB에서 불러와 출력
get_image_from_mongodb(file_id)



# MySQL 작성

# import mysql.connector

# # MySQL 데이터베이스 연결 설정
# db_config = {
#     'user': os.getenv('DB_USER'),
#     'password': os.getenv('DB_PASSWORD'),
#     'host': os.getenv('DB_HOST'),
#     'database': os.getenv('DB_NAME'),
# }

# # MySQL 데이터베이스 연결
# def get_db_connection():
#     return mysql.connector.connect(**db_config)


        # # 파일을 MySQL uploads 테이블에 저장
        # connection = get_db_connection()
        # cursor = connection.cursor()
        # cursor.execute("INSERT INTO uploads (filename, content) VALUES (%s, %s)", (file.filename, file.read()))
        # connection.commit()




        # # MySQL
        # cursor.execute("INSERT INTO structured_data (ocr_text, summary, formatted_data) VALUES (%s, %s, %s)", 
        #                (ocr_text, summary, formatted_data))
        # connection.commit()

        # cursor.close()
        # connection.close()