export interface QAResult {
  id: string;
  title: string;
  podcast_title: string;
  episode_description: string;
  author: string;
  question: string;
  answer: string;
  date_published: string;
  duration: number;
  enclosure_url: string;
  start?: number; // optional, ms if you keep it
  end?: number;
  episode_image?: string;
  podcast_url?: string;
}