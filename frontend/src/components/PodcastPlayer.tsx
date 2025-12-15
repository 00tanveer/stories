"use client";

import React, { useRef, useState, useEffect } from "react";
import type { QAResult } from "./types";
import styles from "./PodcastPlayer.module.css";
import { Button } from "./ui/button";

export interface PodcastPlayerHandle {
  seekTo: (seconds: number) => void;
  play: () => void;
  pause: () => void;
}

import Spinner from "./Spinner";

interface PodcastPlayerProps {
  episode: QAResult | null;
  seekTime: { time: number; token: number } | null;
  isPlaying: boolean;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
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
  isLoading,
  setIsLoading,
  seekTime,
  onPlayStateChange,
  onSeekChange,
  onEnded,
}) =>{
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [progress, setProgress] = useState(0);
    const [showModal, setShowModal] = useState(false);
    
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
      // Only set loading if audio is not already ready to play
      if (audio.readyState < 3) {
        setIsLoading(true);
      } else {
        setIsLoading(false);
      }
      audio.play().catch(err => {
        setIsLoading(false);
        console.warn("Play failed:", err);
      });
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
      if (seekTime?.time != null) {
        audio.currentTime = seekTime.time / 1000;
      }
      if (isPlaying) {
        audio.play().catch(err => console.warn("Autoplay failed:", err));
      }
    };
    const handleCanPlay = () => {
      setIsLoading(false);
    };
    audio.addEventListener("loadedmetadata", handleLoaded);
    audio.addEventListener("canplay", handleCanPlay);
    return () => {
      audio.removeEventListener("loadedmetadata", handleLoaded);
      audio.removeEventListener("canplay", handleCanPlay);
    };
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
    <>
      <div className={styles.player}>
        {episode.episode_image && (
          <img
            src={episode.episode_image}
            alt={episode.title}
            className={styles.episodeImage}
          />
        )}
        <Button className={styles.shownotes} onClick={() => setShowModal(true)}>
          Show Notes
        </Button>

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
              disabled={isLoading}
              aria-label={isPlaying ? "Pause" : "Play"}
            >
              {isLoading ? <Spinner size={20} /> : (isPlaying ? "❚❚" : "▶")}
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

      {/* Modal */}
      {showModal && (
        <div className={styles.modalOverlay} onClick={() => setShowModal(false)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>Show Notes</h2>
              <button className={styles.modalClose} onClick={() => setShowModal(false)}>
                ✕
              </button>
            </div>
            <div className={styles.modalBody}>
              <p>{episode.episode_description || "No show notes available."}</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default PodcastPlayer;
