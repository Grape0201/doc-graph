import { SearchResult } from '../types';
import { ChevronLeft, ChevronRight, FileText } from 'lucide-react';

interface SearchResultsProps {
  results: SearchResult[];
  total: number;
  page: number;
  size: number;
  onPageChange: (page: number) => void;
  onResultClick: (docId: string) => void;
  isLoading: boolean;
}

export function SearchResults({ 
  results, total, page, size, onPageChange, onResultClick, isLoading 
}: SearchResultsProps) {
  if (isLoading && results.length === 0) {
    return <div style={{ textAlign: 'center', padding: 'var(--spacing-xl)', color: 'var(--text-muted)' }}>Searching...</div>;
  }

  if (!isLoading && results.length === 0 && total === 0) {
    return <div style={{ textAlign: 'center', padding: 'var(--spacing-xl)', color: 'var(--text-muted)' }}>No results found</div>;
  }

  const totalPages = Math.ceil(total / size);

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: 'var(--spacing-md)', flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div className="results-header">
        <span>{total} results found</span>
        <span>Page {page} of {totalPages}</span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {results.map((result) => (
          <div 
            key={result.doc_id} 
            className="result-item"
            onClick={() => onResultClick(result.doc_id)}
          >
            <div className="result-title">
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <FileText size={14} />
                {result.title}
              </span>
              <span className="result-score">{(result.score * 100).toFixed(0)}%</span>
            </div>
            <div 
              className="result-snippet"
              dangerouslySetInnerHTML={{ __html: result.snippet }}
            />
          </div>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button 
            className="glass-button" 
            style={{ padding: '4px 8px' }}
            disabled={page === 1}
            onClick={() => onPageChange(page - 1)}
          >
            <ChevronLeft size={16} /> Prev
          </button>
          <button 
            className="glass-button" 
            style={{ padding: '4px 8px' }}
            disabled={page === totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            Next <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
