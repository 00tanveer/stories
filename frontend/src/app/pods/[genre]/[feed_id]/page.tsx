"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import PodcastPlayer from "@/components/PodcastPlayer";
import type { QAResult } from "@/components/types";
import appStyles from "../../../../App.module.css";
import styles from "./podcast.module.css";
import { Button } from "@/components/ui/button";
import Link from "next/link";

interface Podcast {
  feedId: string;
  title: string;
  itunesAuthor?: string;
  description: string;
  episodeCount: number;
  rating?: number;
  numberOfRatings?: number;
  imageUrl?: string;
  collectionViewUrl?: string;
  newestEnclosureDuration?: number;
  newestItemPubdate?: number;
  oldestItemPubdate?: number;
  language?: string;
  explicit?: number;
  updateFrequency?: number;
  popularityScore?: number;
  category1?: string;
  category2?: string;
  category3?: string;
}

interface Episode {
  id: string;
  podcast_id: string;
  title: string;
  description?: string;
  podcast_url: string;
  podcast_image: string;
  episode_image?: string;
  enclosure_url: string;
  duration: number;
  date_published: string;
  host_questions?: any[];
  question_answers?: any[];
}

export default function PodcastDetailPage() {
  const params = useParams();
  const router = useRouter();
  const genre = params.genre as string;
  const feedId = params.feed_id as string;
  const [podcast, setPodcast] = useState<Podcast | null>(null);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingEpisodes, setLoadingEpisodes] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // PodcastPlayer states
  type SeekTime = { time: number; token: number };
  const [currentEpisode, setCurrentEpisode] = useState<QAResult | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [seekTime, setSeekTime] = useState<SeekTime | null>(null);
  const [isLoadingPlayer, setIsLoadingPlayer] = useState(false);

  useEffect(() => {
    const fetchPodcast = async () => {
      try {
        console.log('Fetching podcast for genre:', genre, 'and feedId:', feedId);
        setLoading(true);
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/pods/${genre}/${feedId}`
        );
        if (!response.ok) {
          throw new Error('Podcast not found');
        }
        const data = await response.json();
        setPodcast(data);
      } catch (error) {
        console.error('Error fetching podcast:', error);
        setError('Failed to load podcast');
      } finally {
        setLoading(false);
      }
    };

    fetchPodcast();
  }, [genre, feedId]);

  useEffect(() => {
    const fetchEpisodes = async () => {
      try {
        console.log('Fetching episodes for feedId:', feedId);
        setLoadingEpisodes(true);
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/episodes/${feedId}`
        );
        if (!response.ok) {
          throw new Error('Episodes not found');
        }
        const data = await response.json();
        setEpisodes(data.episodes || []);
      } catch (error) {
        console.error('Error fetching episodes:', error);
      } finally {
        setLoadingEpisodes(false);
      }
    };

    if (feedId) {
      fetchEpisodes();
    }
  }, [feedId]);

  const handlePlayClick = (episode: Episode) => {
    // Convert Episode to QAResult format for PodcastPlayer
    const qaResult: QAResult = {
      id: episode.id,
      title: episode.title,
      podcast_title: podcast?.title || '',
      episode_description: episode.description || '',
      author: podcast?.itunesAuthor || '',
      date_published: episode.date_published,
      duration: episode.duration,
      enclosure_url: episode.enclosure_url,
      start: 0, // Start from beginning
      episode_image: episode.episode_image,
      podcast_url: episode.podcast_url,
    };
    
    setCurrentEpisode(qaResult);
    setSeekTime({ time: 0, token: Date.now() });
    setIsLoadingPlayer(true);
    setIsPlaying(true);
  };

  if (loading) {
    return (
      <div className={appStyles.appRoot}>
        <Navbar />
        <div className={appStyles.container}>
          <p className={appStyles.loading}>Loading podcast...</p>
        </div>
      </div>
    );
  }

  if (error || !podcast) {
    return (
      <div className={appStyles.appRoot}>
        <Navbar />
        <div className={appStyles.container}>
          <div className={styles.errorMessage}>
            <h2>Podcast not found</h2>
            <p>{error || 'The podcast you are looking for does not exist.'}</p>
            <Button onClick={() => router.push(`/pods/${genre}`)}>
              Back to {genre} podcasts
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const formatDate = (timestamp?: number) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp * 1000).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const minutes = Math.floor(seconds / 60);
    return `${minutes} min`;
  };

  const categories = [
    podcast.category1,
    podcast.category2,
    podcast.category3
  ].filter(Boolean);

  return (
    <div className={appStyles.appRoot}>
      <Navbar />
      <div className={appStyles.container}>
        {/* Breadcrumb */}
        <div className={styles.breadcrumb}>
          <Link href="/">Home</Link>
          <span className={styles.separator}>›</span>
          <Link href={`/pods/${genre}`}>{genre}</Link>
          <span className={styles.separator}>›</span>
          <span>{podcast.title}</span>
        </div>

        {/* Podcast Header */}
        <div className={styles.podcastHeader}>
          <div className={styles.podcastImageLarge}>
            {podcast.imageUrl ? (
              <img src={podcast.imageUrl} alt={podcast.title} />
            ) : (
              <div className={styles.podcastImagePlaceholder}>🎙️</div>
            )}
          </div>

          <div className={styles.podcastInfo}>
            <h1 className={styles.podcastTitle}>{podcast.title}</h1>
            <p className={styles.podcastAuthor}>by {podcast.itunesAuthor || 'Unknown'}</p>

            {/* Rating */}
            {podcast.rating && podcast.rating > 0 ? (
              <div className={styles.ratingSection}>
                <div className={styles.ratingStars}>
                  {[...Array(5)].map((_, i) => (
                    <span key={i} className={i < Math.round(podcast.rating!) ? styles.starFilled : styles.starEmpty}>
                      ⭐
                    </span>
                  ))}
                </div>
                <span className={styles.ratingText}>
                  {podcast.rating.toFixed(1)} ({podcast.numberOfRatings?.toLocaleString() || 0} reviews)
                </span>
              </div>
            ) : (
              <p className={styles.noRating}>No ratings yet</p>
            )}

            {/* Categories */}
            {categories.length > 0 && (
              <div className={styles.categories}>
                {categories.map((cat, idx) => (
                  <span key={idx} className={styles.categoryTag}>
                    {cat}
                  </span>
                ))}
              </div>
            )}

            {/* Action Buttons */}
            <div className={styles.actionButtons}>
              {podcast.collectionViewUrl && (
                <Button 
                  onClick={() => window.open(podcast.collectionViewUrl, '_blank')}
                  className={styles.primaryButton}
                >
                  View on Apple Podcasts
                </Button>
              )}
              <Button 
                onClick={() => router.push(`/search?q=${encodeURIComponent(podcast.title)}`)}
                className={styles.secondaryButton}
              >
                Search Episodes
              </Button>
            </div>
          </div>
        </div>

        {/* Description */}
        <div className={styles.descriptionSection}>
          <h2>About this podcast</h2>
          <p className={styles.description}>
            {podcast.description || 'No description available'}
          </p>
        </div>

        {/* Stats Grid */}
        <div className={styles.statsGrid}>
          <div className={styles.statCard}>
            <span className={styles.statIcon}>📊</span>
            <div className={styles.statContent}>
              <span className={styles.statLabel}>Episodes</span>
              <span className={styles.statValue}>{podcast.episodeCount}</span>
            </div>
          </div>

          <div className={styles.statCard}>
            <span className={styles.statIcon}>🕐</span>
            <div className={styles.statContent}>
              <span className={styles.statLabel}>Latest Episode Duration</span>
              <span className={styles.statValue}>{formatDuration(podcast.newestEnclosureDuration)}</span>
            </div>
          </div>

          <div className={styles.statCard}>
            <span className={styles.statIcon}>📅</span>
            <div className={styles.statContent}>
              <span className={styles.statLabel}>Latest Episode</span>
              <span className={styles.statValue}>{formatDate(podcast.newestItemPubdate)}</span>
            </div>
          </div>

          <div className={styles.statCard}>
            <span className={styles.statIcon}>🔥</span>
            <div className={styles.statContent}>
              <span className={styles.statLabel}>Popularity Score</span>
              <span className={styles.statValue}>{podcast.popularityScore || 'N/A'}</span>
            </div>
          </div>

          <div className={styles.statCard}>
            <span className={styles.statIcon}>📆</span>
            <div className={styles.statContent}>
              <span className={styles.statLabel}>Update Frequency</span>
              <span className={styles.statValue}>
                {podcast.updateFrequency ? `Every ${podcast.updateFrequency} days` : 'N/A'}
              </span>
            </div>
          </div>

          <div className={styles.statCard}>
            <span className={styles.statIcon}>🌍</span>
            <div className={styles.statContent}>
              <span className={styles.statLabel}>Language</span>
              <span className={styles.statValue}>{podcast.language?.toUpperCase() || 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* Recent Episodes Section */}
        <div className={styles.episodesSection}>
          <h2>Recent Episodes ({episodes.length})</h2>
          
          {loadingEpisodes ? (
            <p className={styles.loadingText}>Loading episodes...</p>
          ) : episodes.length === 0 ? (
            <p className={styles.noEpisodes}>No episodes found for this podcast.</p>
          ) : (
            <div className={styles.episodesList}>
              {episodes.map((episode) => (
                <div key={episode.id} className={styles.episodeCard}>
                  <div className={styles.episodeImage}>
                    {episode.episode_image || episode.podcast_image ? (
                      <img 
                        src={episode.episode_image || episode.podcast_image} 
                        alt={episode.title} 
                      />
                    ) : (
                      <div className={styles.episodeImagePlaceholder}>🎙️</div>
                    )}
                  </div>
                  
                  <div className={styles.episodeContent}>
                    <h3 className={styles.episodeTitle}>{episode.title}</h3>
                    
                    <div className={styles.episodeMeta}>
                      <span className={styles.episodeDate}>
                        {new Date(episode.date_published).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric'
                        })}
                      </span>
                      <span className={styles.episodeDuration}>
                        {formatDuration(episode.duration)}
                      </span>
                    </div>
                    
                    {episode.description && (
                      <p className={styles.episodeDescription}>
                        {episode.description.length > 200 
                          ? `${episode.description.substring(0, 200)}...` 
                          : episode.description}
                      </p>
                    )}
                    
                    <div className={styles.episodeActions}>
                      <Button
                        onClick={() => handlePlayClick(episode)}
                        className={styles.playButton}
                        disabled={!episode.enclosure_url}
                      >
                        {currentEpisode?.id === episode.id && isPlaying ? '⏸️ Pause' : '▶️ Play'}
                      </Button>
                      {episode.podcast_url && (
                        <Button
                          onClick={() => window.open(episode.podcast_url, '_blank')}
                          className={styles.linkButton}
                          variant="outline"
                        >
                          View Details
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <PodcastPlayer
          episode={currentEpisode}
          seekTime={seekTime}
          isPlaying={isPlaying}
          isLoading={isLoadingPlayer}
          setIsLoading={setIsLoadingPlayer}
          onPlayStateChange={setIsPlaying}
          onSeekChange={(ms: number) => setSeekTime({ time: ms, token: Date.now() })}
          onEnded={() => setIsPlaying(false)}
        />
      </div>
    </div>
  );
}
