import { useNavigate } from "react-router-dom"; // useNavigate 추가
import "../css/OcrOutput.css";

const OcrOutput = ({
  isOcrProcessing,
  htmlOutput,
  setHtmlOutput,
  isSummaryProcessing,
  summaryHtml,
  uploadId,
}) => {
  const navigate = useNavigate(); // useNavigate 훅 사용

  const handleAccuracyComparison = () => {
    // 페이지 이동 로직
    navigate(`/accuracy/${uploadId}`); // 정확도 비교 페이지로 이동
  };

  return (
    <div className="ocr-output">
      <h2>OCR 텍스트 추출 결과</h2>
      {isOcrProcessing ? (
        <p>처리 중...</p>
      ) : (
        htmlOutput && (
          <textarea
            value={htmlOutput}
            onChange={(e) => setHtmlOutput(e.target.value)}
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
          {!isSummaryProcessing && summaryHtml && (
            <button onClick={handleAccuracyComparison}>정확도 비교</button>
          )}
          {/* 정확도 비교 버튼 추가 */}
        </>
      )}
    </div>
  );
};

export default OcrOutput;
