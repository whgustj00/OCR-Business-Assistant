// src/components/SearchResults.js
import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

function SearchResults() {
  const location = useLocation();
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const queryParams = new URLSearchParams(location.search);
  const query = queryParams.get("query"); // 쿼리 파라미터로 검색어 추출

  useEffect(() => {
    // 검색 요청 함수
    const fetchSearchResults = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(
          `http://127.0.0.1:5000/search?query=${encodeURIComponent(query)}`
        );

        // 응답이 JSON 형식인지 확인
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }

        const data = await response.json();

        // data.results가 배열인지 확인 후 설정
        if (Array.isArray(data.results)) {
          setSearchResults(data.results); // 검색 결과 설정
        } else {
          console.warn("Expected 'results' to be an array", data.results);
          setSearchResults([]); // 빈 배열로 설정
        }
      } catch (error) {
        console.error("Error fetching search results:", error);
        setSearchResults([]); // 오류 발생 시 빈 배열 설정
      } finally {
        setIsLoading(false);
      }
    };

    if (query) {
      fetchSearchResults();
    }
  }, [query]);

  if (isLoading) return <div>검색 중...</div>;

  return (
    <div>
      <h2>검색 결과: {query}</h2>
      <div className="search-results">
        {searchResults.length > 0 ? (
          searchResults.map((result, index) => (
            <div key={index} className="search-result-item">
              <h3>{result.title}</h3>
              <p>{result.summary}</p>
              {/* 미리보기 이미지 추가 */}
              {result.imageLink && (
                <img
                  src={result.imageLink}
                  alt="미리보기"
                  style={{ width: "300px", height: "auto" }} // 이미지 스타일 설정
                />
              )}
              <button
                onClick={() => window.open(result.downloadLink, "_blank")}
              >
                다운로드
              </button>
              <button onClick={() => window.open(result.previewLink, "_blank")}>
                미리보기
              </button>
            </div>
          ))
        ) : (
          <div>검색 결과가 없습니다.</div>
        )}
      </div>
    </div>
  );
}

export default SearchResults;
