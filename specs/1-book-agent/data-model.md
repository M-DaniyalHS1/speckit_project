# Data Model for AI-Enhanced Interactive Book Agent

## User Entity
- **user_id**: UUID (Primary Key) - Globally unique identifier
- **email**: String (Unique) - For login and verification
- **password_hash**: String - Securely hashed password
- **created_at**: DateTime - Account creation timestamp
- **preferences**: JSON - User preferences (explanation depth, etc.)
- **gdpr_consent**: Boolean - GDPR compliance flag

## Book Entity
- **book_id**: UUID (Primary Key) - Unique identifier per user-book combination
- **user_id**: UUID (Foreign Key) - Owner of the book instance
- **title**: String - Book title
- **author**: String - Book author
- **file_path**: String - Path to uploaded file
- **file_format**: String - Format (PDF, EPUB, etc.)
- **upload_date**: DateTime - When book was uploaded
- **metadata**: JSON - Additional book metadata

## ReadingSession Entity
- **session_id**: UUID (Primary Key) - Unique session identifier
- **user_id**: UUID (Foreign Key) - Associated user
- **book_id**: UUID (Foreign Key) - Associated book
- **current_location**: String - Current position (chapter:page:paragraph)
- **start_time**: DateTime - Session start
- **last_access**: DateTime - Last interaction timestamp
- **is_active**: Boolean - Whether session is currently active

## BookContent Entity
- **content_id**: UUID (Primary Key) - Unique content identifier
- **book_id**: UUID (Foreign Key) - Associated book
- **chunk_id**: String - Identifier for the content chunk
- **content**: Text - The actual text content
- **page_number**: Integer - Page where this content appears
- **section_title**: String - Section/chapter title
- **embedding**: Vector - Embedding vector for RAG search

## Query Entity
- **query_id**: UUID (Primary Key) - Unique query identifier
- **user_id**: UUID (Foreign Key) - User who made the query
- **book_id**: UUID (Foreign Key) - Book the query relates to
- **query_text**: Text - The user's query
- **timestamp**: DateTime - When the query was made
- **query_type**: String - Type (search, explanation, summary, etc.)

## Explanation Entity
- **explanation_id**: UUID (Primary Key) - Unique explanation identifier
- **query_id**: UUID (Foreign Key) - Associated query
- **source_chunks**: Array[UUID] - References to source content chunks
- **content**: Text - The explanation content
- **confidence_score**: Float - Confidence level of the explanation
- **citations**: JSON - Citations to book sections

## LearningMaterial Entity
- **material_id**: UUID (Primary Key) - Unique material identifier
- **user_id**: UUID (Foreign Key) - Owner of the material
- **book_id**: UUID (Foreign Key) - Associated book
- **material_type**: String - Type (quiz, flashcard, note, etc.)
- **title**: String - Title of the material
- **content**: JSON - The actual learning material content
- **created_at**: DateTime - Creation timestamp
- **associated_chunks**: Array[UUID] - Related content chunks