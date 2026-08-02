from neo4j import GraphDatabase
from backend.app.config import settings
from backend.app.models.graph import GraphNode, GraphEdge, GraphExpandResponse
import uuid

class Neo4jClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jClient, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        self.driver = GraphDatabase.driver(settings.NEO4J_URI, auth=None)

    def initialize(self):
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT doc_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.doc_id IS UNIQUE")
            session.run("CREATE CONSTRAINT keyword_name_unique IF NOT EXISTS FOR (k:Keyword) REQUIRE k.name IS UNIQUE")
            session.run("CREATE CONSTRAINT equip_no_unique IF NOT EXISTS FOR (e:Equipment) REQUIRE e.equipment_no IS UNIQUE")

    def create_document_node(self, doc_id: str, title: str, properties: dict):
        with self.driver.session() as session:
            session.run(
                """
                MERGE (d:Document {doc_id: $doc_id})
                SET d.title = $title, d += $props
                """,
                doc_id=doc_id, title=title, props=properties
            )

    def create_reference_edge(self, from_doc_id: str, to_doc_id: str):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (a:Document {doc_id: $from_id})
                MATCH (b:Document {doc_id: $to_id})
                MERGE (a)-[:REFERENCES]->(b)
                """,
                from_id=from_doc_id, to_id=to_doc_id
            )

    def create_keyword_node_and_edge(self, doc_id: str, keyword: str):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (d:Document {doc_id: $doc_id})
                MERGE (k:Keyword {name: $keyword})
                MERGE (d)-[:HAS_KEYWORD]->(k)
                """,
                doc_id=doc_id, keyword=keyword
            )

    def create_equipment_node_and_edge(self, doc_id: str, equipment_no: str):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (d:Document {doc_id: $doc_id})
                MERGE (e:Equipment {equipment_no: $equipment_no})
                MERGE (d)-[:USES_EQUIPMENT]->(e)
                """,
                doc_id=doc_id, equipment_no=equipment_no
            )

    def expand_graph(self, node_id: str, node_type: str, hops: int, limit: int) -> GraphExpandResponse:
        nodes_dict = {}
        edges_list = []
        has_more = False
        total_connected = 0
        
        if node_type == "Document":
            id_field = "doc_id"
        elif node_type == "Keyword":
            id_field = "name"
        else:
            id_field = "equipment_no"

        with self.driver.session() as session:
            # First, check total connections to determine if hub
            count_res = session.run(
                f"""
                MATCH (start:{node_type} {{{id_field}: $node_id}})-[*]-(connected)
                RETURN count(distinct connected) as total
                """,
                node_id=node_id
            )
            total_connected = count_res.single()["total"]
            if total_connected > limit:
                has_more = True

            # Then, get paths with limit
            res = session.run(
                f"""
                MATCH path = (start:{node_type} {{{id_field}: $node_id}})-[*1..{hops}]-(connected)
                RETURN path
                LIMIT $limit
                """,
                node_id=node_id, limit=limit
            )

            for record in res:
                path = record["path"]
                for node in path.nodes:
                    n_id = node.get("doc_id") or node.get("name") or node.get("equipment_no")
                    if n_id not in nodes_dict:
                        label = list(node.labels)[0]
                        label_name = node.get("title") or n_id
                        nodes_dict[n_id] = GraphNode(
                            id=str(n_id),
                            label=str(label_name),
                            node_type=label,
                            properties=dict(node)
                        )
                for rel in path.relationships:
                    start_node = rel.start_node
                    end_node = rel.end_node
                    s_id = start_node.get("doc_id") or start_node.get("name") or start_node.get("equipment_no")
                    e_id = end_node.get("doc_id") or end_node.get("name") or end_node.get("equipment_no")
                    
                    edges_list.append(GraphEdge(
                        id=f"{s_id}-{rel.type}-{e_id}",
                        source=str(s_id),
                        target=str(e_id),
                        edge_type=rel.type
                    ))

            # Deduplicate edges
            unique_edges = {edge.id: edge for edge in edges_list}.values()

        return GraphExpandResponse(
            nodes=list(nodes_dict.values()),
            edges=list(unique_edges),
            has_more=has_more,
            total_connected=total_connected
        )

    def get_node_detail(self, node_id: str, node_type: str) -> GraphNode | None:
        if node_type == "Document":
            id_field = "doc_id"
        elif node_type == "Keyword":
            id_field = "name"
        else:
            id_field = "equipment_no"

        with self.driver.session() as session:
            res = session.run(
                f"MATCH (n:{node_type} {{{id_field}: $node_id}}) RETURN n",
                node_id=node_id
            )
            record = res.single()
            if record:
                node = record["n"]
                n_id = node.get(id_field)
                label_name = node.get("title") or n_id
                return GraphNode(
                    id=str(n_id),
                    label=str(label_name),
                    node_type=node_type,
                    properties=dict(node)
                )
        return None

    def count_connected_documents(self, node_id: str, node_type: str) -> int:
        """Keyword または Equipment に接続されている Document ノードの数を返す"""
        if node_type == "Keyword":
            id_field = "name"
        else:
            id_field = "equipment_no"

        with self.driver.session() as session:
            res = session.run(
                f"""
                MATCH (n:{node_type} {{{id_field}: $node_id}})-[]-(d:Document)
                RETURN count(distinct d) as cnt
                """,
                node_id=node_id
            )
            record = res.single()
            return record["cnt"] if record else 0

    def close(self):
        self.driver.close()

neo4j_client = Neo4jClient()
