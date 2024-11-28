import React, { useState } from "react";
import "../css/FileUpload.css"; // CSS 파일 임포트

const FileUpload = ({ onFileUpload }) => {
  const [fileName, setFileName] = useState(""); // 파일명 상태 추가

  const handleFileUpload = (event) => {
    const selectedFile = event.target.files[0];
    if (!selectedFile) return;

    setFileName(selectedFile.name); // 선택된 파일명 상태에 저장
    onFileUpload(selectedFile); // 상위 컴포넌트로 파일을 전달
  };

  return (
    <div className="file-upload-container">
      <div className="file-upload-wrapper">
        <label htmlFor="file-upload" className="file-upload-label">
          파일 업로드
        </label>
        <input
          type="file"
          id="file-upload"
          accept="image/*,application/pdf"
          onChange={handleFileUpload}
        />
        {fileName && <div className="file-name">{fileName}</div>}{" "}
        {/* 파일명이 있으면 출력 */}
      </div>
    </div>
  );
};

export default FileUpload;
