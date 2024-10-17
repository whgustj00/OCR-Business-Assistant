// src/components/FileUpload.js
import React from "react";
import "../css/FileUpload.css"; // CSS 파일 임포트

const FileUpload = ({ onFileUpload }) => {
  const handleFileUpload = (event) => {
    const selectedFile = event.target.files[0];
    if (!selectedFile) return;

    onFileUpload(selectedFile); // 상위 컴포넌트로 파일을 전달
  };

  return (
    <div className="file-upload-container">
      <input
        type="file"
        accept="image/*,application/pdf"
        onChange={handleFileUpload}
      />
    </div>
  );
};

export default FileUpload;
