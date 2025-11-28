import React, { useRef, useState, useEffect } from "react";
import type { QAResult } from "./types";
import styles from "./PodcastPlayer.module.css";

export interface PodcastPlayerHandle {
  seekTo: (seconds: number) => void;
  play: () => void;
  pause: () => void;
}

interface PodcastPlayerProps {
  episode: QAResult | null;
  seekTime: { time: number; token: number } | null;
  isPlaying: boolean;
  onPlayStateChange: (playing: boolean) => void;
  onSeekChange: (ms: number) => void;
  onEnded?: () => void;
}

const formatTime = (seconds: number): string => {
  if (isNaN(seconds)) return "00:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
};

const PodcastPlayer: React.FC<PodcastPlayerProps> = ({
  episode,
  isPlaying,
  seekTime,
  onPlayStateChange,
  onSeekChange,
  onEnded,
}) =>{
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [progress, setProgress] = useState(0);
    
    // Load Episode when it changes
    useEffect(() => {
    if (!episode || !audioRef.current) return;

    const audio = audioRef.current;
    audio.src = episode.enclosure_url;
    audio.load();

    // Reset state for new episode
    setCurrentTime(0);
    setDuration(0);
    setProgress(0);

  }, [episode]);

  // Play/pause based on isPlaying prop
  useEffect(() => {
    if (!audioRef.current) return;

    const audio = audioRef.current;
    if (isPlaying) {
      audio.play().catch(err => console.warn("Play failed:", err));
    } else {
      audio.pause();
    }

  }, [isPlaying]);

  // Seek when seekTime changes
  useEffect(() => {
    if (!audioRef.current) return;
    if (seekTime == null) return;

    audioRef.current.currentTime = seekTime.time / 1000;

  }, [seekTime?.token]);

  // Metadata loaded - set duration and other items
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleLoaded = () => {
      setDuration(audio.duration || episode?.duration || 0);

      // 🟢 Auto-seek AFTER load (guard for null seekTime)
      if (seekTime?.time != null) {
        audio.currentTime = seekTime.time / 1000;
      }
      // 🟢 Auto-play AFTER the new source is ready
      if (isPlaying) {
        audio.play().catch(err => console.warn("Autoplay failed:", err));
      }

    };

    audio.addEventListener("loadedmetadata", handleLoaded);
    return () => audio.removeEventListener("loadedmetadata", handleLoaded);
  }, [episode]);

  // Track progress + emit playing state upward
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const update = () => {
      setCurrentTime(audio.currentTime);
      setDuration(audio.duration || 0);

      if (audio.duration) {
        setProgress((audio.currentTime / audio.duration) * 100);
      }

      onPlayStateChange?.(!audio.paused);
    };

    const handleEnded = () => {
      onEnded?.();
      onPlayStateChange?.(false);
    };

    audio.addEventListener("timeupdate", update);
    audio.addEventListener("ended", handleEnded);

    return () => {
      audio.removeEventListener("timeupdate", update);
      audio.removeEventListener("ended", handleEnded);
    };
  }, [onPlayStateChange, onEnded]);
  /////////
  // User scrubs via slider
  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!audioRef.current) return;
    const pct = Number(e.target.value);
    const newTime = (pct / 100) * duration;

    audioRef.current.currentTime = newTime;
    setProgress(pct);
  };

  //
  // Declarative toggle play
  //
  const togglePlay = () => {
    onPlayStateChange(!isPlaying);
  };
  //
  // Declarative skip
  //
  const skip = (deltaSeconds: number) => {
    if (!audioRef.current) return;

    const newSeconds = Math.min(
      Math.max(audioRef.current.currentTime + deltaSeconds, 0),
      duration
    );

    onSeekChange(newSeconds * 1000);
  };


  if (!episode) return null;
  return (
    <div className={styles.player}>
      {episode.episode_image && (
        <img
          src={episode.episode_image}
          alt={episode.title}
          className={styles.episodeImage}
        />
      )}

      <div className={styles.info}>
        <h2 className={styles.title}>{episode.title}</h2>
        <p className={styles.duration}>
          {Math.round(episode.duration / 60)} min
        </p>

        {/* Custom progress bar */}
        <div className={styles.progressRow}>
          <span className={styles.time}>{formatTime(currentTime)}</span>
          <input
            type="range"
            value={progress}
            onChange={handleSeek}
            className={styles.progressBar}
          />
          <span className={`${styles.time} ${styles.timeEnd}`}>{formatTime(duration)}</span>
        </div>

        {/* Controls */}
        <div className={styles.controls}>
          <button
            onClick={() => skip(-10)}
            className={styles.controlBtn}
          >
            ⏪ 10s
          </button>

          <button
            onClick={togglePlay}
            className={styles.playBtn}
          >
            {isPlaying ? "❚❚" : "▶"}
          </button>

          <button
            onClick={() => skip(10)}
            className={styles.controlBtn}
          >
            10s ⏩
          </button>
        </div>
      </div>

      <audio ref={audioRef} src={episode.enclosure_url} preload="metadata" />
    </div>
  );
}

export default PodcastPlayer;
