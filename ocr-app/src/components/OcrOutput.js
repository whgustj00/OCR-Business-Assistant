// src/components/OcrOutput.js
import React from "react";
import "../css/OcrOutput.css"; // CSS 파일 임포트

const OcrOutput = ({ isProcessing, htmlOutput }) => {
  return (
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
  );
};

export default OcrOutput;
