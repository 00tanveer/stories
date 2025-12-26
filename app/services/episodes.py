"""Service for episode-related database operations."""

from typing import List, Dict, Optional
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.data_models.episode import Episode


async def get_episodes_by_podcast_id(podcast_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
    """
    Fetch episodes for a given podcast ID.
    
    Args:
        podcast_id: The podcast feed ID
        limit: Maximum number of episodes to return (default: 50)
        offset: Number of episodes to skip for pagination (default: 0)
    
    Returns:
        List of episode dictionaries with all episode data
    """
    async with AsyncSessionLocal() as session:
        query = (
            select(Episode)
            .where(Episode.podcast_id == str(podcast_id))
            .order_by(Episode.date_published.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(query)
        episodes = result.scalars().all()
        
        return [
            {
                "id": episode.id,
                "podcast_id": episode.podcast_id,
                "title": episode.title,
                "description": episode.description,
                "podcast_url": episode.podcast_url,
                "podcast_image": episode.podcast_image,
                "episode_image": episode.episode_image,
                "enclosure_url": episode.enclosure_url,
                "duration": episode.duration,
                "date_published": episode.date_published.isoformat() if episode.date_published else None,
                "host_questions": episode.host_questions,
                "question_answers": episode.question_answers,
            }
            for episode in episodes
        ]


async def get_episode_by_id(episode_id: str) -> Optional[Dict]:
    """
    Fetch a single episode by its ID.
    
    Args:
        episode_id: The episode ID
    
    Returns:
        Episode dictionary or None if not found
    """
    async with AsyncSessionLocal() as session:
        query = select(Episode).where(Episode.id == str(episode_id))
        result = await session.execute(query)
        episode = result.scalar_one_or_none()
        
        if not episode:
            return None
        
        return {
            "id": episode.id,
            "podcast_id": episode.podcast_id,
            "title": episode.title,
            "description": episode.description,
            "podcast_url": episode.podcast_url,
            "podcast_image": episode.podcast_image,
            "episode_image": episode.episode_image,
            "enclosure_url": episode.enclosure_url,
            "duration": episode.duration,
            "date_published": episode.date_published.isoformat() if episode.date_published else None,
            "host_questions": episode.host_questions,
            "question_answers": episode.question_answers,
        }
