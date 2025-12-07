import React from "react";
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
