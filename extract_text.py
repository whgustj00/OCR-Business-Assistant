from flask import Blueprint, request, jsonify
from PIL import Image
from models import api_url, secret_key, perform_clova_ocr, save_image_to_gridfs, save_db_upload, convert_pdf_to_images, preprocess_image, parse_page_range

extract_text = Blueprint('extract_text', __name__)

@extract_text.route('/extract_text', methods=['POST'])
def extract_text_route():
    
    try:
        if 'file' not in request.files:
            return jsonify({"error": "파일이 없습니다."}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "파일 이름이 비어있습니다."}), 400

        # 페이지 범위 가져오기
        page_range = request.form.get('pageRange', '')  # 페이지 범위 가져오기
        pages_to_process = parse_page_range(page_range) if page_range else None  # 페이지 범위 파싱

        ocr_text = ""

        if file.content_type == 'application/pdf':
            # PDF 파일을 이미지로 변환
            images = convert_pdf_to_images(file)

            # 특정 페이지 범위만 처리
            if pages_to_process:
                for page_number in pages_to_process:
                    if page_number < len(images):  # 페이지 번호 유효성 검사
                        img = images[page_number]
                        # GridFS에 이미지 저장 (전처리 전에)
                        image_id = save_image_to_gridfs(img)
                        # 이미지 전처리 후 OCR 수행
                        img = preprocess_image(img)
                        ocr_text += f"=== 페이지 {page_number + 1} ===\n\n"  # 페이지 번호 추가
                        ocr_text += perform_clova_ocr(img, api_url, secret_key) + "\n\n\n"  # OCR 수행 후 결과 구분
            else:
                # 모든 페이지 처리
                for i, img in enumerate(images):
                    # GridFS에 이미지 저장 (전처리 전에)
                    image_id = save_image_to_gridfs(img)
                    # 이미지 전처리 후 OCR 수행
                    img = preprocess_image(img)
                    ocr_text += f"=== 페이지 {i + 1} ===\n\n"  # 페이지 번호 추가
                    ocr_text += perform_clova_ocr(img, api_url, secret_key) + "\n\n\n"  # OCR 수행 후 결과 구분
        else:
            # JPG, PNG 등 이미지 파일 처리
            img = Image.open(file)
            # GridFS에 이미지 저장 (전처리 전에)
            image_id = save_image_to_gridfs(img)
            # 이미지 전처리 후 OCR 수행
            img = preprocess_image(img)
            ocr_text = perform_clova_ocr(img, api_url, secret_key)  # CLOVA OCR 수행
            # ocr_text = perform_ocr(img) # GPT API OCR 수행

        # 업로드 정보를 DB에 저장
        upload_id = save_db_upload(file.filename, ocr_text, image_id)

        return jsonify({"html": ocr_text, "upload_id": upload_id})

    except Exception as e:
        print(f"Error in extract_text: {str(e)}")
        return jsonify({"error": str(e)}), 500
