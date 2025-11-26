import React, { useState, useEffect } from "react";
import SearchBar from "./components/SearchBar";
import ResultsList from "./components/ResultsList";
import PodcastPlayer from "./components/PodcastPlayer";
import type { QAResult } from "./components/types";
import { usePostHog } from '@posthog/react'

const App: React.FC = () => {
  const posthog = usePostHog()
  const [results, setResults] = useState<QAResult[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Podcastplayer state to pass as props
  const [sessionId, setSessionId] = useState<string | null>(null)
  type SeekTime = { time: number; token: number };
  const [currentEpisode, setCurrentEpisode] = useState<QAResult | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [seekTime, setSeekTime] = useState<SeekTime | null>(null);

  useEffect(() => {
        if (posthog) {
            const id = posthog.get_session_id()
            setSessionId(id)
        }
    }, [posthog])
  const handleSearch = async (query: string) => {
    posthog?.capture('clicked_search')
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
    console.log(episode.start)
    setCurrentEpisode(episode);
    // episode.start is optional on QAResult, ensure we pass a number
    setSeekTime({ time: episode.start ?? 0, token: Date.now() });
    setIsPlaying(true);
  };

  

  return (
    <div className="w-screen h-screen flex flex-col items-center justify-start py-5 px-5 bg-gray-100">
      <h1 className="title text-3xl font-bold mb-6 text-black">Stories</h1>
      <h2 className="text-xl font-bold mb-6 mx-2 text-center text-black">🎯 Search for wisdom, across thousands of conversations</h2>
      <SearchBar onSearch={handleSearch} />
      {loading ? (
        <p className="text-gray-600 mt-6">Searching...</p>
      ) : (
        <ResultsList results={results} onPlayClick={handlePlayClick}/>
      )}
      <PodcastPlayer
        episode={currentEpisode}
        seekTime={seekTime}
        isPlaying={isPlaying}
        onPlayStateChange={setIsPlaying}
        // PodcastPlayer expects onSeekChange: (ms: number) => void
        onSeekChange={(ms: number) => setSeekTime({ time: ms, token: Date.now() })}
        onEnded={() => setIsPlaying(false)}
      />
    </div>
  );
};

export default App;
