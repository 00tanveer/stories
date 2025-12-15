import QACard from "./QACard";
import type { QAResult } from "./types.tsx";
import styles from "./ResultsList.module.css";

interface ResultsListProps {
  results: QAResult[];
  onPlayClick: (episode: QAResult) => void;
  isPlaying: boolean;
  isLoading: boolean;
  currentEpisode: QAResult | null;
  onPlayStateChange: (playing: boolean) => void;
}

const ResultsList: React.FC<ResultsListProps> = ({ results, onPlayClick, isPlaying, isLoading, currentEpisode, onPlayStateChange }) => {
  return (
    <div className={styles.resultsList}>
      {results.map((r, i) => (
        <QACard
          key={i}
          result={r}
          onPlayClick={onPlayClick}
          isPlaying={Boolean(isPlaying && currentEpisode && r.id === currentEpisode.id)}
          isLoading={Boolean(isLoading && isPlaying && currentEpisode && r.id === currentEpisode.id)}
          onPlayStateChange={onPlayStateChange}
        />
      ))}
    </div>
  );
};

export default ResultsList;
