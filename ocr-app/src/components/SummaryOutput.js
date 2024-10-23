// src/components/SummaryOutput.js
import React from "react";
import "../css/SummaryOutput.css"; // CSS 파일 임포트

const SummaryOutput = ({ isProcessing, summaryHtml }) => {
  return (
    <div className="summary-output">
      <h2>요약 및 정형화 결과</h2>
      {isProcessing ? (
        <p>처리 중...</p>
      ) : (
        <div
          dangerouslySetInnerHTML={{ __html: summaryHtml }} // HTML로 요약 결과 표시
          className="output"
        />
      )}
    </div>
  );
};

export default SummaryOutput;
