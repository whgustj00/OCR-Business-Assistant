import { useNavigate } from "react-router-dom"; // useNavigate 추가
import "../css/OcrOutput.css";
import "../css/App.css";

const OcrOutput = ({
  isOcrProcessing,
  htmlOutput,
  setHtmlOutput,
  isSummaryProcessing,
  summaryHtml,
  uploadId,
  confidence,
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
        <>
          {htmlOutput && (
            <>
              <div className="ocr-header">
                <textarea
                  value={htmlOutput}
                  onChange={(e) => setHtmlOutput(e.target.value)}
                  className="output-textarea"
                />
                {confidence !== 0 &&
                  confidence !== undefined &&
                  confidence !== null && ( // 신뢰도가 0이 아니고 유효한 값일 때만 출력
                    <p className="confidence-display">
                      신뢰도: {confidence.toFixed(3) * 100}%
                    </p>
                  )}
              </div>
            </>
          )}

          {htmlOutput && (
            <>
              {isSummaryProcessing ? (
                <p>처리 중...</p>
              ) : (
                <div
                  dangerouslySetInnerHTML={{ __html: summaryHtml }}
                  className="output"
                />
              )}
              {!isSummaryProcessing && summaryHtml && (
                <button className="button" onClick={handleAccuracyComparison}>
                  정확도 비교
                </button>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
};

export default OcrOutput;
