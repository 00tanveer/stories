import React from "react";
import styles from "./ResultsDisplay.module.css";

interface QAResult {
  question: string;
  similarity: number;
  answer?: string;
}

interface ResultsDisplayProps {
  results: QAResult[];
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results }) => {
  if (results.length === 0)
    return <p className={styles.empty}>No results yet.</p>;

  return (
    <div className={styles.resultsGrid}>
      {/* Left Column - Similar Questions */}
      <div className={styles.section}>
        <h2 className={styles.heading}>Similar Questions</h2>
        <ul className={styles.list}>
          {results.map((item, i) => (
            <li key={i} className={styles.item}>
              <p className={styles.question}>{item.question}</p>
              <p className={styles.similarity}>
                Similarity: {item.similarity.toFixed(4)}
              </p>
            </li>
          ))}
        </ul>
      </div>

      {/* Right Column - Answers */}
      <div className={styles.section}>
        <h2 className={styles.heading}>Answers</h2>
        <ul className={styles.list}>
          {results.map((item, i) => (
            <li key={i} className={styles.item}>
              <p className={styles.answer}>
                {item.answer || "No answer loaded yet."}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default ResultsDisplay;
