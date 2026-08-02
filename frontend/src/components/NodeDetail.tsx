import { NodeDetailResponse, NodeType } from '../types';
import { X, ExternalLink, FileText, Key, Wrench } from 'lucide-react';

interface NodeDetailProps {
  nodeDetail: NodeDetailResponse | null;
  isLoading: boolean;
  onClose: () => void;
  onNavigate: (nodeId: string, nodeType: NodeType) => void;
}

export function NodeDetail({ nodeDetail, isLoading, onClose, onNavigate }: NodeDetailProps) {
  if (isLoading) {
    return (
      <div className="detail-panel animate-slide-right" style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div className="search-spinner animate-spin" style={{ position: 'static' }} />
      </div>
    );
  }

  if (!nodeDetail) {
    return null;
  }

  const { node, metadata } = nodeDetail;
  const isDoc = node.node_type === 'Document';
  const isKey = node.node_type === 'Keyword';
  const isEq = node.node_type === 'Equipment';

  let icon = <FileText size={14} />;
  let badgeClass = 'badge doc';
  if (isKey) {
    icon = <Key size={14} />;
    badgeClass = 'badge key';
  } else if (isEq) {
    icon = <Wrench size={14} />;
    badgeClass = 'badge eq';
  }

  return (
    <div className="detail-panel animate-slide-right">
      <div className="detail-header">
        <div>
          <span className={badgeClass} style={{ display: 'flex', alignItems: 'center', gap: '4px', width: 'fit-content' }}>
            {icon} {node.node_type}
          </span>
          <h2 className="detail-title">{node.label}</h2>
        </div>
        <button 
          className="glass-button" 
          style={{ padding: '4px', border: 'none', background: 'transparent' }} 
          onClick={onClose}
        >
          <X size={20} />
        </button>
      </div>

      <div className="detail-content">
        {metadata && isDoc && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
            
            {metadata.pdf_path && (
              <button className="glass-button" style={{ width: '100%', borderColor: 'var(--accent-doc)', color: 'var(--accent-doc)' }}>
                <ExternalLink size={16} /> Open PDF Document
              </button>
            )}

            <div>
              <h3 style={{ fontSize: '0.9rem', marginBottom: '8px', color: 'var(--text-secondary)' }}>Properties</h3>
              <table className="meta-table">
                <tbody>
                  <tr><th>Document ID</th><td>{metadata.doc_id}</td></tr>
                  <tr><th>Category</th><td>{metadata.category || '-'}</td></tr>
                  <tr><th>Type</th><td>{metadata.document_type || '-'}</td></tr>
                  <tr><th>Department</th><td>{metadata.department || '-'}</td></tr>
                  <tr><th>Author</th><td>{metadata.author || '-'}</td></tr>
                  <tr><th>Created</th><td>{metadata.created_date || '-'}</td></tr>
                  <tr><th>Status</th><td>{metadata.status || '-'}</td></tr>
                </tbody>
              </table>
            </div>

            {metadata.keywords && metadata.keywords.length > 0 && (
              <div>
                <h3 style={{ fontSize: '0.9rem', marginBottom: '8px', color: 'var(--text-secondary)' }}>Keywords</h3>
                <div className="tag-list">
                  {metadata.keywords.map(kw => (
                    <span 
                      key={kw} 
                      className="tag" 
                      style={{ cursor: 'pointer', border: '1px solid rgba(0, 230, 138, 0.3)', color: 'var(--accent-keyword)' }}
                      onClick={() => onNavigate(kw, 'Keyword')}
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {metadata.equipment_nos && metadata.equipment_nos.length > 0 && (
              <div>
                <h3 style={{ fontSize: '0.9rem', marginBottom: '8px', color: 'var(--text-secondary)' }}>Equipment</h3>
                <div className="tag-list">
                  {metadata.equipment_nos.map(eq => (
                    <span 
                      key={eq} 
                      className="tag" 
                      style={{ cursor: 'pointer', border: '1px solid rgba(255, 184, 0, 0.3)', color: 'var(--accent-equipment)' }}
                      onClick={() => onNavigate(eq, 'Equipment')}
                    >
                      {eq}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!isDoc && (
          <div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Connected Documents: {Number(metadata?.connected_document_count ?? 0)}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
