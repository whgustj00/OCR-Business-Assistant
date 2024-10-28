// src/components/OcrOutput.js
import React from "react";
import "../css/OcrOutput.css";

const OcrOutput = ({
  isOcrProcessing,
  htmlOutput,
  setHtmlOutput,
  isSummaryProcessing,
  summaryHtml,
}) => {
  return (
    <div className="ocr-output">
      <h2>OCR 텍스트 추출 결과</h2>
      {isOcrProcessing ? (
        <p>처리 중...</p>
      ) : (
        htmlOutput && ( // htmlOutput
          <textarea
            value={htmlOutput}
            onChange={(e) => setHtmlOutput(e.target.value)} // 상위 컴포넌트에 변경 반영
            className="output-textarea"
          />
        )
      )}

      {htmlOutput && (
        <>
          <h2>요약 및 정형화 결과</h2>
          {isSummaryProcessing ? (
            <p>처리 중...</p>
          ) : (
            <div
              dangerouslySetInnerHTML={{ __html: summaryHtml }}
              className="output"
            />
          )}
        </>
      )}
    </div>
  );
};

export default OcrOutput;
