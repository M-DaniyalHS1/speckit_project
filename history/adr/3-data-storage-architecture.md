# ADR-3: Data Storage Architecture

**Status**: Accepted  
**Date**: 2025-11-23

## Context

The AI-Enhanced Interactive Book Agent requires multiple types of data storage:
- User accounts and preferences (structured data with ACID properties)
- Book content and metadata
- Embeddings for RAG functionality (vector storage)
- User sessions and reading progress
- Generated learning materials and AI interactions

The solution must support concurrent users (up to 600), handle large documents (up to 700 pages), and provide efficient retrieval for semantic search.

## Decision

We will implement a hybrid storage approach:
- **PostgreSQL**: For user data, session management, and structured book metadata
- **ChromaDB**: As a vector database for storing embeddings and enabling semantic search
- **File System**: For storing original book files and processed content chunks

## Alternatives Considered

- **MongoDB**: Flexible schema but less suitable for relational data like user accounts
- **Redis**: Excellent performance but less persistence guarantees for user data
- **Elasticsearch**: Traditional search approach but less suitable for semantic similarity
- **Single database approach**: Could simplify operations but no single solution adequately addresses all storage needs

## Consequences

### Positive
- PostgreSQL provides ACID compliance essential for user data and session tracking
- ChromaDB offers specialized vector storage for efficient semantic search
- Clear separation of concerns between different data types
- Leveraging specialized storage engines for their respective strengths
- Scalability for both structured data and vector search requirements

### Negative
- Increased operational complexity with multiple storage systems
- Additional network overhead between storage systems
- More complex backup and maintenance procedures
- Potential consistency challenges between storage systems

## References

- research.md - Decision: User Session Management and RAG Implementation
- data-model.md - Complete data model definition
- plan.md - Technical Context section