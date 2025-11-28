import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import ReadingProgress from '../components/ReadingProgress';
import '../services/api'; // Import the API service
import './BookReader.css'; // Optional CSS file for styling

/**
 * BookReader Component
 * Main page for reading books with progress tracking and session restoration
 */
const BookReader = () => {
  const { bookId } = useParams();
  const [bookContent, setBookContent] = useState('');
  const [currentChapter, setCurrentChapter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [overallProgress, setOverallProgress] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  // Function to fetch the book content
  const fetchBookContent = async () => {
    try {
      // In a real implementation, this would fetch from the backend API
      // Example: const response = await api.get(`/books/${bookId}/content`);
      console.log(`Fetching content for book ID: ${bookId}`);
      
      // Mock content for demonstration
      setBookContent(`
        Chapter 1: Introduction to the Reading App
        This is the beginning of the book. Here we introduce the main concepts and ideas.
        The reading experience is enhanced with progress tracking and session management.
        
        As we continue reading, we track our location in the book and maintain a consistent experience across sessions.
        
        The application remembers exactly where you left off, and presents the content in an easy-to-read format.
        
        Chapter 2: Deep Dive
        In this chapter, we'll explore the advanced features of the reading application.
        We'll discuss how the progress tracking works and the benefits of session restoration.
        
        The app remembers your preferences and reading style to enhance your experience.
        
        Chapter 3: Advanced Features
        Here we'll go over the more advanced features of the reading application.
        These features include search, bookmarking, and AI-powered explanations.
      `);
      
      setCurrentChapter('Chapter 1');
      setLoading(false);
    } catch (err) {
      setError('Failed to load book content');
      setLoading(false);
      console.error('Error fetching book content:', err);
    }
  };

  // Function to restore reading session
  const restoreReadingSession = async () => {
    try {
      // First, check if there's an existing session for this book
      // In a real implementation, this would call our backend API
      console.log(`Attempting to restore session for book ID: ${bookId}`);
      
      // Mock restoration logic - in real implementation, fetch from backend
      const mockSession = {
        session_id: 'mock-session-id',
        current_location: 'Chapter 2:15:1', // Format: chapter:page:paragraph
        current_position_percent: 45,
        last_accessed_at: new Date().toISOString()
      };
      
      setSessionId(mockSession.session_id);
      
      // Parse the location
      const locationParts = mockSession.current_location.split(':');
      if (locationParts.length >= 2) {
        setCurrentChapter(locationParts[0]);
        setCurrentPage(parseInt(locationParts[1]) || 1);
      }
      
      setOverallProgress(mockSession.current_position_percent);
      
      console.log('Session restored:', mockSession);
    } catch (err) {
      console.error('Error restoring session:', err);
      // If session restoration fails, start from the beginning
      setCurrentChapter('Chapter 1');
      setCurrentPage(1);
      setOverallProgress(0);
    }
  };

  // Function to initialize a new reading session
  const initializeReadingSession = async () => {
    try {
      // In a real implementation, this would call our backend API
      // Example: const response = await api.post('/sessions/', { book_id: bookId });
      console.log(`Initializing session for book ID: ${bookId}`);
      
      const mockSession = {
        id: 'new-session-id',
        book_id: bookId,
        current_location: '1:1:1', // chapter:page:paragraph
        current_position_percent: 0
      };
      
      setSessionId(mockSession.id);
      setCurrentChapter('Chapter 1');
      setCurrentPage(1);
      setOverallProgress(0);
      
      console.log('New session created:', mockSession);
    } catch (err) {
      console.error('Error initializing session:', err);
    }
  };

  // Function to update progress in the backend
  const updateProgress = async (progressData) => {
    try {
      // In a real implementation, this would call our backend API
      // Example: await api.put(`/sessions/${sessionId}/position`, progressData);
      console.log('Updating progress:', progressData);
    } catch (err) {
      console.error('Error updating progress:', err);
    }
  };

  // Effect to restore session when component mounts
  useEffect(() => {
    const loadAndRestoreSession = async () => {
      setLoading(true);
      await fetchBookContent();
      
      // Try to restore the reading session
      await restoreReadingSession();
      
      // If no session was found, initialize a new one
      if (!sessionId) {
        await initializeReadingSession();
      }
      
      setLoading(false);
    };

    loadAndRestoreSession();
  }, [bookId]);

  // Handle progress updates from the ReadingProgress component
  const handleProgressUpdate = (progressData) => {
    updateProgress({
      current_location: `${progressData.chapter}:${progressData.page}:1`,
      position_percent: progressData.progress
    });
    
    setCurrentChapter(progressData.chapter);
    setCurrentPage(progressData.page);
    setOverallProgress(progressData.progress);
  };

  // Render loading state
  if (loading) {
    return (
      <div className="book-reader-container">
        <div className="loading">Loading book content...</div>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="book-reader-container">
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  // Parse the book content into chapters for display
  const chapters = bookContent.split(/(\n\s*\n\s*Chapter \d+:?)/).filter(part => part.trim() !== '');
  const currentChapterIndex = chapters.findIndex(part => 
    part.includes(currentChapter)
  );

  const currentChapterContent = chapters[currentChapterIndex + 1] || '';

  return (
    <div className="book-reader-container">
      <header className="book-header">
        <h1>Book Reader</h1>
        <h2>Book ID: {bookId}</h2>
      </header>

      <div className="reading-interface">
        <aside className="progress-panel">
          <ReadingProgress 
            bookId={bookId}
            currentChapter={currentChapter}
            currentPage={currentPage}
            totalProgress={overallProgress}
            onProgressUpdate={handleProgressUpdate}
          />
        </aside>

        <main className="book-content">
          <div className="chapter-header">
            <h2>{currentChapter}</h2>
            <div className="chapter-navigation">
              <button 
                onClick={() => {
                  const newPage = Math.max(1, currentPage - 1);
                  setCurrentPage(newPage);
                  updateProgress({
                    current_location: `${currentChapter}:${newPage}:1`,
                    position_percent: Math.max(0, overallProgress - 2)
                  });
                }}
                disabled={currentPage <= 1}
              >
                Previous Page
              </button>
              <span>Page {currentPage}</span>
              <button 
                onClick={() => {
                  const newPage = currentPage + 1;
                  setCurrentPage(newPage);
                  updateProgress({
                    current_location: `${currentChapter}:${newPage}:1`,
                    position_percent: Math.min(100, overallProgress + 2)
                  });
                }}
              >
                Next Page
              </button>
            </div>
          </div>
          
          <div className="chapter-content">
            {currentChapterContent}
          </div>
        </main>
      </div>
    </div>
  );
};

export default BookReader;