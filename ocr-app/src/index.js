// src/index.js
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./components/App"; // App 컴포넌트 임포트
import "./index.css"; // CSS 파일을 추가하세요.

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
