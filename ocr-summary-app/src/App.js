import React, { useState } from "react";
import "./App.css"; // CSS 파일을 추가하세요.

const FileUpload = () => {
  const [htmlOutput, setHtmlOutput] = useState("");

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (response.ok) {
        setHtmlOutput(data.html); // HTML로 출력
      } else {
        alert(`파일 업로드 중 오류가 발생했습니다: ${data.error}`);
      }
    } catch (error) {
      console.error("Error:", error);
      alert("파일 업로드 중 오류가 발생했습니다.");
    }
  };

  return (
    <div className="file-upload-container">
      <h1>OCR 비즈니스 어시스턴트</h1>
      <input type="file" accept="image/*" onChange={handleFileUpload} />
      <div
        dangerouslySetInnerHTML={{ __html: htmlOutput }}
        className="output"
      />
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <FileUpload />
    </div>
  );
}

export default App;
