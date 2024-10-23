// src/components/App.js
import React, { useState } from "react";
import { getDocument } from "pdfjs-dist/webpack"; // PDF.js 가져오기
import FileUpload from "./FileUpload";
import ImagePreview from "./ImagePreview";
import OcrOutput from "./OcrOutput";
import { useNavigate } from "react-router-dom"; // 페이지 이동을 위한 hook
import "../css/App.css"; // CSS 파일을 추가하세요.

function App() {
  const [htmlOutput, setHtmlOutput] = useState("");
  const [imageUrls, setImageUrls] = useState([]); // 이미지 미리보기를 위한 상태
  const [isProcessing, setIsProcessing] = useState(false); // 처리 중 상태
  const [pageRange, setPageRange] = useState(""); // 페이지 범위 상태 추가
  const [file, setFile] = useState(null); // 선택된 파일 상태 추가
  const [currentPage, setCurrentPage] = useState(0); // 현재 페이지 상태 추가
  const [scale, setScale] = useState(1); // 스케일 상태 추가
  const [searchTerm, setSearchTerm] = useState("");
  const navigate = useNavigate(); // 페이지 이동을 위한 함수

  // 검색 요청 처리
  const handleSearch = async () => {
    if (!searchTerm) {
      alert("검색어를 입력하세요.");
      return;
    }

    // 검색어를 쿼리 파라미터로 새로운 페이지로 이동
    navigate(`/search?query=${encodeURIComponent(searchTerm)}`);
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

  const handleFileUpload = async (selectedFile) => {
    setFile(selectedFile); // 선택된 파일 상태 업데이트
    setImageUrls([]); // 새로운 파일 선택 시 이미지 미리보기 초기화
    setCurrentPage(0); // 페이지 초기화

    // PDF 파일인 경우 처리
    if (selectedFile.type === "application/pdf") {
      const pdfImageUrls = await convertPdfToImages(selectedFile);
      setImageUrls(pdfImageUrls);
    } else {
      setImageUrls([URL.createObjectURL(selectedFile)]); // 이미지 미리보기 설정
    }

    setPageRange("");
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
          const viewport = page.getViewport({ scale: 1.5 });
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

  return (
    <div>
      <nav className="navbar">
        <h1 className="navbar-title">OCR 비즈니스 어시스턴트</h1>
      </nav>
      <div className="App">
        <input
          type="text"
          placeholder="문서 검색"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <button onClick={handleSearch}>검색</button>
        <FileUpload onFileUpload={handleFileUpload} />
        <input
          type="text"
          placeholder="페이지 범위 (예: 1-3)"
          value={pageRange}
          onChange={(e) => setPageRange(e.target.value)}
          disabled={file && file.type !== "application/pdf"} // PDF가 아닐 경우 비활성화
        />
        <br />
        <button onClick={handleTextExtraction} disabled={isProcessing}>
          텍스트 추출
        </button>
        <div className="output-container">
          <ImagePreview
            imageUrls={imageUrls}
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
            scale={scale}
            setScale={setScale}
          />
          <OcrOutput isProcessing={isProcessing} htmlOutput={htmlOutput} />
        </div>
      </div>
    </div>
  );
}

export default App;
