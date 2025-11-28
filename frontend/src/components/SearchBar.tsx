import React, { useState } from "react";
import { Search } from 'lucide-react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import styles from "./SearchBar.module.css";

interface SearchBarProps {
  onSearch: (query: string) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch }) => {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) onSearch(query);
  };

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      <div className={styles.searchBar}>
        <Search className={styles.icon} />
        <Input
          type="text"
          placeholder="Ask any career questions..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
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
