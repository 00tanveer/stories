import asyncio
import hashlib
import json
import requests
import time
from dotenv import load_dotenv
import os
import json
import functools
from datetime import datetime

# typing
from typing import Dict, List

# Async DB session 
from app.db.session import AsyncSessionLocal
from app.db.data_models.podcast import Podcast
from app.db.data_models.episode import Episode
from app.db.data_models.transcript import Transcript
from app.db.data_models.transcript_chapter import TranscriptChapter
from app.db.data_models.transcript_utterance import TranscriptUtterance
from app.db.data_models.transcript_word import TranscriptWord

# sqlalchemy 
from sqlalchemy import select, func, and_, text
from sqlalchemy.orm import selectinload


def get_version():
    with open("version.json") as f:
        return json.load(f)['version']

VERSION = get_version()

    
def __map_feed_to_podcast(feed_data: Dict) -> Podcast:
    """Map PodcastIndex feed data to Podcast ORM model."""
    podcast = Podcast(
        id=str(feed_data.get('id')),
        title=feed_data.get('title', ''),
        url=feed_data.get('url', ''),
        original_url=feed_data.get('originalUrl', ''),
        description=feed_data.get('description', ''),
        cover_image=feed_data.get('image', ''),
        author=feed_data.get('author', ''),
        website=feed_data.get('originalUrl', ''),
        language=feed_data.get('language', ''),
        episode_count=feed_data.get('episodeCount', 0)
    )
    return podcast

def __map_item_to_episode(item: Dict) -> Episode:
    """
    Map an episode item into Episode ORM. Placeholder mapping — adapt fields if needed.
    """
    # datePublished sometimes is unix timestamp or ISO
    pub_raw = item.get("datePublished")
    date_published = None
    pub_raw = item.get("datePublished")
    date_published = (
        datetime.fromtimestamp(pub_raw)
        if pub_raw is not None
        else None
    )

    return Episode(
        id=str(item.get("id")),
        podcast_id=str(item.get("feedId")),
        title=item.get("title") or "",
        podcast_url=item.get("link") or item.get("url") or "",
        podcast_image=item.get("feedImage") or None,
        episode_image=item.get("image") or None,
        enclosure_url=item.get("enclosureUrl") or (item.get("enclosure", {}).get("url") if isinstance(item.get("enclosure"), dict) else None),
        duration=int(item.get("duration") or 0),
        date_published=date_published,
    )
def __map_item_to_transcript(item: Dict) -> Transcript:
    """
    Map a transcript item into Transcript ORM. Placeholder mapping — adapt fields if needed.
    """
    return Transcript(
        id=str(item.get("id")),
        episode_id=str(item.get("episodeId")),
        status=item.get("status"),
        audio_url=item.get("audio_url"),
        text=item.get("text"), 
    )

def __map_item_to_transcript_chapter(item: Dict) -> TranscriptChapter:
    """
    Map a transcript chapter into TranscriptChapter ORM
    """
    return TranscriptChapter(
        transcript_id=item.get("transcriptId"),
        summary=item.get("summary"),
        headline=item.get("headline"),
        gist=item.get("gist") or "",
        start=item.get('start'),
        end=item.get("end")
    )

def __map_item_to_transcript_utterance(item: Dict) -> TranscriptChapter:
    """
    Map a transcript utterance into TranscriptUtterance ORM
    """
    return TranscriptUtterance(
        transcript_id=item.get("transcriptId"),
        start=item.get("start"),
        end=item.get("end"),
        confidence=float(item.get("confidence")),
        speaker=item.get("speaker"),
        text=item.get("text"),
    )

def __map_item_to_transcript_word(item: Dict) -> TranscriptWord:
    """
    Map a transcript word into TranscriptWord ORM
    """
    return TranscriptWord(
        transcript_id=item.get("transcriptId"),
        start=item.get("start"),
        end=item.get("end"),
        confidence=float(item.get("confidence")),
        speaker=item.get("speaker"),
        text=item.get("text"),
    )
async def save_podcast(feed: Dict):
    """
    Upsert a Podcast row using AsyncSession.merge() — idempotent.
    """
    # Ensure DB tables exist (call init_db() earlier in app startup normally)
    async with AsyncSessionLocal() as session:  # type: AsyncSession
        async with session.begin():
            podcast_obj = __map_feed_to_podcast(feed)
            # session.merge returns a persistent instance; await it because AsyncSession.merge is async
            await session.merge(podcast_obj)
        # commit happens on context exit because begin() used
    return True


async def save_episodes(items: List[Dict]):
    """
    Upsert multiple Episode rows.
    - Tries to use feed_url to find podcast_id (if you prefer), otherwise maps episode's feedId/guid.
    - Uses merge() for idempotent behavior.
    """
    semaphore = asyncio.Semaphore(100) # max 10 concurrent inserts
    async def save_one_episode(item):
        async with semaphore:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    episode_obj = __map_item_to_episode(item)
                    await session.merge(episode_obj)
            return True
    await asyncio.gather(*(save_one_episode(item) for item in items))
    return True

semaphore = asyncio.Semaphore(5)
async def save_one_transcript(t_dict: Dict, episodes: list, audio_urls: list):
    """Save a single transcript and its child objects."""
    async with semaphore:
        try:
            # Match transcript → episode
            if t_dict['audio_url'] in audio_urls:
                idx = audio_urls.index(t_dict['audio_url'])
                t_dict['episodeId'] = episodes[idx]['id']
            else:
                print(f"⚠️ No matching episode for {t_dict['audio_url']}")
                return False

            # Map ORM objects
            transcript_obj = __map_item_to_transcript(t_dict)

            t_ch_obj_list = [
                __map_item_to_transcript_chapter({**ch, "transcriptId": t_dict["id"]})
                for ch in t_dict.get("chapters", [])
            ]
            t_utt_obj_list = [
                __map_item_to_transcript_utterance({**utt, "transcriptId": t_dict["id"]})
                for utt in t_dict.get("utterances", [])
            ]
            t_word_obj_list = [
                __map_item_to_transcript_word({**w, "transcriptId": t_dict["id"]})
                for w in t_dict.get("words", [])
            ]

            async with AsyncSessionLocal() as session:
                async with session.begin():
                    merged = await session.merge(transcript_obj)
                    session.add_all(t_ch_obj_list)
                    session.add_all(t_utt_obj_list)
                    session.add_all(t_word_obj_list)

                await session.commit()
                print(f"✅ Saved transcript {merged.id} with {len(t_word_obj_list)} words.")
                return True

        except Exception as e:
            print(f"❌ Failed transcript {t_dict.get('id')} — {e}")
            return False
async def save_transcripts(files: List[Dict]):
    """
        Upsert multiple transcript records
        and their child records: words, utterances and
        chapters
    """
    episodes = json.load(open('data/podcasts/pod_episodes_metadata.json', 'r'))
    audio_urls = [e['enclosureUrl'] for e in episodes]

    # create tasks
    tasks = [
        save_one_transcript(t, episodes, audio_urls)
        for t in files
    ]

    # run them concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success = sum(1 for r in results if r is True)
    fail = sum(1 for r in results if r is False or isinstance(r, Exception))

    print(f"\nSummary: ✅ {success} saved, ❌ {fail} failed\n")
    return True

async def read_podcast_metadata(id: str):
    '''
        Read podcast metadata including episode information 
        - podcast title
        - no. of episodes (from podcast table, don't calculate)
        - no. of hours of audio (sql query)
        - author
        - category
        - avg episode duration
        - website
        - avg transcript length
        - avg no. of chapters per episode
        - average number of utterances per episode
        ---- NLP ----
        - most common topics
        - named entities
        -
    '''
    pass
async def get_word_count(session, episode_id: str):
    stmt = (
        select(func.count(TranscriptWord.id))
        .join(Transcript, TranscriptWord.transcript_id == Transcript.id)
        .where(Transcript.episode_id == episode_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() or 0

async def get_utterance_count(session, episode_id: str):
    stmt = (
        select(func.count(TranscriptUtterance.id))
        .join(Transcript, TranscriptUtterance.transcript_id == Transcript.id)
        .where(Transcript.episode_id == episode_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() or 0
async def get_avg_utterance_duration(session, episode_id: str):
    stmt = (
        select(func.avg(TranscriptUtterance.end - TranscriptUtterance.start))
        .join(Transcript, TranscriptUtterance.transcript_id == Transcript.id)
        .where(Transcript.episode_id == episode_id)
    )
    result = await session.execute(stmt)
    return round(result.scalar_one_or_none() or 0, 2)
async def get_chapter_count(session, episode_id: str):
    stmt = (
        select(func.count(TranscriptChapter.id))
        .join(Transcript, TranscriptChapter.transcript_id == Transcript.id)
        .where(Transcript.episode_id == episode_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() or 0
async def read_episode_data() -> Dict:
    '''
        Read episode information including guest information
        - episode title
        - guest 
        - audio_duration
        - total utterances (sql query)
        - avg utterance duration (sql query)
        - questions
        - question answer pair
    '''
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = select(
                    Episode,
                    Podcast.author
                ).join(
                    Episode.podcast
                ).where(
                    and_(
                    Episode.host_questions != [],
                    Episode.question_answers != []
                )).limit(5)
            results = await session.execute(stmt)
            return results.all()

async def load_all_question_episodes():
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
async def load_all_episode_utterances():
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
                utterances = []
                for row in rows:
                    episode, author, podcast_title = row
                    if episode.transcript and episode.transcript.utterances:
                        for u in episode.transcript.utterances:
                            utterances.append({
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
                                "start": u.start,
                                "end": u.end,
                                "confidence": u.confidence,
                                "speaker": u.speaker,
                                "text": u.text,
                            })  
        print(len(utterances))
        # for u in utterances[:4]:
        #     print(u)
        #     print("-----\n")
        return utterances
async def update_confidence_from_json():
    """
    Update only confidence fields for transcript_utterance and transcript_word.
    Assumes t_dict contains the original data with float confidence values.
    """
    transcript_file_paths = os.listdir("data/transcripts/")
    transcripts = []
    for path in transcript_file_paths:
        with open(f"data/transcripts/{path}", 'r') as f:
            transcript = json.load(f)
            transcripts.append(transcript)
    async with AsyncSessionLocal() as session:
        for t in transcripts:
            tid = t.get("id")
            if not tid:
                print("⚠️ Transcript missing id in JSON")
                continue

            # ----- WORDS -----
            for w in t.get("words", []):
                await session.execute(
                    text("""
                        UPDATE transcript_words
                        SET confidence = :confidence
                        WHERE transcript_id = :transcript_id
                        AND start = :start
                        AND "end" = :end
                        AND text = :text
                        AND speaker = :speaker
                    """),
                    {
                        "transcript_id": tid,
                        "start": w["start"],
                        "end": w["end"],
                        "text": w["text"],
                        "speaker": w["speaker"],
                        "confidence": float(w.get("confidence", 0.0)),
                    }
                )

            # ----- UTTERANCES -----
            for u in t.get("utterances", []):
                await session.execute(
                    text("""
                        UPDATE transcript_utterance
                        SET confidence = :confidence
                        WHERE transcript_id = :transcript_id
                        AND start = :start
                        AND "end" = :end
                        AND text = :text
                        AND speaker = :speaker
                    """),
                    {
                        "transcript_id": tid,
                        "start": u["start"],
                        "end": u["end"],
                        "text": u["text"],
                        "speaker": u["speaker"],
                        "confidence": float(u.get("confidence", 0.0)),
                    }
                )

            print(f"Updated transcript {tid}")

        await session.commit()
        print("🎉 All confidence values restored successfully!")

            