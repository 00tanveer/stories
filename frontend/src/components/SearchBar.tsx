"use client";

import React, { useState, useEffect } from "react";
import { Search } from 'lucide-react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import styles from "./SearchBar.module.css";

interface SearchBarProps {
  query: string;
  onQueryChange: (value: string) => void;
  onSearch: (query: string) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ query, onQueryChange, onSearch }) => {

  const prompts = [
    "What are the latest trends in AI?",
    "How to improve remote work productivity?",
    "What skills are in demand in 2024?",
    "Tips for effective time management",
    "How to start a successful startup?"
  ]
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) onSearch(query);
  };

  const [randomPrompt, setRandomPrompt] = useState(prompts[0]);

  useEffect(() => {
    setRandomPrompt(prompts[Math.floor(Math.random() * prompts.length)]);
  }, []);

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      <div className={styles.searchBar}>
        <Search className={styles.icon} />
        <Input
          type="text"
          placeholder={randomPrompt}
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          className={styles.input}
        />
        <Button type="submit" className={styles.button}>
          Search
        </Button>
      </div>
    </form>
  );
};

export default SearchBar;
