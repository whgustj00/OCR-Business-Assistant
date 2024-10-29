import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { diffWords } from "diff"; // diff 라이브러리에서 diffWords 함수 임포트
import "../css/Accuracy.css";

const Accuracy = () => {
  const { uploadId } = useParams();
  const [originalText, setOriginalText] = useState("");
  const [ocrText, setOcrText] = useState("");
  const [accuracy, setAccuracy] = useState(null);

  useEffect(() => {
    const fetchAccuracyData = async () => {
      const response = await fetch("http://127.0.0.1:5000/accuracy", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ upload_id: uploadId }),
      });
      const data = await response.json();

      if (response.ok) {
        setOriginalText(data.original_text); // 원본 텍스트
        setOcrText(data.ocr_text); // 수정된 텍스트
        setAccuracy(data.accuracy); // 정확도
      } else {
        alert(`오류 발생: ${data.error}`);
      }
    };

    fetchAccuracyData();
  }, [uploadId]);

  const highlightDifferences = (original, modified) => {
    const diff = diffWords(original, modified);

    // 원본 텍스트와 수정 텍스트를 강조 표시 설정
    const highlightedOriginal = [];
    const highlightedModified = [];

    diff.forEach((part, index) => {
      if (part.added) {
        // 수정 텍스트에서 추가된 부분 강조
        highlightedModified.push(
          <span key={`mod-${index}`} style={{ backgroundColor: "lightgreen" }}>
            {part.value}
          </span>
        );
      } else if (part.removed) {
        // 원본 텍스트에서 삭제된 부분 강조
        highlightedOriginal.push(
          <span key={`orig-${index}`} style={{ backgroundColor: "lightcoral" }}>
            {part.value}
          </span>
        );
        // 수정 텍스트에는 추가된 부분을 추가하지 않음
      } else {
        // 두 텍스트 모두 동일한 부분
        highlightedOriginal.push(part.value);
        highlightedModified.push(part.value); // 동일 부분은 수정 텍스트에도 추가
      }
    });

    return { highlightedOriginal, highlightedModified };
  };

  const { highlightedOriginal, highlightedModified } = highlightDifferences(
    originalText,
    ocrText
  );

  return (
    <div className="title">
      <h2>정확도 비교</h2>
      {accuracy !== null && <h3>정확도: {accuracy.toFixed(2)}%</h3>}
      <div className="text-container">
        <div className="text-output">
          <h3>원본 텍스트</h3>
          <div>{highlightedOriginal}</div> {/* 강조된 원본 텍스트 표시 */}
        </div>
        <div className="text-output">
          <h3>수정 텍스트</h3>
          <div>{highlightedModified}</div> {/* 강조된 수정 텍스트 표시 */}
        </div>
      </div>
    </div>
  );
};

export default Accuracy;
