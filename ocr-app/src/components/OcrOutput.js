// src/components/OcrOutput.js
import React from "react";
import "../css/OcrOutput.css"; // CSS 파일 임포트

const OcrOutput = ({
  isOcrProcessing,
  htmlOutput,
  isSummaryProcessing,
  summaryHtml,
}) => {
  return (
    <div className="ocr-output">
      <h2>OCR 텍스트 추출 결과</h2>
      {isOcrProcessing ? (
        <p>처리 중...</p>
      ) : (
        <div
          dangerouslySetInnerHTML={{ __html: htmlOutput }}
          className="output"
        />
      )}

      {htmlOutput && ( // OCR 결과가 있을 때만 요약 및 정형화 결과 표시
        <>
          {isSummaryProcessing ? (
            <p>처리 중...</p>
          ) : (
            <div
              dangerouslySetInnerHTML={{ __html: summaryHtml }} // HTML로 요약 결과 표시
              className="output"
            />
          )}
        </>
      )}
    </div>
  );
};

export default OcrOutput;
