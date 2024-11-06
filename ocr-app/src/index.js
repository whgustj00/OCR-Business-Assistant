import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom"; // React Router 임포트
import App from "./components/App"; // App 컴포넌트 임포트
import SearchResults from "./components/SearchResults"; // SearchResults 컴포넌트 임포트
import Accuracy from "./components/Accuracy";
import RagPage from "./components/RagPage"; // LLM 검색 결과 컴포넌트 추가

import "./index.css"; // CSS 파일을 추가하세요.

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<App />} /> {/* 메인 페이지 */}
        <Route path="/search" element={<SearchResults />} />{" "}
        {/* 검색 결과 페이지 */}
        <Route path="/accuracy/:uploadId" element={<Accuracy />} />{" "}
        {/* 정확도 비교 페이지 */}
        <Route path="/ragpage" element={<RagPage />} />{" "}
        {/* RAG 검색 결과 경로 추가 */}
      </Routes>
    </Router>
  </React.StrictMode>
);
