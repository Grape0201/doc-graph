export type NodeType = 'Document' | 'Keyword' | 'Equipment';
export type EdgeType = 'REFERENCES' | 'HAS_KEYWORD' | 'USES_EQUIPMENT';

export interface GraphNode {
  id: string;
  label: string;
  node_type: NodeType;
  properties: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  edge_type: EdgeType;
}

export interface GraphExpandResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  has_more: boolean;
  total_connected: number;
}

export interface SearchResult {
  doc_id: string;
  title: string;
  score: number;
  snippet: string;
  highlights: Record<string, string[]>;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  page: number;
  size: number;
}

export interface DocumentMetadata {
  doc_id: string;
  title: string;
  related_doc_ids: string[];
  keywords: string[];
  equipment_nos: string[];
  pdf_path: string;
  category: string;
  author: string;
  created_date: string;
  department: string;
  document_type: string;
  status: string;
  [key: string]: unknown;
}

export interface NodeDetailResponse {
  node: GraphNode;
  metadata: DocumentMetadata | null;
}
