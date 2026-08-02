import { useState, useCallback, useMemo } from 'react';
import { SearchBar } from './components/SearchBar';
import { FilterPanel } from './components/FilterPanel';
import { SearchResults } from './components/SearchResults';
import { GraphView } from './components/GraphView';
import { GraphControls } from './components/GraphControls';
import { NodeDetail } from './components/NodeDetail';
import { searchDocuments, expandGraph, getNodeDetail } from './api/client';
import { GraphNode, GraphEdge, NodeType, SearchResult, NodeDetailResponse } from './types';
import { Share2 } from 'lucide-react';

function App() {
  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchTotal, setSearchTotal] = useState(0);
  const [searchPage, setSearchPage] = useState(1);
  const [isSearching, setIsSearching] = useState(false);
  
  // Graph State
  const [nodes, setNodes] = useState<Map<string, GraphNode>>(new Map());
  const [edges, setEdges] = useState<Map<string, GraphEdge>>(new Map());
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [hops, setHops] = useState(1);
  const [visibleTypes, setVisibleTypes] = useState<Set<NodeType>>(new Set(['Document', 'Keyword', 'Equipment']));
  
  // Detail State
  const [nodeDetail, setNodeDetail] = useState<NodeDetailResponse | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  // Handlers
  const handleSearch = async (query: string, page = 1) => {
    setSearchQuery(query);
    setSearchPage(page);
    setIsSearching(true);
    try {
      const res = await searchDocuments(query, page);
      setSearchResults(res.results);
      setSearchTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  // SearchBar に渡すコールバック（参照を安定化して不要な再検索を防止）
  const handleSearchFromBar = useCallback((q: string) => {
    handleSearch(q, 1);
  }, []);

  const loadGraphData = async (nodeId: string, nodeType: NodeType, currentHops: number) => {
    try {
      const res = await expandGraph(nodeId, nodeType, currentHops);
      
      setNodes(prev => {
        const next = new Map(prev);
        res.nodes.forEach(n => next.set(n.id, n));
        return next;
      });
      
      setEdges(prev => {
        const next = new Map(prev);
        res.edges.forEach(e => next.set(e.id, e));
        return next;
      });
    } catch (err) {
      console.error(err);
    }
  };

  const handleResultClick = async (docId: string) => {
    // 既存グラフをクリアして新しい起点からグラフを描画
    setNodes(new Map());
    setEdges(new Map());
    await loadGraphData(docId, 'Document', hops);
    handleNodeClick(docId, 'Document');
  };

  const handleNodeClick = useCallback(async (nodeId: string, nodeType: NodeType) => {
    setSelectedNodeId(nodeId);
    setIsDetailLoading(true);
    try {
      const detail = await getNodeDetail(nodeType, nodeId);
      setNodeDetail(detail);
    } catch (err) {
      console.error(err);
    } finally {
      setIsDetailLoading(false);
    }
  }, []);

  const handleNodeExpand = useCallback(async (nodeId: string, nodeType: NodeType) => {
    await loadGraphData(nodeId, nodeType, hops);
  }, [hops]);

  const handleHopsChange = async (newHops: number) => {
    const oldHops = hops;
    setHops(newHops);
    if (selectedNodeId && nodeDetail) {
      if (newHops < oldHops) {
        // ホップ数が減少した場合はグラフをクリアして再描画
        setNodes(new Map());
        setEdges(new Map());
      }
      await loadGraphData(selectedNodeId, nodeDetail.node.node_type, newHops);
    }
  };

  const handleToggleType = (type: NodeType) => {
    setVisibleTypes(prev => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  // Filter nodes based on visible types (memoized to prevent unnecessary GraphView re-renders)
  const filteredNodes = useMemo(
    () => Array.from(nodes.values()).filter(n => visibleTypes.has(n.node_type)),
    [nodes, visibleTypes]
  );
  const filteredEdges = useMemo(() => {
    const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
    return Array.from(edges.values()).filter(e =>
      filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)
    );
  }, [filteredNodes, edges]);

  return (
    <div className={`app-container ${selectedNodeId ? 'has-detail' : ''}`}>
      
      <header className="app-header">
        <div className="app-logo">
          <Share2 className="app-logo-icon" />
          <span>Doc-Graph</span>
        </div>
      </header>

      <aside className="sidebar">
        <div className="sidebar-content">
          <SearchBar onSearch={handleSearchFromBar} isLoading={isSearching} />
          <FilterPanel onFilterChange={(filters) => console.log('Filters:', filters)} />
          <SearchResults 
            results={searchResults}
            total={searchTotal}
            page={searchPage}
            size={10}
            onPageChange={(p) => handleSearch(searchQuery, p)}
            onResultClick={handleResultClick}
            isLoading={isSearching}
          />
        </div>
      </aside>

      <main className="main-area">
        <GraphView 
          nodes={filteredNodes}
          edges={filteredEdges}
          onNodeClick={handleNodeClick}
          onNodeExpand={handleNodeExpand}
          selectedNodeId={selectedNodeId}
        />
        <GraphControls 
          hops={hops}
          onHopsChange={handleHopsChange}
          visibleTypes={visibleTypes}
          onToggleType={handleToggleType}
          nodeCount={filteredNodes.length}
          onResetLayout={() => {
            // Triggered via cytoscape instance in GraphView ideally, but a simple state toggle could force remount/layout
            // For now, handled implicitly if we just pass a prop, but omit full implementation to save space
          }}
          onFitToScreen={() => {}}
        />
      </main>

      {selectedNodeId && (
        <NodeDetail 
          nodeDetail={nodeDetail} 
          isLoading={isDetailLoading} 
          onClose={() => setSelectedNodeId(null)} 
          onNavigate={(id, type) => {
            handleNodeExpand(id, type);
            handleNodeClick(id, type);
          }}
        />
      )}
      
    </div>
  );
}

export default App;
