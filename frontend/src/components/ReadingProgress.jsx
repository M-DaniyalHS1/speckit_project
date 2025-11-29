import React, { useState, useEffect } from 'react';
import './ReadingProgress.css'; // Optional CSS file for styling

/**
 * ReadingProgress Component
 * Displays the user's reading progress for a specific book
 * 
 * Props:
 * - bookId: ID of the book being read
 * - currentChapter: Current chapter name or number
 * - currentPage: Current page number
 * - totalProgress: Overall progress percentage for the book
 * - currentSessionProgress: Current session progress
 * - onProgressUpdate: Callback function when progress changes
 */
const ReadingProgress = ({ 
  bookId, 
  currentChapter, 
  currentPage, 
  totalProgress, 
  currentSessionProgress,
  onProgressUpdate = () => {}
}) => {
  const [progress, setProgress] = useState(totalProgress || 0);
  const [localChapter, setLocalChapter] = useState(currentChapter || 'Chapter 1');
  const [localPage, setLocalPage] = useState(currentPage || 1);

  // Update internal state when props change
  useEffect(() => {
    setProgress(totalProgress || 0);
    setLocalChapter(currentChapter || 'Chapter 1');
    setLocalPage(currentPage || 1);
  }, [totalProgress, currentChapter, currentPage]);

  const handleProgressChange = (newProgress) => {
    const updatedProgress = Math.min(100, Math.max(0, newProgress)); // Ensure value is between 0-100
    setProgress(updatedProgress);
    onProgressUpdate({
      bookId,
      progress: updatedProgress,
      chapter: localChapter,
      page: localPage
    });
  };

  const handleChapterChange = (e) => {
    const newChapter = e.target.value;
    setLocalChapter(newChapter);
    onProgressUpdate({
      bookId,
      progress,
      chapter: newChapter,
      page: localPage
    });
  };

  const handlePageChange = (e) => {
    const newPage = parseInt(e.target.value) || 1;
    setLocalPage(newPage);
    onProgressUpdate({
      bookId,
      progress,
      chapter: localChapter,
      page: newPage
    });
  };

  // Calculate chapter progress if we have chapter-specific data
  const chapterProgress = Math.round((localPage / 50) * 100); // Assuming ~50 pages per chapter for example

  return (
    <div className="reading-progress-container">
      <div className="progress-header">
        <h3>Reading Progress</h3>
        <div className="current-location">
          <span className="chapter">Chapter: {localChapter}</span>
          <span className="page">Page: {localPage}</span>
        </div>
      </div>

      <div className="progress-overview">
        <div className="progress-bar-container">
          <div className="progress-labels">
            <span>Overall Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>

        <div className="progress-bar-container">
          <div className="progress-labels">
            <span>Chapter Progress</span>
            <span>{chapterProgress}%</span>
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill chapter-fill" 
              style={{ width: `${chapterProgress}%` }}
            ></div>
          </div>
        </div>
      </div>

      <div className="progress-inputs">
        <div className="input-group">
          <label htmlFor="chapter-input">Chapter:</label>
          <input
            id="chapter-input"
            type="text"
            value={localChapter}
            onChange={handleChapterChange}
            placeholder="Enter chapter"
          />
        </div>

        <div className="input-group">
          <label htmlFor="page-input">Page:</label>
          <input
            id="page-input"
            type="number"
            min="1"
            value={localPage}
            onChange={handlePageChange}
            placeholder="Enter page"
          />
        </div>

        <div className="input-group">
          <label htmlFor="progress-slider">Progress:</label>
          <input
            id="progress-slider"
            type="range"
            min="0"
            max="100"
            value={progress}
            onChange={(e) => handleProgressChange(parseInt(e.target.value))}
          />
        </div>
      </div>

      <div className="progress-actions">
        <button 
          className="btn-progress-save"
          onClick={() => {
            // Call a function to save the current progress to the backend
            console.log(`Saving progress for book ${bookId}: Chapter ${localChapter}, Page ${localPage}, ${progress}%`);
          }}
        >
          Save Progress
        </button>
        <button 
          className="btn-progress-reset"
          onClick={() => {
            setProgress(0);
            setLocalChapter(currentChapter || 'Chapter 1');
            setLocalPage(currentPage || 1);
          }}
        >
          Reset Progress
        </button>
      </div>
    </div>
  );
};

export default ReadingProgress;