"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import SearchBar from "@/components/SearchBar";
import ResultsList from "@/components/ResultsList";
import PodcastPlayer from "@/components/PodcastPlayer";
import type { QAResult } from "@/components/types";
import { usePostHog } from '@posthog/react';
import styles from "../App.module.css";
import { Button } from "@/components/ui/button";

function HomeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const posthog = usePostHog();
  const [results, setResults] = useState<QAResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState(searchParams.get('q') || "");
  const [lastSearchedQuery, setLastSearchedQuery] = useState("");
  // Podcastplayer state to pass as props
  const [sessionId, setSessionId] = useState<string | null>(null);
  type SeekTime = { time: number; token: number };
  const [currentEpisode, setCurrentEpisode] = useState<QAResult | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [seekTime, setSeekTime] = useState<SeekTime | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const suggestions = [
    "How to be the top 1% software engineer?",
    "Zuckerberg stories",
    "What career advice would you give?",
    "Career horror stories"
  ];

  useEffect(() => {
    if (posthog) {
      const id = posthog.get_session_id();
      setSessionId(id);
    }
  }, [posthog]);

  // Auto-search on load if q in URL
  useEffect(() => {
    const q = searchParams.get('q');
    if (q && q !== lastSearchedQuery) {
      setQuery(q);
      handleSearch(q);
    }
  }, [searchParams]);

  const handleSearch = async (searchQuery: string) => {
    posthog?.capture('clicked_search');
    setLastSearchedQuery(searchQuery);
    setLoading(true);
    // Update URL
    const params = new URLSearchParams(searchParams.toString());
    params.set('q', searchQuery);
    router.push(`/?${params.toString()}`);
    try {
      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (sessionId) {
        headers['X-POSTHOG-SESSION-ID'] = sessionId;
      }
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/search`, {
        method: "POST",
        headers,
        body: JSON.stringify({ query: searchQuery }),
      });
      const data = await res.json();
      const serverResults: QAResult[] = Array.isArray(data)
        ? data
        : (data.results ?? []);
      setResults(serverResults);
    } catch (err) {
      console.error("Search error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayClick = (episode: QAResult) => {
    setCurrentEpisode(episode);
    setSeekTime({ time: episode.start ?? 0, token: Date.now() });
    setIsLoading(true);
    setIsPlaying(true);
  };

  return (
    <div className={styles.appRoot}>
      <Navbar />
      <div className={styles.container}>
        <div className={styles.header}>
          <p className={styles.subtitle}>
            Search for insightful stories, across thousands of conversations ✨
          </p>
          <p className={styles.note}>Just ask a question!</p>
        </div>
        <SearchBar
          query={query}
          onQueryChange={setQuery}
          onSearch={handleSearch}
        />
        <div className={styles.suggestions}>
          <p>Suggestions:</p>
          {
            suggestions.map(s => (
              <Button key={s} className={styles.suggestionBtn} onClick={() => { setQuery(s); handleSearch(s); }}>{s}</Button>
            ))
          }
        </div>
        {loading ? (
          <p className={styles.loading}>Searching...</p>
        ) : (
          results.length > 0 ? (
            <>
              <p>
                Retrieved {results.length} results for <strong>{lastSearchedQuery}</strong>
              </p>
              <ResultsList
                results={results}
                onPlayClick={handlePlayClick}
                isPlaying={isPlaying}
                isLoading={isLoading}
                currentEpisode={currentEpisode}
                onPlayStateChange={setIsPlaying}
              />
            </>
          ) : null
        )}
        
        <PodcastPlayer
          episode={currentEpisode}
          seekTime={seekTime}
          isPlaying={isPlaying}
          isLoading={isLoading}
          setIsLoading={setIsLoading}
          onPlayStateChange={setIsPlaying}
          onSeekChange={(ms: number) => setSeekTime({ time: ms, token: Date.now() })}
          onEnded={() => setIsPlaying(false)}
        />
      </div>
    </div>
  );
}

function LoadingScreen() {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        width: '100vw',
        backgroundColor: 'var(--color-bg)',
      }}
    >
      <img
        src="/logo.png"
        alt="Stories Logo"
        style={{
          width: '120px',
          height: '120px',
          animation: 'pulse 2s ease-in-out infinite',
        }}
      />
      <style jsx>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.6;
            transform: scale(1.05);
          }
        }
      `}</style>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <HomeContent />
    </Suspense>
  );
}
