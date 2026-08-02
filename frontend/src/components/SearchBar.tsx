import { useState, useEffect, useRef } from 'react';
import { Search } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

export function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const onSearchRef = useRef(onSearch);
  onSearchRef.current = onSearch;

  useEffect(() => {
    const timer = setTimeout(() => {
      if (query.trim()) {
        onSearchRef.current(query);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]); // onSearch は ref 経由で参照するため依存配列に含めない

  return (
    <div className="search-container">
      <Search className="search-icon" size={18} />
      <input
        type="text"
        className="glass-input search-input"
        placeholder="Search documents, keywords..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {isLoading && <div className="search-spinner animate-spin" />}
    </div>
  );
}
