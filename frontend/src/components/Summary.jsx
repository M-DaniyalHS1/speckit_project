import React, { useState, useEffect } from 'react';
import './Summary.css';

/**
 * Component for generating and displaying summaries of book content
 * Allows users to get AI-generated summaries at different levels (chapter, section, paragraph)
 */
const Summary = ({ contentId, bookId, contentType = 'chapter', onSummaryGenerated }) => {
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [summaryType, setSummaryType] = useState('concise'); // concise, detailed, key_points
  const [showSummary, setShowSummary] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');

  /**
   * Request a summary from the backend
   */
  const requestSummary = async () => {
    if (!contentId || !bookId) {
      setError('Missing required parameters: contentId and bookId');
      return;
    }

    setLoading(true);
    setError('');
    setSummary('');

    try {
      // Prepare request body based on summary type
      const requestBody = {
        book_id: bookId,
        content_id: contentId,
        summary_type: summaryType,
        content_type: contentType  // chapter, section, paragraph
      };

      // Add custom prompt if provided
      if (customPrompt.trim()) {
        requestBody.custom_prompt = customPrompt.trim();
      }

      // Call the backend API to request summary
      const response = await fetch('/api/summaries/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`, // Assuming auth token is stored
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      setSummary(data.summary_text || data.content || 'No summary received');
      setShowSummary(true);

      // Call the callback function if provided
      if (onSummaryGenerated && typeof onSummaryGenerated === 'function') {
        onSummaryGenerated(data);
      }
    } catch (err) {
      console.error('Error requesting summary:', err);
      setError(`Failed to get summary: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Toggle showing/hiding the generated summary
   */
  const toggleSummary = () => {
    setShowSummary(!showSummary);
  };

  return (
    <div className="summary-container">
      <div className="summary-controls">
        <div className="summary-options">
          <label htmlFor="summary-type">Summary Type:</label>
          <select 
            id="summary-type"
            value={summaryType} 
            onChange={(e) => setSummaryType(e.target.value)}
            disabled={loading}
          >
            <option value="concise">Concise (Brief Overview)</option>
            <option value="detailed">Detailed (Comprehensive)</option>
            <option value="key_points">Key Points (Bullet Points)</option>
          </select>
        </div>

        <div className="summary-options">
          <label htmlFor="content-type">Content Type:</label>
          <select 
            id="content-type"
            value={contentType} 
            onChange={(e) => setContentType(e.target.value)}
            disabled={loading}
          >
            <option value="paragraph">Paragraph</option>
            <option value="section">Section</option>
            <option value="chapter">Chapter</option>
          </select>
        </div>

        <div className="summary-prompt">
          <label htmlFor="custom-prompt">Custom Instructions (optional):</label>
          <textarea
            id="custom-prompt"
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            placeholder="Example: 'Focus on the main arguments and conclusions'"
            rows="3"
            disabled={loading}
          />
        </div>

        <button 
          onClick={requestSummary}
          disabled={loading}
          className="request-summary-btn"
        >
          {loading ? 'Generating Summary...' : 'Generate Summary'}
        </button>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
      </div>

      {showSummary && (
        <div className="summary-display">
          <div className="summary-header">
            <h4>Summary</h4>
            <button 
              onClick={toggleSummary}
              className="hide-summary-btn"
            >
              Hide
            </button>
          </div>
          <div className="summary-content">
            {summary}
          </div>
          <div className="summary-actions">
            <button 
              className="regenerate-summary-btn"
              onClick={requestSummary}
              disabled={loading}
            >
              Regenerate
            </button>
            <button 
              className="save-summary-btn"
              onClick={() => {
                // Implement saving functionality
                navigator.clipboard.writeText(summary);
                alert('Summary copied to clipboard!');
              }}
            >
              Copy to Clipboard
            </button>
          </div>
        </div>
      )}

      {!showSummary && summary && (
        <button 
          onClick={toggleSummary}
          className="show-summary-btn"
        >
          Show Generated Summary
        </button>
      )}

      <div className="summary-help-text">
        <p>Generate AI-powered summaries of book content at different levels of detail. Choose the summary type that best fits your needs.</p>
      </div>
    </div>
  );
};

// Export a memoized version to optimize rendering
export default React.memo(Summary);