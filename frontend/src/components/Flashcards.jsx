import React, { useState, useEffect } from 'react';
import './Flashcards.css';

/**
 * Interactive flashcard component for the AI-Enhanced Interactive Book Agent.
 * This component provides a flashcard interface for studying with AI-generated content.
 */
const Flashcards = ({ 
  bookId, 
  contentId = null, 
  flashcards = [], 
  cardStyle = 'standard', 
  enableShuffle = true,
  showProgress = true,
  onCardFlip = null,
  onComplete = null 
}) => {
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [shuffledCards, setShuffledCards] = useState([]);
  const [viewedCards, setViewedCards] = useState(new Set());
  const [completed, setCompleted] = useState(false);

  // Shuffle cards when component mounts or when flashcards prop changes
  useEffect(() => {
    if (enableShuffle) {
      // Create a shuffled copy of flashcards
      const shuffled = [...flashcards].sort(() => Math.random() - 0.5);
      setShuffledCards(shuffled);
    } else {
      setShuffledCards([...flashcards]);
    }
    
    // Reset to initial state
    setCurrentCardIndex(0);
    setIsFlipped(false);
    setViewedCards(new Set());
    setCompleted(false);
  }, [flashcards, enableShuffle]);

  // Mark the current card as viewed
  useEffect(() => {
    if (shuffledCards.length > 0) {
      const newViewedCards = new Set(viewedCards);
      newViewedCards.add(currentCardIndex);
      setViewedCards(newViewedCards);
      
      // Check if all cards have been viewed
      if (newViewedCards.size === shuffledCards.length) {
        setCompleted(true);
        if (onComplete && typeof onComplete === 'function') {
          onComplete({
            totalCards: shuffledCards.length,
            viewedCards: Array.from(newViewedCards),
            completionPercentage: 100
          });
        }
      }
    }
  }, [currentCardIndex, shuffledCards]);

  // Navigate to next card
  const nextCard = () => {
    if (currentCardIndex < shuffledCards.length - 1) {
      setCurrentCardIndex(currentCardIndex + 1);
      setIsFlipped(false);
    } else if (currentCardIndex === shuffledCards.length - 1) {
      // If we're at the last card, loop back to first card
      setCurrentCardIndex(0);
      setIsFlipped(false);
    }
  };

  // Navigate to previous card
  const prevCard = () => {
    if (currentCardIndex > 0) {
      setCurrentCardIndex(currentCardIndex - 1);
      setIsFlipped(false);
    } else {
      // If we're at the first card, go to the last card
      setCurrentCardIndex(shuffledCards.length - 1);
      setIsFlipped(false);
    }
  };

  // Handle card flip
  const handleFlip = () => {
    const newIsFlipped = !isFlipped;
    setIsFlipped(newIsFlipped);
    
    // Call the onCardFlip callback if provided
    if (onCardFlip && typeof onCardFlip === 'function') {
      onCardFlip({
        cardIndex: currentCardIndex,
        isFlipped: newIsFlipped,
        card: shuffledCards[currentCardIndex]
      });
    }
  };

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowRight') {
        nextCard();
      } else if (e.key === 'ArrowLeft') {
        prevCard();
      } else if (e.key === ' ') { // Space bar to flip card
        handleFlip();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [currentCardIndex, isFlipped]);

  if (shuffledCards.length === 0) {
    return (
      <div className="flashcards-container">
        <div className="no-cards-message">
          <h3>No Flashcards Available</h3>
          <p>There are no flashcards to display. Try generating flashcards from book content first.</p>
          <button 
            className="generate-cards-button"
            onClick={() => {
              // This would typically trigger an API call to generate flashcards
              if (window.confirm('Would you like to generate flashcards from the current content?')) {
                // In a real implementation, this would make an API call to generate flashcards
                console.log('Generating flashcards for book:', bookId, 'content:', contentId);
              }
            }}
          >
            Generate Flashcards
          </button>
        </div>
      </div>
    );
  }

  const currentCard = shuffledCards[currentCardIndex];
  const progress = Math.round(((viewedCards.size) / shuffledCards.length) * 100);

  return (
    <div className="flashcards-container">
      <div className="flashcards-header">
        <h2>Study Flashcards</h2>
        
        {showProgress && (
          <div className="progress-section">
            <div className="progress-text">
              Card {currentCardIndex + 1} of {shuffledCards.length}
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${progress}%` }} 
              ></div>
            </div>
            <div className="progress-percent">
              {progress}% Complete
            </div>
          </div>
        )}
      </div>

      <div className="flashcard-area">
        <div 
          className={`flashcard ${isFlipped ? 'flipped' : ''} card-style-${cardStyle}`}
          onClick={handleFlip}
        >
          <div className="flashcard-inner">
            <div className="flashcard-front">
              <div className="flashcard-content">
                <h3>Term/Concept</h3>
                <p>{currentCard.front || currentCard.term || currentCard.question}</p>
              </div>
              <div className="flip-hint">
                Click or press SPACE to flip
              </div>
            </div>
            <div className="flashcard-back">
              <div className="flashcard-content">
                <h3>Definition/Explanation</h3>
                <p>{currentCard.back || currentCard.definition || currentCard.answer}</p>
                
                {currentCard.explanation && (
                  <div className="card-explanation">
                    <h4>Explanation:</h4>
                    <p>{currentCard.explanation}</p>
                  </div>
                )}
              </div>
              <div className="flip-hint">
                Click or press SPACE to flip back
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flashcard-controls">
        <button className="control-button prev-button" onClick={prevCard}>
          ← Previous
        </button>
        
        <button className="control-button flip-button" onClick={handleFlip}>
          {isFlipped ? 'Show Question' : 'Show Answer'}
        </button>
        
        <button className="control-button next-button" onClick={nextCard}>
          Next →
        </button>
      </div>

      <div className="card-actions">
        <div className="action-buttons">
          <button 
            className="action-button"
            onClick={() => {
              // Mark as difficult and prioritize showing this card again
              console.log('Marked card as difficult for review:', currentCard);
            }}
            title="Mark as difficult - review again"
          >
            ❗ Difficult
          </button>
          
          <button 
            className="action-button"
            onClick={() => {
              // Mark as known to reduce frequency of showing this card
              console.log('Marked card as known:', currentCard);
            }}
            title="Mark as known - don't show again"
          >
            ✅ Known
          </button>
          
          <button 
            className="action-button"
            onClick={() => {
              // Share this flashcard
              navigator.clipboard.writeText(
                `Flashcard: ${currentCard.front || currentCard.term}\n\nAnswer: ${currentCard.back || currentCard.definition}`
              );
              alert('Flashcard copied to clipboard!');
            }}
            title="Share this flashcard"
          >
            📋 Share
          </button>
        </div>
      </div>

      {completed && (
        <div className="completion-message">
          <h3>Congratulations! 🎉</h3>
          <p>You've reviewed all {shuffledCards.length} flashcards in this deck.</p>
          <div className="completion-actions">
            <button onClick={() => {
              // Reset the flashcards to start over
              setCurrentCardIndex(0);
              setIsFlipped(false);
              setViewedCards(new Set());
              setCompleted(false);
            }}>
              Review Again
            </button>
            <button onClick={() => {
              // Create a new deck with only the difficult cards
              alert('Creating a deck with difficult cards...');
            }}>
              Review Difficult Cards Only
            </button>
            {onComplete && typeof onComplete === 'function' && (
              <button onClick={() => onComplete({ totalCards: shuffledCards.length, viewedCards: Array.from(new Set([...viewedCards, currentCardIndex])), completionPercentage: 100 })}>
                Back to Book
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Component for generating flashcards from content
 */
const FlashcardGenerator = ({ 
  bookId, 
  contentId = null, 
  onFlashcardsGenerated = null,
  maxCards = 20 
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationParams, setGenerationParams] = useState({
    numCards: 10,
    difficulty: 'intermediate', // beginner, intermediate, advanced
    cardType: 'concept-definition', // concept-definition, question-answer, fill-blank
    includeExplanations: true
  });

  const generateFlashcards = async () => {
    setIsGenerating(true);
    
    try {
      // In a real implementation, this would make an API call to generate flashcards
      // For now, I'll simulate by creating dummy data
      const response = await fetch(`/api/flashcards/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}` // Assuming token is stored
        },
        body: JSON.stringify({
          book_id: bookId,
          content_id: contentId,
          params: generationParams
        })
      });

      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      
      if (onFlashcardsGenerated && typeof onFlashcardsGenerated === 'function') {
        onFlashcardsGenerated(data.flashcards);
      }
    } catch (error) {
      console.error('Error generating flashcards:', error);
      alert(`Error generating flashcards: ${error.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="flashcard-generator">
      <h3>Generate Flashcards</h3>
      <div className="generator-controls">
        <div className="control-group">
          <label htmlFor="num-cards">Number of Cards:</label>
          <input
            id="num-cards"
            type="number"
            min="5"
            max={maxCards}
            value={generationParams.numCards}
            onChange={(e) => setGenerationParams({...generationParams, numCards: parseInt(e.target.value) || 10})}
          />
        </div>
        
        <div className="control-group">
          <label htmlFor="difficulty">Difficulty:</label>
          <select
            id="difficulty"
            value={generationParams.difficulty}
            onChange={(e) => setGenerationParams({...generationParams, difficulty: e.target.value})}
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>
        
        <div className="control-group">
          <label htmlFor="card-type">Card Type:</label>
          <select
            id="card-type"
            value={generationParams.cardType}
            onChange={(e) => setGenerationParams({...generationParams, cardType: e.target.value})}
          >
            <option value="concept-definition">Concept/Definition</option>
            <option value="question-answer">Question/Answer</option>
            <option value="fill-blank">Fill in the Blank</option>
          </select>
        </div>
        
        <div className="control-group checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={generationParams.includeExplanations}
              onChange={(e) => setGenerationParams({...generationParams, includeExplanations: e.target.checked})}
            />
            Include Explanations
          </label>
        </div>
      </div>
      
      <button 
        onClick={generateFlashcards}
        disabled={isGenerating}
        className="generate-button"
      >
        {isGenerating ? 'Generating...' : 'Generate Flashcards'}
      </button>
    </div>
  );
};

// Export both components
export { Flashcards, FlashcardGenerator };
export default Flashcards;