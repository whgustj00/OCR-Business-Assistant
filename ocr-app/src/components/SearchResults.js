import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

function SearchResults() {
  const location = useLocation();
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(""); // 에러 메시지 상태 추가
  const queryParams = new URLSearchParams(location.search);
  const query = queryParams.get("query"); // 쿼리 파라미터로 검색어 추출
  const startDate = queryParams.get("start_date"); // 시작 날짜 가져오기
  const endDate = queryParams.get("end_date"); // 끝 날짜 가져오기

  useEffect(() => {
    // 검색 요청 함수
    const fetchSearchResults = async () => {
      setIsLoading(true);
      setErrorMessage(""); // 이전 에러 메시지 초기화
      try {
        const response = await fetch(
          `http://127.0.0.1:5000/search?query=${encodeURIComponent(query)}${
            startDate ? `&start_date=${encodeURIComponent(startDate)}` : ""
          }${endDate ? `&end_date=${encodeURIComponent(endDate)}` : ""}`
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
        setErrorMessage("검색 결과를 가져오는 데 오류가 발생했습니다."); // 에러 메시지 설정
        setSearchResults([]); // 오류 발생 시 빈 배열 설정
      } finally {
        setIsLoading(false);
      }
    };

    if (query) {
      fetchSearchResults();
    }
  }, [query, startDate, endDate]); // 의존성 배열에 날짜도 추가

  if (isLoading) return <div>검색 중...</div>;

  return (
    <div>
      <h2>검색 결과 : {query}</h2>
      {errorMessage && <div className="error-message">{errorMessage}</div>}{" "}
      {/* 에러 메시지 표시 */}
      <div className="search-results">
        {searchResults.length > 0 ? (
          searchResults.map((result, index) => (
            <fieldset key={index} className="search-result-item">
              <h3>{result.filename}</h3>
              <p>업로드 날짜 : {result.upload_date}</p>
              <p width="200px">{result.summary}</p>
              <img
                src={result.image_url} // 이미지를 가져오는 URL
                alt="미리보기"
                style={{ width: "300px", height: "auto" }} // 이미지 스타일 설정
              />
            </fieldset>
          ))
        ) : (
          <div>검색 결과가 없습니다.</div>
        )}
      </div>
    </div>
  );
}

export default SearchResults;
