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
      
      // Transform combined results into QAResult format
      const metadatas = data.results.metadatas[0] || [];
      const documents = data.results.documents[0] || [];
      const distances = data.results.distances[0] || [];
      const sources = data.results.sources?.[0] || [];
      
      const transformedResults: QAResult[] = metadatas.map((metadata: any, index: number) => {
        const source = sources[index];
        const document = documents[index];
        
        // Base fields that exist in both collections
        const baseResult = {
          id: metadata.id,
          title: metadata.title || '',
          podcast_title: metadata.podcast_title || '',
          episode_description: metadata.description || '',
          author: metadata.author || '',
          date_published: metadata.date_published || '',
          duration: metadata.duration || 0,
          enclosure_url: metadata.enclosure_url || '',
          start: metadata.start,
          end: metadata.end,
          episode_image: metadata.episode_image || '',
          podcast_url: metadata.podcast_url || '',
          similarity: distances[index] || 0,
        };
        
        // Add fields specific to the source collection
        if (source === 'qa_collection') {
          return {
            ...baseResult,
            question: metadata.question || '',
            answer: metadata.answer || '',
            // utterance: document || '',
          };
        } else {
          // utterances_collection - use the document as the utterance
          return {
            ...baseResult,
            question: '',
            answer: '',
            utterance: document,
          };
        }
      });
      // console.log(transformedResults);
      setResults(transformedResults);
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
          <p className={styles.note}>Currently, just indexed software engineering podcasts. v0.0.1-alpha</p>
        </div>
        <SearchBar onSearch={handleSearch} />
        <div className={styles.suggestions}>
          <p>Suggestions:</p>
          <Button className={styles.suggestionBtn} onClick={() => handleSearch("How to be the top 1% software engineer?")}>How to be the top 1% software engineer?</Button>
          <Button className={styles.suggestionBtn} onClick={() => handleSearch("Zuckerberg stories")}>Zuckerberg stories?</Button>
          <Button className={styles.suggestionBtn} onClick={() => handleSearch("What career advice would you give?")}>What career advice would you give?</Button>
          <Button className={styles.suggestionBtn} onClick={() => handleSearch("Career horror stories")}>Career horror stories</Button>
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
