import QACard from "./QACard.tsx";
import type { QAResult } from "./types.tsx";
import styles from "./ResultsList.module.css";

interface ResultsListProps {
  results: QAResult[];
  onPlayClick: (episode: QAResult) => void;
}

const ResultsList: React.FC<ResultsListProps> = ({ results, onPlayClick }) => {
  return (
    <div className={styles.resultsList}>
      {results.map((r, i) => (
        <QACard
          key={i}
          result={r}
          onPlayClick={onPlayClick}
        />
      ))}
    </div>
  );
};

export default ResultsList;
