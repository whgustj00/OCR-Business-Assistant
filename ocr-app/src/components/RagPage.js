import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import "../css/RagPage.css"; // CSS 파일을 import 합니다.

const formatDate = (dateString) => {
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${year}년 ${month}월 ${day}일 ${hours}시 ${minutes}분`;
};

function RagPage() {
  const location = useLocation();
  const [searchResults, setSearchResults] = useState(null);
  const [mostSimilarDocument, setMostSimilarDocument] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const queryParams = new URLSearchParams(location.search);
  const query = queryParams.get("query");

  // 캐시된 데이터를 로컬 스토리지에서 가져옵니다.
  const getCachedData = () => {
    const cachedResults = localStorage.getItem(query);
    if (cachedResults) {
      return JSON.parse(cachedResults); // 캐시된 데이터 반환
    }
    return null; // 없으면 null 반환
  };

  useEffect(() => {
    const fetchSearchResults = async () => {
      setIsLoading(true);
      setErrorMessage("");

      const cachedData = getCachedData();
      if (cachedData) {
        setSearchResults(cachedData.results);
        setMostSimilarDocument(cachedData.sources[0]);
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(
          `http://127.0.0.1:5000/rag?query=${encodeURIComponent(query)}`
        );

        if (!response.ok) {
          throw new Error("Network response was not ok");
        }

        const data = await response.json();

        if (data.results && data.sources && data.sources.length > 0) {
          setSearchResults(data.results);
          setMostSimilarDocument(data.sources[0]);

          // 데이터를 로컬 스토리지에 저장하여 캐시
          localStorage.setItem(query, JSON.stringify(data));
        } else {
          console.warn("Expected 'results' and 'sources' to be present", data);
          setSearchResults(null);
          setMostSimilarDocument(null);
        }
      } catch (error) {
        console.error("Error fetching search results:", error);
        setErrorMessage("검색 결과를 가져오는 데 오류가 발생했습니다.");
        setSearchResults(null);
        setMostSimilarDocument(null);
      } finally {
        setIsLoading(false);
      }
    };

    if (query) {
      fetchSearchResults();
    }
  }, [query]);

  if (isLoading) return <div className="loading">검색 중...</div>;

  return (
    <div className="rag-page">
      <h2>검색어 : {query}</h2>
      {errorMessage && <div className="error-message">{errorMessage}</div>}

      <div className="search-results">
        {searchResults ? (
          <div className="result-answer">
            <h3>답변:</h3>
            <p>{searchResults}</p>
          </div>
        ) : (
          <div>검색 결과가 없습니다.</div>
        )}

        {mostSimilarDocument && (
          <div className="document-card">
            <h3>가장 유사한 문서:</h3>
            <div className="document-details">
              <p>
                <strong>파일명:</strong>{" "}
                {mostSimilarDocument.filename || "파일명 없음"}
              </p>
              <p>
                <strong>업로드 날짜:</strong>{" "}
                {formatDate(mostSimilarDocument.upload_date)}
              </p>
              <p>
                <strong>내용:</strong>{" "}
                {/* dangerouslySetInnerHTML을 사용하여 HTML 삽입 */}
                <div
                  className="document-content"
                  dangerouslySetInnerHTML={{
                    __html: mostSimilarDocument.page_content,
                  }}
                />
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default RagPage;
