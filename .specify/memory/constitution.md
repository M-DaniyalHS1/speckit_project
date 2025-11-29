<!-- 
Sync Impact Report:
- Version change: 1.1.0 (added AI-specific principle)
- Modified principles: Added principle #7 for AI/ML development
- Templates requiring updates: ✅ All checked
- Follow-up TODOs: None
-->
# Qwen Agent Book Constitution

## Core Principles

### 1. Spec-Driven Development (SDD)
All development follows a specification-first approach. Features, tasks, and implementation details must be documented in specs before coding begins. Specifications include acceptance criteria, error handling, and test scenarios to ensure comprehensive coverage.

### 2. Prompt History Records (PHR) for Every User Input
Every user input must be recorded verbatim in a Prompt History Record (PHR). This ensures traceability, reproducibility, and maintains a complete audit trail of all interactions and decisions made during development.

### 3. Architectural Decision Records (ADR) for Significant Decisions
When architecturally significant decisions are made (long-term consequences with multiple viable options), they must be documented in an ADR. This preserves institutional knowledge and provides clear reasoning for future developers.

### 4. Authoritative Source Mandate
MCP tools and CLI commands are prioritized for all information gathering and task execution. Internal knowledge is never assumed; verification through external sources is required for all decisions.

### 5. Small, Testable Changes
Every change should be minimal and testable. Focus on the smallest viable diff that addresses the requirement. Avoid refactoring unrelated code during feature implementation to maintain clarity and reduce risk.

### 6. Human as Tool Strategy
When encountering ambiguous requirements, unforeseen dependencies, architectural uncertainty, or at completion checkpoints, the human user is treated as a specialized tool for clarification and decision-making.

### 7. AI/ML Experimentation and Evaluation
AI/ML components require systematic experimentation with proper evaluation metrics, versioned datasets, and reproducible training procedures. All AI model changes must include performance baselines and regression tests to ensure model quality and prevent degradation.

## Additional Constraints
- All code changes must maintain backward compatibility unless explicitly approved for breaking changes
- Security best practices must be followed, especially when handling sensitive data or tokens
- Code must be platform-agnostic and work across major operating systems (Windows, Linux, macOS)
- Dependencies should be minimal and well-justified
- Documentation must be maintained alongside code changes
- AI model outputs must include confidence scores or uncertainty estimates where appropriate

## Development Workflow
- All features must start with a clear specification
- Implementation follows test-driven development where appropriate
- Code reviews verify compliance with constitution principles
- Every commit message must reference relevant specs, tasks, or decisions
- Continuous integration tests must pass before merging
- AI model changes require evaluation against baseline metrics

## Governance
This constitution supersedes all other development practices within the project. All changes to project practices must align with these principles. Amendments require explicit documentation and approval from project maintainers. All pull requests and code reviews must verify compliance with these principles.

Version: 1.1.0 | Ratified: 2025-11-23 | Last Amended: 2025-11-23