import chromadb
import json
import uuid
from datetime import datetime
from app.api.runpod_serverless import infinity_embeddings
from app.db.session import AsyncSessionLocal
from app.db.data_models.episode import Episode 
from app.db.data_models.podcast import Podcast
from app.db.data_models.transcript import Transcript
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from tqdm import tqdm
import os
from dotenv import load_dotenv

ENV = os.getenv("APP_ENV", "development")  # default to development

if ENV == "development":
    load_dotenv(".env.development")

class Indexer:
    '''This Indexer class has the abilities to index
        anything inside the Stories project with ChromaDB
    Args:
        chroma_db_dir: Root data folder path.
        subfolder: Subfolder containing JSON files with questions.
        use_remote: Whether to use remote Ollama host.
    '''
    # Indexer class attributes
    EMBEDDING_MODEL = 'BAAI/bge-base-en-v1.5'
    
    def __init__(self):
        print(os.getenv("CHROMA_HOST")) # The print output is chroma 
        print(os.getenv("CHROMA_PORT")) # The print output is 8001

        self.chroma_client = chromadb.HttpClient(host=os.getenv("CHROMA_HOST"), port=os.getenv("CHROMA_PORT"))
        self.embeddings_generator = infinity_embeddings(self.EMBEDDING_MODEL)
        self.chroma_coll_config = {
            "hnsw": {
                "space": "cosine",
                "ef_construction": 200,
                "ef_search": 10,
            }
        }
        # collections
        self.qa_collection_name = "episode_qa_pairs"
        self.utterances_collection_name = "utterances"
        self.qa_collection = None
        self.utterances_collection = None
        self.batch_size = 50
    
    def init_chroma_collection(self):
        self.qa_collection = self.chroma_client.get_or_create_collection(
            name=self.qa_collection_name,
            configuration=self.chroma_coll_config,
            metadata = {
                "description": "Question-answer exchanges in every podcast episode. Metadata includes timestamps",
                "created": str(datetime.now())
            }
        )
        self.utterances_collection = self.chroma_client.get_or_create_collection(
            name=self.utterances_collection_name,
            configuration=self.chroma_coll_config,
            metadata = {
                "description": "Utterances from podcast episodes. Metadata includes speaker labels and timestamps",
                "created": str(datetime.now())
            }
        )
    def get_collection(self, name):
        return self.chroma_client.get_collection(name)
    def sanitize_metadata(self, meta: dict):
        clean = {}
        for k, v in meta.items():
            if v is None:
                clean[k] = ""
                continue

            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
                continue
            if isinstance(v, datetime):
                clean[k] = v.isoformat()
                continue
            if isinstance(v, bytes):
                clean[k] = v.decode("utf-8", errors="ignore")
                continue
            if isinstance(v, (list, dict)):
                clean[k] = json.dumps(v)
                continue
            clean[k] = str(v)

        return clean
    
    async def load_all_question_episodes(self):
        episodes = []
        async with AsyncSessionLocal() as session:
            async with session.begin():
                stmt = (
                    select(Episode, Podcast.author, Podcast.title)
                    .join(Episode.podcast)
                    .where(
                        and_(
                            Episode.host_questions != [],
                            Episode.question_answers != [],
                        )
                    )
                )
                result = await session.execute(stmt)
                rows = result.all()

                for row in rows:
                    episode, author, podcast_title = row
                    episodes.append({
                        "id": episode.id,
                        "author": author,
                        "title": episode.title,
                        "description": episode.description,
                        "podcast_url": episode.podcast_url,
                        "podcast_title": podcast_title,
                        "episode_image": episode.episode_image,
                        "enclosure_url": episode.enclosure_url,
                        "duration": episode.duration,
                        "date_published": episode.date_published,
                        "questions": episode.host_questions,
                        "question_answers": episode.question_answers,
                    })
        return episodes
    
    async def load_all_episode_utterances(self):
        episodes = []
        async with AsyncSessionLocal() as session:
            async with session.begin():
                stmt = (
                    select(Episode, Podcast.author, Podcast.title)
                    .join(Episode.podcast)
                    .join(Episode.transcript)
                    .options(
                        # load transcript + nested utterances
                        selectinload(Episode.transcript)
                            .selectinload(Transcript.utterances)
                    )
                )

                result = await session.execute(stmt)
                rows = result.all()

                for row in rows:
                    episode, author, podcast_title = row

                    # extract utterances safely
                    utterances = []
                    if episode.transcript and episode.transcript.utterances:
                        utterances = [
                            {
                                "id": u.id,
                                "start": u.start,
                                "end": u.end,
                                "confidence": u.confidence,
                                "speaker": u.speaker,
                                "text": u.text,
                            }
                            for u in episode.transcript.utterances
                        ]

                    episodes.append({
                        "id": episode.id,
                        "author": author,
                        "title": episode.title,
                        "description": episode.description,
                        "podcast_url": episode.podcast_url,
                        "podcast_title": podcast_title,
                        "episode_image": episode.episode_image,
                        "enclosure_url": episode.enclosure_url,
                        "duration": episode.duration,
                        "date_published": episode.date_published,

                        # your custom fields
                        "utterances": utterances,
                    })
        episodes = [e for e in episodes if e['utterances']!=[]]
        return episodes
    async def embed_batch(self, docs):
        """
        Call Runpod's Infinity Embeddings Serverless API to embed a batch of documents.
        """
        res = self.embeddings_generator.get_embeddings(docs)

        embeddings = res.get("embeddings")
        if embeddings is None:
            raise RuntimeError("❌ Runpod returned no embeddings field.")

        return embeddings
    def filtered_episodes_to_index(self, all_episodes, qa_collection):
        existing = qa_collection.get(include=["metadatas"])

        indexed_episode_ids = set(
            m["id"] for m in existing.get("metadatas", []) if m and "id" in m
        )
        episodes_to_process = [
            ep for ep in all_episodes
            if ep["id"] not in indexed_episode_ids
        ]
        episodes_to_process
        return episodes_to_process

    async def upsert_qa_collection(self):
        print("Starting QA indexing...")

        if self.qa_collection is None:
            self.init_chroma_collection()

        all_episodes = await self.load_all_question_episodes()
        print("Loaded", len(all_episodes), "episodes")

        episodes = self.filtered_episodes_to_index(all_episodes, self.qa_collection)
        print("Episodes remaining to index: ", len(episodes))
        total_qa = sum(len(ep["question_answers"]) for ep in episodes)
        print(f"Total question-answer pairs to index: {total_qa}")

        BATCH_SIZE = 100   # sweet spot for Ollama performance

        batch_ids = []
        batch_docs = []
        batch_metas = []

        for episode in tqdm(episodes, desc="Processing episodes"):
            episode_meta_raw = {
                k: v for k, v in episode.items()
                if k not in ("questions", "question_answers")
            }
            episode_meta = self.sanitize_metadata(episode_meta_raw)

            questions = episode["questions"]
            qa_pairs = episode["question_answers"]
            print(f"In episode {episode['id']}, there are {len(qa_pairs)} qa pairs.")
            for i, qa in enumerate(qa_pairs):
                q = qa.get("question", "")
                a = qa.get("answer", "")

                q_item = questions[i]
                # print("q_item: ", q_item)
                start = q_item.get("start")
                end   = q_item.get("end")

                qa_id = str(uuid.uuid4())
                doc = json.dumps({"question": q, "answer": a})

                metadata = dict(episode_meta)
                metadata["question"] = q
                metadata["answer"] = a
                metadata["start"] = float(start) if start is not None else None
                metadata["end"] = float(end) if end is not None else None
                metadata = self.sanitize_metadata(metadata)

                batch_ids.append(qa_id)
                batch_docs.append(doc)
                batch_metas.append(metadata)

                # 🚀 When batch is full → embed once → upsert once
                if len(batch_ids) >= BATCH_SIZE:
                    embeddings = await self.embed_batch(batch_docs)
                    self.qa_collection.upsert(
                        ids=batch_ids,
                        embeddings=embeddings,
                        documents=batch_docs,
                        metadatas=batch_metas
                    )
                    batch_ids, batch_docs, batch_metas = [], [], []

        # --- Flush last batch ---
        if batch_ids:
            embeddings = await self.embed_batch(batch_docs)
            self.qa_collection.upsert(
                ids=batch_ids,
                embeddings=embeddings,
                documents=batch_docs,
                metadatas=batch_metas
            )

        print("🎉 Finished indexing all QA pairs!")
        print("Total items in collection:", self.qa_collection.count())

    async def upsert_utterances_collection(self):
        print("Starting Utterances indexing...")

        self.utterances = self.chroma_client.get_collection(
                name=self.utterances_collection_name)

        all_episodes = await self.load_all_episode_utterances()
        print("Loaded", len(all_episodes), "episodes")
        episodes = self.filtered_episodes_to_index(all_episodes, self.utterances_collection)
        print("Episodes remaining to index: ", len(episodes))
        total_utterances = sum(len(ep["utterances"]) for ep in episodes)
        print(f"Total utterances to index: {total_utterances}")
        # for every episode, filter out utterances that are less than 10 words
        for ep in episodes:
            ep["utterances"] = [u for u in ep["utterances"] if len(u["text"].split()) >= 10]
        filtered_total_utterances = sum(len(ep["utterances"]) for ep in episodes)
        print(f"Total utterances to index after filtering short ones: {filtered_total_utterances}")
        BATCH_SIZE = 100   # sweet spot for Ollama performance

        batch_ids = []
        batch_docs = []
        batch_metas = []

        for episode in tqdm(episodes, desc="Processing episodes"):
            episode_meta_raw = {
                k: v for k, v in episode.items()
                if k not in ("utterances")
            }
            episode_meta = self.sanitize_metadata(episode_meta_raw)

            utterances = episode["utterances"]
            # qa_pairs = episode["question_answers"]
            print(f"In episode {episode['id']}, there are {len(utterances)} utterances.")
            for i, u in enumerate(utterances):
                # q = u.get("question", "")
                # a = u.get("answer", "")

                # q_item = questions[i]
                # print("q_item: ", q_item)
                start = u.get("start")
                end   = u.get("end")
                speaker = u.get("speaker")

                u_id = str(uuid.uuid4())
                doc = u.get("text", "")

                metadata = dict(episode_meta)
                metadata["speaker"] = speaker
                metadata["start"] = float(start) if start is not None else None
                metadata["end"] = float(end) if end is not None else None
                metadata = self.sanitize_metadata(metadata)

                batch_ids.append(u_id)
                batch_docs.append(doc)
                batch_metas.append(metadata)

                # 🚀 When batch is full → embed once → upsert once
                if len(batch_ids) >= BATCH_SIZE:
                    # for doc in batch_docs:
                    #     print(doc[:100])
                    #     print('\n')
                    embeddings = await self.embed_batch(batch_docs)
                    self.utterances.upsert(
                        ids=batch_ids,
                        embeddings=embeddings,
                        documents=batch_docs,
                        metadatas=batch_metas
                    )
                    batch_ids, batch_docs, batch_metas = [], [], []

        # --- Flush last batch ---
        if batch_ids:
            embeddings = await self.embed_batch(batch_docs)
            self.utterances_collection.upsert(
                ids=batch_ids,
                embeddings=embeddings,
                documents=batch_docs,
                metadatas=batch_metas
            )

        print("🎉 Finished indexing all QA pairs!")
        print("Total items in collection:", self.utterances_collection.count())
        
        
    def delete_collection(self, collection_name):
        try:
            self.chroma_client.delete_collection(collection_name)
            print(f"Deleted collection: {collection_name}")
        except Exception as e:
            print(f"Error: {e}")
    
    async def update_metadata(self):
        episodes = await self.load_all_question_episodes()
        collection = self.get_collection(self.qa_collection_name) 
        res = collection.get(include=["metadatas"])
        ids = res["ids"]
        old_metas = res["metadatas"]
        print(len(ids))
        new_metas = []
        for m in old_metas:
            m = dict(m)
            m["podcast_title"] = next((ep["podcast_title"] for ep in episodes if ep["id"] == m["id"]))
            m["episode_description"] = next((ep["description"] for ep in episodes if ep["id"] == m["id"]))
            new_metas.append(m)

        collection.update(
            ids=ids,
            metadatas=new_metas
        )
                    