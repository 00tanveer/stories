import React, { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import SearchBar from "./components/SearchBar";
import ResultsList from "./components/ResultsList";
import PodcastPlayer from "./components/PodcastPlayer";
import type { QAResult } from "./components/types";
import { usePostHog } from '@posthog/react';
import styles from "./App.module.css";
import { Button } from "./components/ui/button";

const App: React.FC = () => {
  const posthog = usePostHog();
  const [results, setResults] = useState<QAResult[]>([]);
  const [loading, setLoading] = useState(false);
  // Podcastplayer state to pass as props
  const [sessionId, setSessionId] = useState<string | null>(null);
  type SeekTime = { time: number; token: number };
  const [currentEpisode, setCurrentEpisode] = useState<QAResult | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [seekTime, setSeekTime] = useState<SeekTime | null>(null);

  useEffect(() => {
    if (posthog) {
      const id = posthog.get_session_id();
      setSessionId(id);
    }
  }, [posthog]);

  const handleSearch = async (query: string) => {
    posthog?.capture('clicked_search');
    setLoading(true);
    try {
      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (sessionId) {
        headers['X-POSTHOG-SESSION-ID'] = sessionId;
      }
      const res = await fetch(`${import.meta.env.VITE_API_URL}/search`, {
        method: "POST",
        headers,
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      const docs = data.results.metadatas[0];
      setResults(docs || []);
    } catch (err) {
      console.error("Search error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayClick = (episode: QAResult) => {
    setCurrentEpisode(episode);
    setSeekTime({ time: episode.start ?? 0, token: Date.now() });
    setIsPlaying(true);
  };

  return (
    <div className={styles.appRoot}>
      <Navbar />
      <div className={styles.container}>
        <div className={styles.header}>
          <p className={styles.subtitle}>
            Search for career wisdom, across thousands of conversations ✨
          </p>
          <p className={styles.note}>Currently, just indexed software engineering podcasts. v0.0.alpha-1</p>
        </div>
        <SearchBar onSearch={handleSearch} />
        <div className={styles.suggestions}>
          <p>Suggestions:</p>
          <Button className={styles.suggestionBtn} onClick={() => handleSearch("What should I learn?")}>What should I learn?</Button>
          <Button className={styles.suggestionBtn} onClick={() => handleSearch("Zuckerberg stories")}>Zuckerberg stories?</Button>
          <Button className={styles.suggestionBtn} onClick={() => handleSearch("What career advice would you give?")}>What career advice would you give?</Button>
        </div>
        {loading ? (
          <p className={styles.loading}>Searching...</p>
        ) : (
          <ResultsList results={results} onPlayClick={handlePlayClick} />
        )}
        
        <PodcastPlayer
          episode={currentEpisode}
          seekTime={seekTime}
          isPlaying={isPlaying}
          onPlayStateChange={setIsPlaying}
          onSeekChange={(ms: number) => setSeekTime({ time: ms, token: Date.now() })}
          onEnded={() => setIsPlaying(false)}
        />
      </div>
    </div>
  );
};

export default App;
