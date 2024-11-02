import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

function LlmSearchResults() {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const queryParams = new URLSearchParams(location.search);
  const [query, setQuery] = useState(queryParams.get("query") || "");

  const fetchSearchResults = async (searchQuery) => {
    setIsLoading(true);
    try {
      console.log("Fetching search results for query:", searchQuery);
      const response = await fetch(
        `http://127.0.0.1:5000/search_llm?query=${encodeURIComponent(
          searchQuery
        )}`
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Error: ${errorData.error || response.statusText}`);
      }

      const data = await response.json();

      if (data.results) {
        setSearchResults(data.results);
      }
    } catch (error) {
      console.error("Error fetching LLM search results:", error);
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (event) => {
    event.preventDefault();
    navigate(`/search_llm?query=${encodeURIComponent(query)}`);
    fetchSearchResults(query); // 버튼 클릭 시 검색 결과 가져오기
  };

  if (isLoading) return <div>검색 중...</div>;

  return (
    <div>
      <h2>LLM 검색 결과 : {query}</h2>
      <form onSubmit={handleSearch}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)} // 상태 업데이트는 여전히 필요
          placeholder="검색어를 입력하세요"
        />
        <button type="submit">검색</button>
      </form>
      <div className="search-results">
        {searchResults.length > 0 ? (
          searchResults.map((result, index) => (
            <fieldset key={index} className="search-result-item">
              <h3>{result.filename}</h3>
              <p>업로드 날짜 : {result.upload_date}</p>
              <p>{result.summary}</p>
            </fieldset>
          ))
        ) : (
          <div>검색 결과가 없습니다.</div>
        )}
      </div>
    </div>
  );
}

export default LlmSearchResults;
