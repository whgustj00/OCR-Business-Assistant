from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()  # 환경 변수 로드

api_key = os.getenv("api_key")

app = Flask(__name__)
CORS(app)


headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

# 라우트 가져오기
from extract_text import extract_text
from summarize import summarize_and_format
from search import search
from accuracy import accuracy
from rag import rag

# 라우트 등록
app.register_blueprint(extract_text)
app.register_blueprint(summarize_and_format)
app.register_blueprint(search)
app.register_blueprint(accuracy)
app.register_blueprint(rag)

if __name__ == '__main__':
    app.run(debug=True)
