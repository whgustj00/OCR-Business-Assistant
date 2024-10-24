// src/components/App.js
import React, { useState } from "react";
import { getDocument } from "pdfjs-dist/webpack";
import FileUpload from "./FileUpload";
import ImagePreview from "./ImagePreview";
import OcrOutput from "./OcrOutput";
import { useNavigate } from "react-router-dom";
import "../css/App.css";

function App() {
  const [htmlOutput, setHtmlOutput] = useState("");
  const [imageUrls, setImageUrls] = useState([]);
  const [isOcrProcessing, setIsOcrProcessing] = useState(false);
  const [isSummaryProcessing, setIsSummaryProcessing] = useState(false);
  const [pageRange, setPageRange] = useState("");
  const [file, setFile] = useState(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [scale, setScale] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const [summaryHtml, setSummaryHtml] = useState("");
  const [formattedData, setFormattedData] = useState({});
  const [fileName, setFileName] = useState("");
  const [summary, setSummary] = useState("");
  const [uploadId, setUploadId] = useState("");

  const navigate = useNavigate();

  // 검색 요청 처리
  const handleSearch = async () => {
    if (!searchTerm) {
      alert("검색어를 입력하세요.");
      return;
    }
    navigate(`/search?query=${encodeURIComponent(searchTerm)}`);
  };

  const validatePageRange = (range) => {
    const regex = /^\d+-\d+$/;
    if (!regex.test(range)) return false;

    const [start, end] = range.split("-").map(Number);
    return start <= end && start > 0;
  };

  // 텍스트 추출
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
    formData.append("pageRange", pageRange);

    try {
      setIsOcrProcessing(true);
      const response = await fetch("http://127.0.0.1:5000/extract_text", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (response.ok) {
        setHtmlOutput(data.html); // HTML 레이아웃으로 저장
        setFileName(file.name); // 파일 이름 저장
        setUploadId(data.upload_id); // 백엔드에서 받은 upload_id 저장
      } else {
        alert(`텍스트 추출 중 오류가 발생했습니다: ${data.error}`);
      }
    } catch (error) {
      console.error("Error:", error);
      alert("텍스트 추출 중 오류가 발생했습니다.");
    } finally {
      setIsOcrProcessing(false);
    }
  };

  // 요약 및 정형화
  const handleSummarizeAndFormat = async () => {
    if (!htmlOutput) {
      alert("먼저 텍스트 추출을 수행하세요.");
      return;
    }

    try {
      setIsSummaryProcessing(true); // 요약 처리 시작
      const response = await fetch(
        "http://127.0.0.1:5000/summarize_and_format",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ocr_text: htmlOutput,
            filename: fileName,
            upload_id: uploadId, // upload_id 전송
          }),
        }
      );
      const data = await response.json();

      if (response.ok) {
        setSummaryHtml(data.html); // 요약 HTML 저장
        setFormattedData(data.formatted_data); // 정형화된 데이터 저장
        setSummary(data.summary); // 요약 저장
      } else {
        alert(`요약 및 정형화 중 오류가 발생했습니다: ${data.error}`);
      }
    } catch (error) {
      console.error("Error:", error);
      alert("요약 및 정형화 중 오류가 발생했습니다.");
    } finally {
      setIsSummaryProcessing(false);
    }
  };

  // 파일 업로드 핸들러
  const handleFileUpload = async (selectedFile) => {
    setHtmlOutput("");
    setImageUrls([]);
    setCurrentPage(0);
    setSummaryHtml("");
    setFormattedData({});
    setSummary("");
    setPageRange("");
    setFile(selectedFile);
    setIsOcrProcessing(false);
    setIsSummaryProcessing(false);

    if (selectedFile.type === "application/pdf") {
      const pdfImageUrls = await convertPdfToImages(selectedFile);
      setImageUrls(pdfImageUrls);
    } else {
      setImageUrls([URL.createObjectURL(selectedFile)]);
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
          disabled={file && file.type !== "application/pdf"}
        />
        <br />
        <button onClick={handleTextExtraction} disabled={isOcrProcessing}>
          텍스트 추출
        </button>

        {htmlOutput && (
          <button
            onClick={handleSummarizeAndFormat}
            disabled={isSummaryProcessing}
          >
            요약 및 정형화
          </button>
        )}

        <div className="output-container">
          <ImagePreview
            imageUrls={imageUrls}
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
            scale={scale}
            setScale={setScale}
          />
          <OcrOutput
            isOcrProcessing={isOcrProcessing}
            htmlOutput={htmlOutput}
            isSummaryProcessing={isSummaryProcessing}
            summaryHtml={summaryHtml}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
