# Changelog

All notable changes to Stories will be documented here. The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Added
- Curation of top 500 technology podcasts
- Browse podcasts

### Changed 

### Deprecated 

### Removed 

### Fixed 

### Known issues

### Security

## [0.0.4-alpha] 2025-12-10
### Added 
- Created a custom DAG data flow library to orchestrate data plumbing
- Added Cloudflare R2 cloud storage support for artifacts

### Fixed
- Record duplication on async session.merge during utterance inserts

## [0.0.3-alpha] 2025-12-07
### Added
- Added key word search (sparse retrieval) with elasticsearch to make retrieval better for shorter queries
- Better Player UI for mobile
- Improved search UI 

### Known issues
- Need to review load_utterance_episodes() functions in podcast services
## [0.0.2-alpha] - 2025-12-02
### Added 
- Indexed all utterances across all episodes
---

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