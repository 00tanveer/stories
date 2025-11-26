# Stories - Development Roadmap

## pre-v0.0.alpha-1 
---- Observability ----
- [ ] Set up Posthog across all services to track errors, monitor performance and trigger error alerts
- [ ] Set up Locust for load testing
---- Deployment ----
- [ ] Set up automated deployments for all services in dev and prod environments
- [ ] Document workflows for dev and prod environments (run commands, env variable loading, docker builds, GH action workflow, build commands in prod server)
- [ ] Set up docker workflow for all services in dev DONE
- [ ] Containerize services in prod and run DONE
- [ ] Set up nginx correctly to reverse proxy requests to react app and FastAPI server correctly DONE
- [ ] Containerize Python server, React app and test locally DONE
---- Frontend ----
- [ ] Make search page mobile responsive 
- [ ] Make the Podcast player functional DONE
- [ ] Enrich QA cards with episode data DONE

---- Data pipeline ----
- [ ] Add guest metadata (name, current title, bio)
- [ ] Index all significant utterances
- [ ] Move the transcript files to Cloudfare R2 storage 
- [ ] Big question, small answer - pairs, append more utterances to answers  DONE

- [ ] Fix question duplication error (assemblyAI duplicates remain) DONE
- [ ] Rewrite the retrieval service DONE
- [ ] Create an Infinity embeddings serverless endpoint on Runpod DONE
- [ ] Update Indexer service. Index questions and questions-answer pairs with chromadb DONE
- [ ] Save questions and question-answer pairs to episode tables  DONE
- [ ] Switch to Postgresql and adapt sqlalchemy models to better complement pg DONE
- [ ] Set up sqlalchemy and companion alembic for ORM and migrations DONE
- [ ] Successfully retrieve question utterances and question/answer pairs from available transcripts DONE
- [ ] Write worker for sending transcription requests to AssemblyAI API and fetching them when completed DONE
- [ ] Write data pipeline workers for fetching external data and persisting data in sqlite DONE
- [ ] SQlite database with SQLAlchemy for podcasts, episodes and transcripts - DONE
- [ ] Organize repo into distinct services (1. core services like fetching, transcription, knowledge extraction, indexing; 2. fastapi server 3. data 4. workers) DONE
- [ ] Data scripts to pull curated podcast and their episodes metadata with API, store in json DONE
- [ ] Use the AssemblyAI API for transcribing all episodes ~125 OUT OF ~200 DONE (out of AAI credits) DONE
- [ ] Make connection between Podplayer and Story Results (QA pair cards) seamless DONE
- [ ] Add toolbar (play, insights,) to QA pair cards 
- [ ] Write the backend service for pulling podcast data with Podcastindex API. Enrich curated collection of 20 episodes (The Perterman Pod) with an automated script DONE
## v0.0.1 (Current) ✓
- [x] Search interface DONE
- [x] Storypod Player DONE
- [x] 200+ interviews loaded DONE

## v0.1.0 (Storypod player features)
- [ ] Storypod smart seek
- [ ] 
## v0.0.2 (Get early users)
- [ ] Email newsletter
- [ ] Generate micro-blogs with AI

## Hot ideas - parked
- [ ] Answer summary for each query (for example - what does a top 1% software engineer look like? answer - look at the conversation segments, their metadata and generate a response)
- [ ] Metadata chat agent (to retrieve answers based on the current context of the React app - the podcast guest, topic, etc)
- [ ] Questions from audience -> send to podcast authors 
- [ ] Index per entity (person, company)
- [ ] Mashups - Make your own hour long pod mashup of brilliant bits from thousands of podcasts
- [ ] Get words from different podcast episodes and string them together to make rap songs


// Git tagging - mark releases (you have the changelog.md to contain the updates you released)
// git tag -a v0.0.1 -m "Initial MVP release"
// git push origin v0.0.1

// Release process checklist
Before releasing v0.0.2:
bash# 1. Update version
# Edit version.json: "0.0.1" → "0.0.2"

# 2. Update changelog
# Add new section to CHANGELOG.md

# 3. Commit version bump
git add version.json CHANGELOG.md
git commit -m "Bump version to 0.0.2"

# 4. Tag release
git tag -a v0.0.2 -m "Bug fixes and improvements"
git push origin main --tags

# 5. Deploy
# (your deploy script here)
