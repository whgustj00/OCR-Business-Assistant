import React, { useState } from "react";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import { FaRedo, FaSearchPlus, FaSearchMinus } from "react-icons/fa"; // 확대/축소 아이콘 임포트
import "../css/ImagePreview.css"; // CSS 파일 임포트

const ImagePreview = ({ imageUrls, currentPage, setCurrentPage }) => {
  // 페이지 이동 함수
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

  return (
    <div className="file-preview">
      {imageUrls.length > 0 && (
        <>
          <TransformWrapper
            initialScale={1}
            minScale={0.75} // 최소 확대 비율
            maxScale={2} // 최대 확대 비율
            wheel={{ step: 0.05 }} // 휠로 확대/축소
          >
            {({ zoomIn, zoomOut, resetTransform, ...rest }) => (
              <>
                {/* 줌 컨트롤 버튼들 */}
                <div className="zoom-controls">
                  <button onClick={() => zoomIn()}>
                    <FaSearchPlus size={18} /> {/* 확대 아이콘 */}
                  </button>
                  <button onClick={() => zoomOut()}>
                    <FaSearchMinus size={18} /> {/* 축소 아이콘 */}
                  </button>
                  <button
                    className="reset-button"
                    onClick={() => resetTransform()}
                  >
                    <FaRedo size={18} /> {/* 리셋 아이콘 */}
                  </button>
                </div>

                {/* 이미지 영역 */}
                <TransformComponent>
                  <img
                    src={imageUrls[currentPage]}
                    alt={`Page ${currentPage + 1}`}
                    className="preview-image"
                  />
                </TransformComponent>
              </>
            )}
          </TransformWrapper>

          {/* 페이지 이동 버튼들 */}
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

          {/* 페이지 정보 */}
          <p className="page-info">
            페이지 {currentPage + 1} / {imageUrls.length}
          </p>
        </>
      )}
    </div>
  );
};

export default ImagePreview;
