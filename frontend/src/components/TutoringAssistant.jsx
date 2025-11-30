import React, { useState, useEffect, useRef } from 'react';
import './TutoringAssistant.css';

/**
 * AI-Powered Tutoring Assistant for the Interactive Book Agent
 * Provides tutoring-style assistance with hints and guided learning for difficult concepts
 */
const TutoringAssistant = ({
  bookId,
  contentId,
  currentQuery = "",
  onHintReceived = null,
  onExplanationReceived = null,
  context = null,
  userId = null
}) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [hintsEnabled, setHintsEnabled] = useState(true);
  const [tutoringMode, setTutoringMode] = useState('guided'); // 'guided', 'exploratory', 'direct'
  const [currentHintLevel, setCurrentHintLevel] = useState(0); // 0 = minimal, 1 = moderate, 2 = substantial
  const [availableHints, setAvailableHints] = useState([]);
  const [showHint, setShowHint] = useState(false);
  const [sessionHistory, setSessionHistory] = useState([]);
  const messagesEndRef = useRef(null);

  // Scroll to bottom of messages
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Function to get tutoring assistance from backend
  const getTutoringAssistance = async (query, hintsRequested = false) => {
    setIsLoading(true);
    
    try {
      const tutoringEndpoint = hintsRequested ? '/api/tutoring/hint' : '/api/tutoring/assistance';
      
      const response = await fetch(tutoringEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify({
          book_id: bookId,
          content_id: contentId,
          query: query || inputValue,
          context: context || '',
          hints_requested: hintsRequested,
          user_id: userId,
          hint_level: currentHintLevel,
          tutoring_mode: tutoringMode
        })
      });

      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      
      // Add response to messages
      const newMessage = {
        id: Date.now(),
        sender: 'tutor',
        content: data.response || data.hint || data.message || 'No response received.',
        timestamp: new Date().toISOString(),
        type: hintsRequested ? 'hint' : 'response'
      };
      
      setMessages(prev => [...prev, newMessage]);
      
      // If it's a hint, also add to available hints
      if (hintsRequested && data.hint) {
        setAvailableHints(prev => [...prev, data.hint]);
        setShowHint(true);
      }
      
      // Call the callback if provided
      if (hintsRequested && onHintReceived && typeof onHintReceived === 'function') {
        onHintReceived(data);
      } else if (!hintsRequested && onExplanationReceived && typeof onExplanationReceived === 'function') {
        onExplanationReceived(data);
      }
      
      // Update session history
      setSessionHistory(prev => [...prev, {
        query: query || inputValue,
        response: data,
        timestamp: new Date().toISOString()
      }]);
      
      setInputValue('');
    } catch (error) {
      console.error('Error getting tutoring assistance:', error);
      
      const errorMessage = {
        id: Date.now(),
        sender: 'system',
        content: `Error: ${error.message}`,
        timestamp: new Date().toISOString(),
        type: 'error'
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!inputValue.trim()) return;
    
    // Add user message to chat
    const userMessage = {
      id: Date.now(),
      sender: 'user',
      content: inputValue,
      timestamp: new Date().toISOString(),
      type: 'query'
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    // Get tutoring assistance
    getTutoringAssistance(inputValue);
  };

  const requestHint = async () => {
    if (!inputValue.trim()) {
      // If no input value, request hint for the last query
      const lastQuery = sessionHistory.length > 0 
        ? sessionHistory[sessionHistory.length - 1].query 
        : currentQuery;
      
      if (!lastQuery) return;
      
      await getTutoringAssistance(lastQuery, true);
      return;
    }
    
    // Add user hint request to chat
    const hintRequestMessage = {
      id: Date.now(),
      sender: 'user',
      content: `Hint for: ${inputValue}`,
      timestamp: new Date().toISOString(),
      type: 'hint_request'
    };
    
    setMessages(prev => [...prev, hintRequestMessage]);
    
    // Request hint from backend
    await getTutoringAssistance(inputValue, true);
  };

  const increaseHintLevel = () => {
    if (currentHintLevel < 2) {
      setCurrentHintLevel(prev => prev + 1);
      
      // Add system message about increased hint level
      const systemMessage = {
        id: Date.now(),
        sender: 'system',
        content: `Hint level increased. More guidance will be provided.`,
        timestamp: new Date().toISOString(),
        type: 'system'
      };
      
      setMessages(prev => [...prev, systemMessage]);
    }
  };

  const decreaseHintLevel = () => {
    if (currentHintLevel > 0) {
      setCurrentHintLevel(prev => prev - 1);
      
      // Add system message about decreased hint level
      const systemMessage = {
        id: Date.now(),
        sender: 'system',
        content: `Hint level decreased. Less guidance will be provided.`,
        timestamp: new Date().toISOString(),
        type: 'system'
      };
      
      setMessages(prev => [...prev, systemMessage]);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setAvailableHints([]);
    setShowHint(false);
    setSessionHistory([]);
  };

  const nextHint = () => {
    if (availableHints.length > currentHintLevel + 1) {
      setCurrentHintLevel(prev => prev + 1);
      setShowHint(true);
    }
  };

  const previousHint = () => {
    if (currentHintLevel > 0) {
      setCurrentHintLevel(prev => prev - 1);
      setShowHint(true);
    }
  };

  return (
    <div className="tutoring-assistant-container">
      <div className="tutoring-header">
        <h2>AI Tutoring Assistant</h2>
        <div className="tutoring-settings">
          <div className="setting-control">
            <label htmlFor="tutoring-mode">Mode:</label>
            <select 
              id="tutoring-mode"
              value={tutoringMode}
              onChange={(e) => setTutoringMode(e.target.value)}
            >
              <option value="guided">Guided (Step-by-step)</option>
              <option value="exploratory">Exploratory (Discovery-based)</option>
              <option value="direct">Direct (Straight to answer)</option>
            </select>
          </div>
          
          <div className="setting-control">
            <label htmlFor="hints-enabled">Hints:</label>
            <input
              id="hints-enabled"
              type="checkbox"
              checked={hintsEnabled}
              onChange={(e) => setHintsEnabled(e.target.checked)}
            />
          </div>
        </div>
      </div>

      <div className="tutoring-chat-area">
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <h3>Welcome to the AI Tutoring Assistant!</h3>
              <p>
                I'm here to help you understand difficult concepts from your book. 
                Ask a question, request a hint, or seek an explanation about any part of the content.
              </p>
              <div className="tutoring-tips">
                <h4>Tips for best results:</h4>
                <ul>
                  <li>Ask specific questions about the content</li>
                  <li>Use the "Request Hint" button when you want guidance without a full answer</li>
                  <li>Adjust the hint level based on how much help you need</li>
                  <li>Switch between tutoring modes depending on your learning style</li>
                </ul>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div 
                key={message.id} 
                className={`message ${message.sender}-message message-${message.type}`}
              >
                <div className="message-content">
                  {message.content}
                </div>
                <div className="message-meta">
                  {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div className="message system-message message-loading">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {showHint && availableHints.length > 0 && (
          <div className="current-hint">
            <div className="hint-content">
              <h4>Hint:</h4>
              <p>{availableHints[currentHintLevel]}</p>
              
              <div className="hint-controls">
                <button 
                  onClick={previousHint}
                  disabled={currentHintLevel === 0}
                  className="hint-nav-button"
                >
                  ← Prev Hint
                </button>
                
                <span className="hint-level-indicator">
                  Level: {currentHintLevel + 1}/{availableHints.length}
                </span>
                
                <button 
                  onClick={nextHint}
                  disabled={currentHintLevel === availableHints.length - 1}
                  className="hint-nav-button"
                >
                  Next Hint →
                </button>
              </div>
            </div>
            
            <button 
              onClick={() => setShowHint(false)}
              className="close-hint-button"
            >
              ×
            </button>
          </div>
        )}
      </div>

      <div className="tutoring-input-area">
        <form onSubmit={handleSubmit} className="tutoring-form">
          <div className="input-and-buttons">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask a question about the content..."
              disabled={isLoading}
              className="tutoring-input"
            />
            
            <div className="tutoring-actions">
              {hintsEnabled && (
                <button
                  type="button"
                  onClick={requestHint}
                  disabled={isLoading || !inputValue.trim()}
                  className="hint-button"
                >
                  💡 Request Hint
                </button>
              )}
              
              <button
                type="submit"
                disabled={isLoading || !inputValue.trim()}
                className="ask-button"
              >
                {isLoading ? 'Thinking...' : 'Ask Tutor'}
              </button>
            </div>
          </div>
        </form>
      </div>

      <div className="tutoring-controls">
        <div className="hint-level-control">
          <button 
            onClick={decreaseHintLevel}
            disabled={currentHintLevel === 0}
            title="Less help"
          >
            -
          </button>
          <span>Hint Level: {currentHintLevel === 0 ? 'Minimal' : currentHintLevel === 1 ? 'Moderate' : 'Substantial'}</span>
          <button 
            onClick={increaseHintLevel}
            disabled={currentHintLevel === 2}
            title="More help"
          >
            +
          </button>
        </div>
        
        <button onClick={clearChat} className="clear-chat-button">
          Clear Chat
        </button>
      </div>

      <div className="tutoring-extras">
        <div className="hint-explanation">
          <h4>About Hints</h4>
          <p>
            Hints are designed to guide your thinking without giving away the full answer. 
            Use the hint level controls to adjust how much guidance you receive.
          </p>
        </div>
        
        <div className="tutoring-modes-explanation">
          <h4>Tutoring Modes</h4>
          <p>
            <strong>Guided:</strong> Step-by-step guidance to help you arrive at the answer yourself<br/>
            <strong>Exploratory:</strong> Questions and prompts to help you discover concepts<br/>
            <strong>Direct:</strong> Straight to explanations and answers when needed
          </p>
        </div>
      </div>
    </div>
  );
};

/**
 * Standalone component to request hints for specific content
 */
const HintRequester = ({ 
  content, 
  onHintReceived,
  bookId = null,
  contentId = null
}) => {
  const [hint, setHint] = useState('');
  const [loading, setLoading] = useState(false);
  const [hintLevel, setHintLevel] = useState('moderate'); // mild, moderate, substantial

  const requestHint = async () => {
    if (!content) return;

    setLoading(true);
    
    try {
      const response = await fetch('/api/tutoring/hint', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify({
          content: content,
          hint_type: 'understanding', // understanding, application, analysis, etc.
          hint_level: hintLevel,
          book_id: bookId,
          content_id: contentId
        })
      });

      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      setHint(data.hint || data.response || 'No hint generated.');
      
      // Call the callback if provided
      if (onHintReceived && typeof onHintReceived === 'function') {
        onHintReceived(data);
      }
    } catch (error) {
      console.error('Error requesting hint:', error);
      setHint(`Error requesting hint: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="hint-requester">
      <div className="hint-controls">
        <label htmlFor="hint-level">Hint Level:</label>
        <select 
          id="hint-level"
          value={hintLevel}
          onChange={(e) => setHintLevel(e.target.value)}
        >
          <option value="mild">Mild (Small nudge)</option>
          <option value="moderate">Moderate (Guidance)</option>
          <option value="substantial">Substantial (Significant help)</option>
        </select>
        
        <button 
          onClick={requestHint}
          disabled={loading}
          className="get-hint-button"
        >
          {loading ? 'Getting Hint...' : 'Get Hint'}
        </button>
      </div>
      
      {hint && (
        <div className="hint-display">
          <h4>Hint:</h4>
          <p>{hint}</p>
        </div>
      )}
    </div>
  );
};

// Export both components
export { TutoringAssistant, HintRequester };
export default TutoringAssistant;