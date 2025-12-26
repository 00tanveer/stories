"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import appStyles from "../../../App.module.css";
import styles from "./genre.module.css";
import { Button } from "@/components/ui/button";

// Define available genres
const GENRES = [
  'technology',
  'business',
  'science',
  'health',
  'education',
  'entertainment',
  'sports',
  'news'
];

interface Podcast {
  id: string;
  title: string;
  itunesAuthor?: string;
  description: string;
  episodeCount: number;
  rating?: number;
  numberOfRatings?: number;
  imageUrl?: string;
  collectionViewUrl?: string;
  newestEnclosureDuration?: number;
}

type SortOption = 'rating' | 'episodeCount' | 'newestEnclosureDuration';
type SortDirection = 'asc' | 'desc';

export default function GenrePage() {
  const params = useParams();
  const genre = params.genre as string;
  const [podcasts, setPodcasts] = useState<Podcast[]>([]);
  const [filteredPodcasts, setFilteredPodcasts] = useState<Podcast[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Filter states
  const [minRating, setMinRating] = useState<number>(0);
  const [minEpisodes, setMinEpisodes] = useState<number>(0);
  const [maxDuration, setMaxDuration] = useState<number>(120);
  const [sortBy, setSortBy] = useState<SortOption>('rating');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [searchQuery, setSearchQuery] = useState('');

  // Reset page to 1 when genre changes
  useEffect(() => {
    setPage(1);
  }, [genre]);

  useEffect(() => {
    // Validate genre
    if (!GENRES.includes(genre.toLowerCase())) {
      // Handle invalid genre
      setLoading(false);
      return;
    }

    // Fetch podcasts from API
    const fetchPodcasts = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/pods/${genre}?page=${page}&page_size=50`
        );
        if (!response.ok) {
          throw new Error('Failed to fetch podcasts');
        }
        const data = await response.json();
        setPodcasts(data.podcasts);
        setFilteredPodcasts(data.podcasts);
        setTotalPages(data.total_pages);
        // Scroll to top when page changes
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } catch (error) {
        console.error('Error fetching podcasts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPodcasts();
  }, [genre, page]);

  useEffect(() => {
    // Apply filters
    let filtered = [...podcasts];

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(p => 
        p.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.itunesAuthor?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.description?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Rating filter
    filtered = filtered.filter(p => (p.rating ?? 0) >= minRating);

    // Episode count filter
    filtered = filtered.filter(p => p.episodeCount >= minEpisodes);

    // Duration filter (convert seconds to minutes)
    filtered = filtered.filter(p => {
      const durationMinutes = (p.newestEnclosureDuration ?? 0) / 60;
      return durationMinutes <= maxDuration;
    });

    // Sort
    filtered.sort((a, b) => {
      const aVal = (a[sortBy] as number) ?? 0;
      const bVal = (b[sortBy] as number) ?? 0;
      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    });

    setFilteredPodcasts(filtered);
  }, [podcasts, minRating, minEpisodes, maxDuration, sortBy, sortDirection, searchQuery]);

  const resetFilters = () => {
    setMinRating(0);
    setMinEpisodes(0);
    setMaxDuration(120);
    setSortBy('rating');
    setSortDirection('desc');
    setSearchQuery('');
  };

  if (loading) {
    return (
      <div className={appStyles.appRoot}>
        <Navbar />
        <div className={appStyles.container}>
          <p className={appStyles.loading}>Loading...</p>
        </div>
      </div>
    );
  }

  if (!GENRES.includes(genre.toLowerCase())) {
    return (
      <div className={appStyles.appRoot}>
        <Navbar />
        <div className={appStyles.container}>
          <div className={styles.errorMessage}>
            <h2>Genre not found</h2>
            <p>The genre "{genre}" is not available. Please choose from:</p>
            <div className={styles.genreList}>
              {GENRES.map(g => (
                <a key={g} href={`/pods/${g}`} className={styles.genreLink}>
                  {g.charAt(0).toUpperCase() + g.slice(1)}
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={appStyles.appRoot}>
      <Navbar />
      <div className={appStyles.container}>
        {/* Header */}
        <div className={styles.pageHeader}>
          <h1 className={styles.pageTitle}>
            {genre.charAt(0).toUpperCase() + genre.slice(1)} Podcasts
          </h1>
          <p className={styles.pageSubtitle}>
            Discover the best {genre} podcasts with insights from industry experts
          </p>
        </div>

        {/* Search Bar */}
        <div className={styles.searchSection}>
          <input
            type="text"
            placeholder="Search podcasts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={styles.searchInput}
          />
        </div>

        

        {/* Results Count */}
        <div className={styles.resultsInfo}>
          <p>Showing {filteredPodcasts.length} of {podcasts.length} podcasts (Page {page} of {totalPages})</p>
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className={styles.paginationContainer}>
            <Button 
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className={styles.paginationButton}
            >
              ← Previous
            </Button>
            <span className={styles.paginationInfo}>
              Page {page} of {totalPages}
            </span>
            <Button 
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className={styles.paginationButton}
            >
              Next →
            </Button>
          </div>
        )}

        {/* Podcasts Grid */}
        <div className={styles.podcastsGrid}>
          {filteredPodcasts.length === 0 ? (
            <div className={styles.noResults}>
              <p>No podcasts match your filters. Try adjusting them!</p>
            </div>
          ) : (
            filteredPodcasts.map((podcast) => (
              <Link 
                key={podcast.id} 
                href={`/pods/${genre}/${podcast.id}`}
                className={styles.podcastCard}
              >
                <div className={styles.podcastImage}>
                  {podcast.imageUrl ? (
                    <img src={podcast.imageUrl} alt={podcast.title} />
                  ) : (
                    <div className={styles.podcastImagePlaceholder}>🎙️</div>
                  )}
                </div>
                <div className={styles.podcastContent}>
                  <h3 className={styles.podcastTitle}>{podcast.title}</h3>
                  <p className={styles.podcastAuthor}>by {podcast.itunesAuthor || 'Unknown'}</p>
                  <p className={styles.podcastDescription}>{podcast.description || 'No description available'}</p>
                  
                  <div className={styles.podcastMetrics}>
                    <div className={styles.metric}>
                      <span className={styles.metricLabel}>Rating</span>
                      <span className={styles.metricValue}>
                        {podcast.rating ? `${podcast.rating.toFixed(1)} ⭐` : 'N/A'}
                      </span>
                    </div>
                    <div className={styles.metric}>
                      <span className={styles.metricLabel}>Episodes</span>
                      <span className={styles.metricValue}>{podcast.episodeCount}</span>
                    </div>
                    <div className={styles.metric}>
                      <span className={styles.metricLabel}>Reviews</span>
                      <span className={styles.metricValue}>
                        {podcast.numberOfRatings || 0}
                      </span>
                    </div>
                  </div>

                  <Button className={styles.viewButton}>
                    View Episodes
                  </Button>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
