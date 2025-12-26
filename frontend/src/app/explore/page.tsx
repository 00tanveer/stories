"use client";

import React from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import appStyles from "../../App.module.css";
import styles from "./explore.module.css";

export default function ExplorePage() {
  return (
    <div className={appStyles.appRoot}>
        <Navbar />
        <div className={appStyles.container}>
          <div className={appStyles.header}>
            <p className={appStyles.subtitle}>
              Discover trending topics, popular episodes, and featured creators
            </p>
          </div>

        {/* Categories Section */}
        <div className={styles.categoriesSection}>
          <h2 className={styles.sectionTitle}>
            📂 Browse by Category
          </h2>
          <div className={styles.categoriesGrid}>
            <Link href="/pods/technology" className={styles.categoryCard}>
              <div className={styles.categoryIcon}>💻</div>
              <h3 className={styles.categoryTitle}>Technology</h3>
              <p className={styles.categoryDescription}>
                Explore tech podcasts, innovations, and insights
              </p>
            </Link>
          </div>
        </div>

        {/* Trending Topics Section */}
        <div className={styles.topicsSection}>
          <h2 className={styles.sectionTitle}>
            🔥 Trending Topics
          </h2>
          <div className={styles.topicsGrid}>
            {['AI & Technology', 'Startup Stories', 'Career Advice', 'Life Lessons', 'Leadership', 'Innovation'].map(topic => (
              <div key={topic} className={styles.topicCard}>
                <h3 className={styles.topicTitle}>{topic}</h3>
                <p className={styles.topicDescription}>
                  Explore stories about {topic.toLowerCase()}
                </p>
              </div>
            ))}
          </div>

          {/* Featured Episodes Section */}
          <h2 className={styles.sectionTitle}>
            ⭐ Featured Episodes
          </h2>
          <div className={styles.episodesGrid}>
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className={styles.episodeCard}>
                <div className={styles.episodeThumbnail} />
                <h3 className={styles.episodeTitle}>
                  Featured Episode {i}
                </h3>
                <p className={styles.episodeMeta}>
                  Podcast Name • 45 min
                </p>
                <p className={styles.episodeDescription}>
                  Discover insights and stories that matter...
                </p>
              </div>
            ))}
          </div>

          {/* Top Creators Section */}
          <h2 className={styles.sectionTitle}>
            🎙️ Top Creators
          </h2>
          <div className={styles.creatorsGrid}>
            {['Alex Hormozi', 'Lex Fridman', 'Joe Rogan', 'Tim Ferriss', 'Naval Ravikant', 'Sam Altman'].map(creator => (
              <div key={creator} className={styles.creatorCard}>
                <div className={styles.creatorAvatar} />
                <h3 className={styles.creatorName}>{creator}</h3>
                <p className={styles.creatorEpisodeCount}>
                  {Math.floor(Math.random() * 50 + 10)} episodes
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
