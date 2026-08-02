import { GraphExpandResponse, NodeDetailResponse, SearchResponse } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function searchDocuments(query: string, page = 1, size = 10): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query, page: page.toString(), size: size.toString() });
  const response = await fetch(`${API_BASE}/api/search?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to search documents');
  }
  return response.json();
}

export async function expandGraph(nodeId: string, nodeType: string, hops = 1, limit = 50): Promise<GraphExpandResponse> {
  const params = new URLSearchParams({ 
    node_id: nodeId, 
    node_type: nodeType, 
    hops: hops.toString(), 
    limit: limit.toString() 
  });
  const response = await fetch(`${API_BASE}/api/graph/expand?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to expand graph');
  }
  return response.json();
}

export async function getNodeDetail(nodeType: string, nodeId: string): Promise<NodeDetailResponse> {
  const response = await fetch(`${API_BASE}/api/graph/node/${nodeType}/${nodeId}`);
  if (!response.ok) {
    throw new Error('Failed to get node detail');
  }
  return response.json();
}
