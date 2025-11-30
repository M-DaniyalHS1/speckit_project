import React, { useState, useEffect } from 'react';
import './ExplanationRequest.css';

/**
 * Component for requesting explanations for book content
 * Allows users to request simplified or detailed explanations of book sections
 */
const ExplanationRequest = ({ contentId, bookId, onExplanationReceived }) => {
  const [explanation, setExplanation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [explanationType, setExplanationType] = useState('simple'); // simple, detailed, technical
  const [showExplanation, setShowExplanation] = useState(false);

  /**
   * Request an explanation from the backend
   */
  const requestExplanation = async () => {
    if (!contentId || !bookId) {
      setError('Missing required parameters: contentId and bookId');
      return;
    }

    setLoading(true);
    setError('');
    setExplanation('');

    try {
      // Call the backend API to request explanation
      const response = await fetch('/api/explanations/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`, // Assuming auth token is stored
        },
        body: JSON.stringify({
          book_id: bookId,
          content_id: contentId,
          explanation_type: explanationType,
          context: '' // Additional context could be passed here
        })
      });

      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      setExplanation(data.explanation_text || data.content || 'No explanation received');
      setShowExplanation(true);
      
      // Call the callback function if provided
      if (onExplanationReceived && typeof onExplanationReceived === 'function') {
        onExplanationReceived(data);
      }
    } catch (err) {
      console.error('Error requesting explanation:', err);
      setError(`Failed to get explanation: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="explanation-request-container">
      <div className="explanation-controls">
        <label htmlFor="explanation-type">Explanation Type:</label>
        <select 
          id="explanation-type"
          value={explanationType} 
          onChange={(e) => setExplanationType(e.target.value)}
          disabled={loading}
        >
          <option value="simple">Simple (Easy to Understand)</option>
          <option value="detailed">Detailed (In-Depth)</option>
          <option value="technical">Technical (Expert Level)</option>
        </select>
        
        <button 
          onClick={requestExplanation}
          disabled={loading}
          className="request-explanation-btn"
        >
          {loading ? 'Getting Explanation...' : 'Request Explanation'}
        </button>
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
      </div>

      {showExplanation && (
        <div className="explanation-display">
          <h4>Explanation:</h4>
          <div className="explanation-content">
            {explanation}
          </div>
          <button 
            onClick={() => setShowExplanation(false)}
            className="close-explanation-btn"
          >
            Hide Explanation
          </button>
        </div>
      )}

      <div className="request-help-text">
        <p>Select an explanation type and click "Request Explanation" to get an AI-generated explanation of this content.</p>
      </div>
    </div>
  );
};

export default ExplanationRequest;