# Changelog

All notable changes to Stories will be documented here. The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Added

### Changed 

### Deprecated 

### Removed 

### Fixed 

### Known issues

### Security
## [0.0.1-alpha] - 2025-12-01
### Added
- An ETL pipeline to fetch data from Podcastindex API
- Transcribe audio with AssemblyAI API 
- Load processed data into postgres and finally 
- Index podcast question-answers with Runpod's Infinity Serverless Endpoint and store embeddings with metadata in ChromaDB vector database
- Python FastAPI web server
- SQLAlchemy ORM with alembic migrations tool for Python backend
- Semantic search engine UI for question-answer segments
- React web podcast player

### Known Issues
- Non-significant utterances end up in search results 
- Loader animation not implemented in podcast player play button on play button click in QA card