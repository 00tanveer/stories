"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import SearchBar from "@/components/SearchBar";
import appStyles from "../App.module.css";
import styles from "./page.module.css";
import { Button } from "@/components/ui/button";
import Link from "next/link";

function HomeContent() {
  const router = useRouter();
  const [query, setQuery] = useState("");

  const suggestions = [
    "How to be the top 1% software engineer?",
    "Zuckerberg stories",
    "What career advice would you give?",
    "Career horror stories"
  ];

  const handleSearch = (searchQuery: string) => {
    // Navigate to /search with query param
    const params = new URLSearchParams();
    params.set('q', searchQuery);
    router.push(`/search?${params.toString()}`);
  };

  return (
    <div className={appStyles.appRoot}>
      <Navbar />
      <div className={appStyles.container}>
        {/* Hero Section */}
        <div className={styles.hero}>
          <h1 className={styles.heroTitle}>
            Discover Stories That Matter
          </h1>
          <p className={appStyles.subtitle}>
            Search for insightful stories, across thousands of conversations ✨
          </p>
          <p className={appStyles.note}>Just ask a question!</p>
        </div>

        {/* Search Bar */}
        <SearchBar
          query={query}
          onQueryChange={setQuery}
          onSearch={handleSearch}
        />

        {/* Suggestions */}
        <div className={appStyles.suggestions}>
          <p>Try these:</p>
          {
            suggestions.map(s => (
              <Button 
                key={s} 
                className={appStyles.suggestionBtn} 
                onClick={() => { setQuery(s); handleSearch(s); }}
              >
                {s}
              </Button>
            ))
          }
        </div>

        {/* Feature Cards */}
        <div className={styles.featureGrid}>
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>🔍</div>
            <h3 className={styles.featureTitle}>Smart Search</h3>
            <p className={styles.featureDescription}>
              Ask questions naturally and get relevant podcast moments instantly
            </p>
          </div>

          <Link href="/explore" style={{ textDecoration: 'none', color: 'inherit' }}>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>🎙️</div>
              <h3 className={styles.featureTitle}>Explore</h3>
              <p className={styles.featureDescription}>
                Browse trending topics, featured episodes, and top creators
              </p>
            </div>
          </Link>

          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>⚡</div>
            <h3 className={styles.featureTitle}>Instant Playback</h3>
            <p className={styles.featureDescription}>
              Jump directly to the exact moment in any podcast episode
            </p>
          </div>
        </div>

        {/* CTA Section */}
        <div className={styles.ctaSection}>
          <h2 className={styles.ctaTitle}>
            Ready to discover?
          </h2>
          <p className={styles.ctaDescription}>
            Start searching for stories that inspire, educate, and entertain
          </p>
          <Button 
            onClick={() => router.push('/search')}
            className={styles.ctaButton}
          >
            Start Searching
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  return <HomeContent />;
}
