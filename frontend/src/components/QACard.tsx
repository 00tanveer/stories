import { Play, Clock, Calendar } from 'lucide-react';
import { Card, CardContent, CardHeader } from './ui/card';
import { Button } from './ui/button';
import type { QAResult } from './types';
import { useState } from 'react';
import styles from './QACard.module.css';

interface QACardProps {
  result: QAResult;
  onPlayClick: (episode: QAResult) => void;
}
export default function QACard({ result, onPlayClick }: QACardProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const truncatedAnswer = !isExpanded && result.answer.length > 300 
      ? result.answer.slice(0, 300) + "..." 
      : result.answer;
    const handlePlay = () => {
        onPlayClick(result);
    }
    return (
    <Card className={styles.card}>
      <CardHeader className={styles.header}>
        <div className={styles.headerRow}>
          <div style={{ flex: 1 }}>
            <span>
              {result.episode_image && (
              <img 
                src={result.episode_image}
                alt={result.title}
                className={styles.episodeImage}
              />)}
              <h3 className={styles.title}>
                {result.question}
              </h3>

            </span>
            <div className={styles.meta}>
              <span className={styles.author}>{result.podcast_title}</span>
              <span className={styles.metaDot}>•</span>
              <span>{result.author}</span>
               <Button
                onClick={handlePlay}
                size="icon"
                className={styles.playBtn}
              >
                <Play style={{ width: 16, height: 16 }} fill="currentColor" />
              </Button>
            </div>
          </div>
         
        </div>
      </CardHeader>
      <CardContent>
        <p className={styles.content}>
          {truncatedAnswer}
        </p>
        {result.answer.length > 300 && (
        <Button 
            onClick={() => setIsExpanded(!isExpanded)}
            className={styles.showBtn}
            >
            {isExpanded ? "Show less" : "Show more"}
            </Button>
        )}
        <div className={styles.footer}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <Calendar style={{ width: 16, height: 16 }} />
            <span>{new Date(result.date_published).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            Hear at 
            <Clock style={{ width: 16, height: 16 }} />
            <span>{(() => {
                const ms = result.start ?? 0;
                const totalSeconds = Math.max(0, Math.floor(ms / 1000));
                const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
                const seconds = (totalSeconds % 60).toString().padStart(2, '0');
                return `${minutes}:${seconds}`;
            })()}</span>
          </div>
          <span className={styles.footerDot}>•</span>
          <span className={styles.italic}>{result.title}</span>
        </div>
      </CardContent>
    </Card>
  );
}