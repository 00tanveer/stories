import React, {
  useRef,
  useState,
  useEffect,
} from "react";
import type { QAResult } from "./types";

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
    console.log('seek time changed', seekTime)
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
      <div className="fixed bottom-0 left-0 w-full bg-neutral-900 text-white h-[150px] flex items-center px-6 shadow-2xl">
        {episode.episode_image && (
          <img
            src={episode.episode_image}
            alt={episode.title}
            className="w-20 h-20 max-sm:w-10 max-sm:h-10 rounded-lg object-cover mr-6"
          />
        )}

        <div className="flex flex-col flex-1">
          <h2 className="text-lg font-semibold max-sm:text-sm">{episode.title}</h2>
          <p className="text-xs text-neutral-400 mb-2">
            {Math.round(episode.duration / 60)} min
          </p>

          {/* Custom progress bar */}
          <div className="flex items-center mb-3">
            <span className="text-xs text-neutral-400 w-10 text-right mr-3">
              {formatTime(currentTime)}
            </span>
            <input
              type="range"
              value={progress}
              onChange={handleSeek}
              className="flex-1 h-1 bg-neutral-700 rounded-lg appearance-none cursor-pointer accent-red-500"
            />
            <span className="text-xs text-neutral-400 w-10 ml-3">
              {formatTime(duration)}
            </span>
          </div>

          {/* Controls */}
          <div className="flex justify-center items-center space-x-8 mt-2">
            <button
              onClick={() => skip(-10)}
              className="text-white hover:text-red-400 transition"
            >
              ⏪ 10s
            </button>

            <button
              onClick={togglePlay}
              className="bg-red-500 hover:bg-red-600 rounded-full w-10 h-10 flex items-center justify-center text-white text-lg"
            >
              {isPlaying ? "❚❚" : "▶"}
            </button>

            <button
              onClick={() => skip(10)}
              className="text-white hover:text-red-400 transition"
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
