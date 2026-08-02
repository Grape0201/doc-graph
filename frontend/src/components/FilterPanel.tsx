import { useState } from 'react';
import { ChevronDown, ChevronUp, Filter } from 'lucide-react';

interface FilterPanelProps {
  onFilterChange: (filters: Record<string, string>) => void;
}

export function FilterPanel({ onFilterChange }: FilterPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [filters, setFilters] = useState({
    document_type: '',
    department: '',
    status: '',
  });

  const handleChange = (key: string, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const clearFilters = () => {
    const emptyFilters = { document_type: '', department: '', status: '' };
    setFilters(emptyFilters);
    onFilterChange(emptyFilters);
  };

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: 'var(--spacing-md)' }}>
      <div 
        className="filter-header" 
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', margin: 0 }}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={16} /> Filters
        </span>
        {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </div>

      {isOpen && (
        <div style={{ marginTop: 'var(--spacing-md)' }} className="animate-slide-up">
          <div className="filter-section">
            <div className="filter-group">
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Document Type</label>
              <select 
                className="glass-input glass-select"
                value={filters.document_type}
                onChange={(e) => handleChange('document_type', e.target.value)}
              >
                <option value="">All Types</option>
                <option value="manual">Manual</option>
                <option value="specification">Specification</option>
                <option value="report">Report</option>
              </select>
            </div>
          </div>
          
          <div className="filter-section">
            <div className="filter-group">
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Department</label>
              <select 
                className="glass-input glass-select"
                value={filters.department}
                onChange={(e) => handleChange('department', e.target.value)}
              >
                <option value="">All Departments</option>
                <option value="engineering">Engineering</option>
                <option value="maintenance">Maintenance</option>
                <option value="operations">Operations</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 'var(--spacing-md)' }}>
            <button className="glass-button" style={{ padding: '4px 8px', fontSize: '0.8rem' }} onClick={clearFilters}>
              Clear
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
