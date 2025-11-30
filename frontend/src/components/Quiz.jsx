import React, { useState, useEffect } from 'react';
import './Quiz.css';

/**
 * Interactive quiz component for the AI-Enhanced Interactive Book Agent.
 * This component handles displaying quiz questions, collecting answers, and providing feedback.
 */
const Quiz = ({ 
  quizId = null, 
  bookId, 
  chapterId = null, 
  questions = [], 
  onComplete = null,
  showInstantFeedback = false,
  allowRetries = true
}) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState(Array(questions.length).fill(null));
  const [quizCompleted, setQuizCompleted] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(null); // null means no timer
  const [score, setScore] = useState(null);
  const [showResults, setShowResults] = useState(false);

  // Timer effect
  useEffect(() => {
    let timer;
    if (timeRemaining !== null && timeRemaining > 0 && !quizCompleted) {
      timer = setTimeout(() => setTimeRemaining(timeRemaining - 1), 1000);
    } else if (timeRemaining === 0) {
      // Time's up - submit the quiz automatically
      handleSubmitQuiz();
    }
    return () => clearTimeout(timer);
  }, [timeRemaining, quizCompleted]);

  // Format time remaining for display
  const formatTime = (seconds) => {
    if (seconds === null) return '';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle answer selection
  const handleAnswerSelect = (questionIndex, optionIndex, isMultipleChoice = false) => {
    if (quizCompleted) return;

    const newAnswers = [...userAnswers];
    
    if (isMultipleChoice) {
      // For multiple selection
      if (!Array.isArray(newAnswers[questionIndex])) {
        newAnswers[questionIndex] = [];
      }
      
      const currentSelections = newAnswers[questionIndex];
      if (currentSelections.includes(optionIndex)) {
        // Unselect if already selected
        newAnswers[questionIndex] = currentSelections.filter(i => i !== optionIndex);
      } else {
        // Select if not already selected
        newAnswers[questionIndex] = [...currentSelections, optionIndex];
      }
    } else {
      // For single selection or text answers
      newAnswers[questionIndex] = optionIndex; // For MCQ, this is the option index
      // For text-based questions, we'd need to handle differently
    }

    setUserAnswers(newAnswers);
  };

  // Handle text answer change
  const handleTextAnswerChange = (questionIndex, textValue) => {
    if (quizCompleted) return;

    const newAnswers = [...userAnswers];
    newAnswers[questionIndex] = textValue;
    setUserAnswers(newAnswers);
  };

  // Navigate to next question
  const goToNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  // Navigate to previous question
  const goToPreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  // Submit the quiz
  const handleSubmitQuiz = async () => {
    // Calculate score
    let correctCount = 0;
    questions.forEach((question, index) => {
      if (question.correct_answer !== undefined && userAnswers[index] !== null) {
        if (typeof question.correct_answer === 'number') {
          // Single selection question
          if (userAnswers[index] === question.correct_answer) {
            correctCount++;
          }
        } else if (Array.isArray(question.correct_answer)) {
          // Multiple selection question
          const userSelection = Array.isArray(userAnswers[index]) ? userAnswers[index] : [];
          const isCorrect = 
            userSelection.length === question.correct_answer.length &&
            userSelection.every(selection => question.correct_answer.includes(selection));
          
          if (isCorrect) {
            correctCount++;
          }
        } else if (typeof question.correct_answer === 'string') {
          // Text-based question - could implement more sophisticated matching
          if (userAnswers[index]?.toLowerCase().includes(question.correct_answer.toLowerCase())) {
            correctCount++;
          }
        }
      }
    });

    const calculatedScore = Math.round((correctCount / questions.length) * 100);
    setScore(calculatedScore);
    setQuizCompleted(true);

    // Report results to parent component if provided
    if (onComplete && typeof onComplete === 'function') {
      onComplete({
        quizId,
        bookId,
        chapterId,
        score: calculatedScore,
        totalQuestions: questions.length,
        correctAnswers: correctCount,
        timeTaken: null, // Would need timer implementation to track this
        answers: userAnswers
      });
    }
  };

  // Reset quiz to try again
  const handleRetakeQuiz = () => {
    setUserAnswers(Array(questions.length).fill(null));
    setCurrentQuestionIndex(0);
    setQuizCompleted(false);
    setScore(null);
    setTimeRemaining(null); // Reset timer if applicable
    setShowResults(false);
  };

  // Get current question
  const currentQuestion = questions[currentQuestionIndex];

  // Check if user answered the current question
  const isCurrentAnswered = userAnswers[currentQuestionIndex] !== null;

  if (questions.length === 0) {
    return (
      <div className="quiz-container">
        <div className="no-questions-message">
          <h3>No Questions Available</h3>
          <p>No questions have been loaded for this quiz. Please try again later or check back for new content.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="quiz-container">
      {!quizCompleted ? (
        <div className="quiz-active">
          {/* Quiz header */}
          <div className="quiz-header">
            <div className="quiz-info">
              <h2>Chapter Quiz</h2>
              {quizId && <p className="quiz-id">Quiz ID: {quizId}</p>}
            </div>
            
            {timeRemaining !== null && (
              <div className={`timer ${timeRemaining < 60 ? 'time-warning' : ''}`}>
                Time Remaining: <span className="time-value">{formatTime(timeRemaining)}</span>
              </div>
            )}
            
            <div className="progress">
              Question {currentQuestionIndex + 1} of {questions.length}
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Question display */}
          <div className="question-container">
            <div className="question-header">
              <h3>{currentQuestion.question}</h3>
              {currentQuestion.type && (
                <span className="question-type-badge">{currentQuestion.type}</span>
              )}
            </div>

            {/* Answer options */}
            <div className="answer-options">
              {currentQuestion.options ? (
                // Multiple choice or multiple select
                currentQuestion.options.map((option, optionIndex) => {
                  const isSelected = Array.isArray(userAnswers[currentQuestionIndex])
                    ? userAnswers[currentQuestionIndex].includes(optionIndex)
                    : userAnswers[currentQuestionIndex] === optionIndex;
                  
                  return (
                    <div 
                      key={optionIndex}
                      className={`answer-option ${
                        isSelected ? 'selected' : ''
                      } ${showInstantFeedback && currentQuestion.correct_answer?.includes(optionIndex) ? 'correct-option' : ''}`}
                      onClick={() => handleAnswerSelect(currentQuestionIndex, optionIndex, currentQuestion.isMultipleSelection)}
                    >
                      <div className="option-selector">
                        {currentQuestion.isMultipleSelection ? (
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => {}}
                          />
                        ) : (
                          <input
                            type="radio"
                            name={`question-${currentQuestionIndex}`}
                            checked={isSelected}
                            onChange={() => {}}
                          />
                        )}
                      </div>
                      <div className="option-text">{option}</div>
                    </div>
                  );
                })
              ) : (
                // Text-based question
                <div className="text-answer">
                  <textarea
                    value={userAnswers[currentQuestionIndex] || ''}
                    onChange={(e) => handleTextAnswerChange(currentQuestionIndex, e.target.value)}
                    placeholder="Type your answer here..."
                    disabled={quizCompleted}
                  />
                </div>
              )}
            </div>

            {/* Feedback for current question if enabled */}
            {showInstantFeedback && isCurrentAnswered && currentQuestion.correct_answer !== undefined && (
              <div className="feedback">
                {typeof currentQuestion.correct_answer === 'number' ? (
                  <div className={`instant-feedback ${userAnswers[currentQuestionIndex] === currentQuestion.correct_answer ? 'correct' : 'incorrect'}`}>
                    {userAnswers[currentQuestionIndex] === currentQuestion.correct_answer
                      ? currentQuestion.explanation || "Correct!"
                      : currentQuestion.explanation || "Incorrect. Try again."}
                  </div>
                ) : Array.isArray(currentQuestion.correct_answer) ? (
                  <div className={`instant-feedback ${currentQuestion.correct_answer.every(a => userAnswers[currentQuestionIndex]?.includes(a)) ? 'correct' : 'incorrect'}`}>
                    {currentQuestion.correct_answer.every(a => userAnswers[currentQuestionIndex]?.includes(a))
                      ? currentQuestion.explanation || "Correct!"
                      : currentQuestion.explanation || "Incorrect. Try again."}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Navigation controls */}
          <div className="quiz-navigation">
            <button
              onClick={goToPreviousQuestion}
              disabled={currentQuestionIndex === 0}
              className="nav-button prev-button"
            >
              Previous
            </button>

            {currentQuestionIndex < questions.length - 1 ? (
              <button
                onClick={goToNextQuestion}
                disabled={!isCurrentAnswered}
                className="nav-button next-button"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSubmitQuiz}
                disabled={!isCurrentAnswered}
                className="nav-button submit-button"
              >
                Submit Quiz
              </button>
            )}
          </div>
        </div>
      ) : (
        /* Quiz results view */
        <div className="quiz-results">
          <h2>Quiz Completed!</h2>
          <div className="score-section">
            <div className="score-circle">
              <span className="score-value">{score}%</span>
            </div>
            <p>Your Score: {score}% ({Math.round((score/100) * questions.length)}/{questions.length} correct)</p>
          </div>

          {showResults && (
            <div className="detailed-results">
              <h3>Detailed Results</h3>
              {questions.map((question, index) => {
                const isCorrect = typeof question.correct_answer === 'number' 
                  ? userAnswers[index] === question.correct_answer
                  : Array.isArray(question.correct_answer)
                  ? question.correct_answer.every(a => userAnswers[index]?.includes(a)) && userAnswers[index]?.every(a => question.correct_answer.includes(a))
                  : userAnswers[index]?.toLowerCase().includes(question.correct_answer.toLowerCase());
                
                return (
                  <div key={index} className={`result-question ${isCorrect ? 'correct' : 'incorrect'}`}>
                    <h4>Question {index + 1}: {question.question}</h4>
                    <p>Your answer: {userAnswers[index] !== null ? 
                      (Array.isArray(question.options) ? question.options[userAnswers[index]] : userAnswers[index]) 
                      : 'No answer selected'}</p>
                    {!isCorrect && question.explanation && (
                      <div className="explanation">
                        <p><strong>Explanation:</strong> {question.explanation}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          <div className="quiz-actions">
            <button onClick={() => setShowResults(!showResults)}>
              {showResults ? 'Hide Details' : 'Show Details'}
            </button>
            
            {allowRetries && (
              <button onClick={handleRetakeQuiz}>
                Retake Quiz
              </button>
            )}
            
            {onComplete && typeof onComplete === 'function' && (
              <button onClick={() => onComplete(null)}>Back to Book</button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Quiz;