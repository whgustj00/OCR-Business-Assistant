// src/components/ImagePreview.js
import React from "react";
import "../css/ImagePreview.css"; // CSS 파일 임포트

const ImagePreview = ({
  imageUrls,
  currentPage,
  setCurrentPage,
  scale,
  setScale,
}) => {
  const handleNextPage = () => {
    if (currentPage < imageUrls.length - 1) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePreviousPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleZoomIn = () => {
    setScale((prevScale) => prevScale + 0.1);
  };

  const handleZoomOut = () => {
    setScale((prevScale) => Math.max(0.1, prevScale - 0.1));
  };

  return (
    <div className="file-preview">
      {imageUrls.length > 0 && (
        <>
          <div className="zoom-controls">
            <button onClick={handleZoomOut} disabled={scale <= 0.1}>
              –
            </button>
            <button onClick={handleZoomIn}>+</button>
          </div>
          <img
            src={imageUrls[currentPage]}
            alt={`Page ${currentPage + 1}`}
            className="preview-image"
            style={{
              transform: `scale(${scale})`,
              transition: "transform 0.2s",
            }}
          />
          <div className="arrow-container">
            <button
              onClick={handlePreviousPage}
              disabled={currentPage === 0}
              className="arrow-button left-arrow"
            >
              ◀
            </button>
            <button
              onClick={handleNextPage}
              disabled={currentPage === imageUrls.length - 1}
              className="arrow-button right-arrow"
            >
              ▶
            </button>
          </div>
        </>
      )}
      <p>
        페이지 {currentPage + 1} / {imageUrls.length}
      </p>
    </div>
  );
};

export default ImagePreview;
