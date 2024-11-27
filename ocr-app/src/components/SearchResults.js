import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import "../css/SearchResults.css";

function SearchResults() {
  const location = useLocation();
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const queryParams = new URLSearchParams(location.search);
  const query = queryParams.get("query");
  const startDate = queryParams.get("start_date");
  const endDate = queryParams.get("end_date");

  useEffect(() => {
    const fetchSearchResults = async () => {
      setIsLoading(true);
      setErrorMessage("");
      try {
        const response = await fetch(
          `http://127.0.0.1:5000/search?query=${encodeURIComponent(query)}${
            startDate ? `&start_date=${encodeURIComponent(startDate)}` : ""
          }${endDate ? `&end_date=${encodeURIComponent(endDate)}` : ""}`
        );

        if (!response.ok) {
          throw new Error("Network response was not ok");
        }

        const data = await response.json();

        if (Array.isArray(data.results)) {
          setSearchResults(data.results);
        } else {
          console.warn("Expected 'results' to be an array", data.results);
          setSearchResults([]);
        }
      } catch (error) {
        console.error("Error fetching search results:", error);
        setErrorMessage("검색 결과를 가져오는 데 오류가 발생했습니다.");
        setSearchResults([]);
      } finally {
        setIsLoading(false);
      }
    };

    if (query) {
      fetchSearchResults();
    }
  }, [query, startDate, endDate]);

  if (isLoading) return <div className="loading">검색 중...</div>;

  return (
    <div>
      <h2 className="search-term">검색어: {query}</h2>
      {errorMessage && <div className="error-message">{errorMessage}</div>}
      <div className="search-results">
        {searchResults.length > 0 ? (
          searchResults.map((result, index) => (
            <fieldset key={index} className="search-result-item">
              <div className="text-content">
                <h3>{result.filename}</h3>
                <p>업로드 날짜: {result.upload_date}</p>
                <p>{result.summary}</p>
              </div>
              <div className="image-content">
                <img
                  src={result.image_url}
                  alt="미리보기"
                  className="result-image"
                />
              </div>
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
