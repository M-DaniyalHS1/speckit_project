import React, { useState, useEffect } from 'react';
import './ResumeReading.css';

/**
 * ResumeReading Component
 * UI component that allows users to easily resume reading from their last position
 * 
 * Props:
 * - bookId: ID of the book
 * - lastPosition: Last reading position (chapter:page:paragraph format)
 * - lastReadTime: Time when the user last read
 * - progress: Overall progress percentage
 * - onResume: Callback function when user clicks resume
 */
const ResumeReading = ({ 
  bookId, 
  lastPosition = '1:1:1', 
  lastReadTime, 
  progress = 0, 
  onResume = () => {} 
}) => {
  const [position, setPosition] = useState({ chapter: '1', page: '1', paragraph: '1' });
  const [timeAgo, setTimeAgo] = useState('');

  // Parse the last position when component mounts or when lastPosition changes
  useEffect(() => {
    if (lastPosition) {
      const [chapter, page, paragraph] = lastPosition.split(':');
      setPosition({
        chapter: chapter || '1',
        page: page || '1',
        paragraph: paragraph || '1'
      });
    }
  }, [lastPosition]);

  // Calculate time ago when component mounts or when lastReadTime changes
  useEffect(() => {
    if (lastReadTime) {
      const date = new Date(lastReadTime);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffDays > 0) {
        setTimeAgo(`${diffDays} day${diffDays > 1 ? 's' : ''} ago`);
      } else if (diffHours > 0) {
        setTimeAgo(`${diffHours} hour${diffHours > 1 ? 's' : ''} ago`);
      } else if (diffMins > 0) {
        setTimeAgo(`${diffMins} minute${diffMins > 1 ? 's' : ''} ago`);
      } else {
        setTimeAgo('Just now');
      }
    }
  }, [lastReadTime]);

  const handleResumeClick = () => {
    onResume({
      bookId,
      position: lastPosition,
      chapter: position.chapter,
      page: position.page
    });
  };

  return (
    <div className="resume-reading-container">
      <div className="resume-header">
        <h3>Continue Reading</h3>
        <div className="progress-indicator">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <span className="progress-text">{progress}% complete</span>
        </div>
      </div>

      <div className="resume-content">
        <div className="position-info">
          <div className="location">
            <strong>Chapter {position.chapter}</strong>, Page {position.page}
          </div>
          {lastReadTime && (
            <div className="timestamp">
              Last read: {timeAgo}
            </div>
          )}
        </div>

        <div className="resume-actions">
          <button 
            className="btn-resume"
            onClick={handleResumeClick}
          >
            Resume Reading
          </button>
          
          <button 
            className="btn-start-over"
            onClick={() => {
              onResume({
                bookId,
                position: '1:1:1',
                chapter: '1',
                page: '1'
              });
            }}
          >
            Start from Beginning
          </button>
        </div>
      </div>

      <div className="book-summary">
        <p>Return to where you left off to maintain your reading momentum and continue your learning journey.</p>
      </div>
    </div>
  );
};

export default ResumeReading;