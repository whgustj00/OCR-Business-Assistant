import React, { useState } from "react";
import "./App.css"; // CSS 파일을 추가하세요.
import { getDocument } from "pdfjs-dist/webpack"; // PDF.js 가져오기

const FileUpload = () => {
  const [htmlOutput, setHtmlOutput] = useState("");
  const [imageUrls, setImageUrls] = useState([]); // 이미지 미리보기를 위한 상태
  const [isProcessing, setIsProcessing] = useState(false); // 처리 중 상태
  const [pageRange, setPageRange] = useState(""); // 페이지 범위 상태 추가
  const [file, setFile] = useState(null); // 선택된 파일 상태 추가
  const [currentPage, setCurrentPage] = useState(0); // 현재 페이지 상태 추가

  const handleFileUpload = (event) => {
    const selectedFile = event.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile); // 파일 상태 업데이트
    setImageUrls([]); // 새로운 파일 선택 시 이미지 미리보기 초기화
    setCurrentPage(0); // 페이지 초기화

    // PDF 파일인 경우 처리
    if (selectedFile.type === "application/pdf") {
      convertPdfToImages(selectedFile).then((pdfImageUrls) => {
        setImageUrls(pdfImageUrls);
      });
    } else {
      setImageUrls([URL.createObjectURL(selectedFile)]); // 이미지 미리보기 설정
    }

    setPageRange("");
  };

  const validatePageRange = (range) => {
    const regex = /^\d+-\d+$/; // "X-Y" 형식인지 확인
    if (!regex.test(range)) return false;

    const [start, end] = range.split("-").map(Number);
    return start <= end && start > 0; // 시작 페이지가 종료 페이지보다 작고 0보다 커야 함
  };

  const handleTextExtraction = async () => {
    if (!file) {
      alert("먼저 파일을 업로드 해주세요.");
      return;
    }

    if (file.type === "application/pdf" && !validatePageRange(pageRange)) {
      alert("유효한 페이지 범위를 입력하세요 (예: 1-3).");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("pageRange", pageRange); // 페이지 범위 추가

    try {
      setIsProcessing(true); // 처리 시작

      const response = await fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (response.ok) {
        setHtmlOutput(data.html); // HTML로 출력
      } else {
        alert(`파일 업로드 중 오류가 발생했습니다: ${data.error}`);
      }
    } catch (error) {
      console.error("Error:", error);
      alert("파일 업로드 중 오류가 발생했습니다.");
    } finally {
      setIsProcessing(false); // 처리 종료
    }
  };

  const convertPdfToImages = async (file) => {
    const fileReader = new FileReader();
    const imageUrls = [];

    return new Promise((resolve, reject) => {
      fileReader.onload = async () => {
        const typedArray = new Uint8Array(fileReader.result);
        const pdf = await getDocument(typedArray).promise;
        const numPages = pdf.numPages;

        for (let i = 1; i <= numPages; i++) {
          const page = await pdf.getPage(i);
          const viewport = page.getViewport({ scale: 1 });
          const canvas = document.createElement("canvas");
          const context = canvas.getContext("2d");
          canvas.height = viewport.height;
          canvas.width = viewport.width;

          await page.render({ canvasContext: context, viewport: viewport })
            .promise;
          imageUrls.push(canvas.toDataURL());
        }

        resolve(imageUrls);
      };
      fileReader.onerror = (error) => reject(error);
      fileReader.readAsArrayBuffer(file);
    });
  };

  const handleNextPage = () => {
    if (currentPage < imageUrls.length - 1) {
      setCurrentPage(currentPage + 1); // 다음 페이지로 이동
    }
  };

  const handlePreviousPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1); // 이전 페이지로 이동
    }
  };

  return (
    <div className="file-upload-container">
      <input
        type="file"
        accept="image/*,application/pdf"
        onChange={handleFileUpload}
      />
      <input
        type="text"
        placeholder="페이지 범위 (예: 1-3)"
        value={pageRange}
        onChange={(e) => setPageRange(e.target.value)}
        disabled={file && file.type !== "application/pdf"}
      />
      <br />
      <button onClick={handleTextExtraction} disabled={isProcessing}>
        텍스트 추출
      </button>
      <div className="output-container">
        <div className="file-preview">
          {imageUrls.length > 0 && (
            <>
              <img
                src={imageUrls[currentPage]}
                alt={`Page ${currentPage + 1}`}
                className="preview-image"
              />
              <div className="arrow-container">
                <button
                  onClick={handlePreviousPage}
                  disabled={currentPage === 0}
                  className="arrow-button left-arrow"
                >
                  ◀
                </button>
                <button
                  onClick={handleNextPage}
                  disabled={currentPage === imageUrls.length - 1}
                  className="arrow-button right-arrow"
                >
                  ▶
                </button>
              </div>
            </>
          )}
          <p>
            페이지 {currentPage + 1} / {imageUrls.length}
          </p>
        </div>
        <div className="ocr-output">
          <h2>OCR 및 요약 결과</h2>
          {isProcessing ? (
            <p>처리 중...</p>
          ) : (
            <div
              dangerouslySetInnerHTML={{ __html: htmlOutput }}
              className="output"
            />
          )}
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <div>
      <nav className="navbar">
        <h1 className="navbar-title">OCR 비즈니스 어시스턴트</h1>
      </nav>
      <div className="App">
        <FileUpload />
      </div>
    </div>
  );
}

export default App;
