import { NodeType } from '../types';
import { Maximize, RotateCcw, FileText, Key, Wrench } from 'lucide-react';

interface GraphControlsProps {
  hops: number;
  onHopsChange: (hops: number) => void;
  visibleTypes: Set<NodeType>;
  onToggleType: (type: NodeType) => void;
  nodeCount: number;
  onResetLayout: () => void;
  onFitToScreen: () => void;
}

export function GraphControls({
  hops, onHopsChange, visibleTypes, onToggleType, nodeCount, onResetLayout, onFitToScreen
}: GraphControlsProps) {
  return (
    <div className="glass-panel graph-controls animate-slide-up">
      <div className="control-group">
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Nodes: {nodeCount}</span>
      </div>
      
      <div className="control-group">
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginRight: '4px' }}>Hops</span>
        <input 
          type="range" 
          min="1" max="3" 
          value={hops} 
          onChange={(e) => onHopsChange(parseInt(e.target.value))}
          style={{ width: '60px' }}
        />
        <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{hops}</span>
      </div>

      <div className="control-group">
        <div 
          className={`type-toggle doc ${visibleTypes.has('Document') ? 'active' : ''}`}
          onClick={() => onToggleType('Document')}
          title="Toggle Documents"
        >
          <FileText size={16} />
        </div>
        <div 
          className={`type-toggle key ${visibleTypes.has('Keyword') ? 'active' : ''}`}
          onClick={() => onToggleType('Keyword')}
          title="Toggle Keywords"
        >
          <Key size={16} />
        </div>
        <div 
          className={`type-toggle eq ${visibleTypes.has('Equipment') ? 'active' : ''}`}
          onClick={() => onToggleType('Equipment')}
          title="Toggle Equipment"
        >
          <Wrench size={16} />
        </div>
      </div>

      <div className="control-group" style={{ borderRight: 'none', paddingRight: 0 }}>
        <button className="glass-button" style={{ padding: '6px' }} onClick={onResetLayout} title="Reset Layout">
          <RotateCcw size={16} />
        </button>
        <button className="glass-button" style={{ padding: '6px' }} onClick={onFitToScreen} title="Fit to Screen">
          <Maximize size={16} />
        </button>
      </div>
    </div>
  );
}
