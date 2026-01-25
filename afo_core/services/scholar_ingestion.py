# Trinity Score: 90.0 (Established by Chancellor)
import glob
import os

# Try to import Qdrant/Neo4j via HybridRAG (or directly if not exposed)
# We will use the hybrid_rag service functions where possible
try:
    from neo4j import GraphDatabase

    # We need UPSERT methods which might not be in hybrid_rag yet.
    # So we will implement direct clients here for ingestion,
    # and later refactor common logic if needed.
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as models

    _HAS_DEPS = True
except ImportError:
    print("Warning: Missing dependencies for ingestion.")
    QdrantClient = None  # type: ignore[assignment, misc]
    GraphDatabase = None  # type: ignore[assignment, misc]
    _HAS_DEPS = False


class ScholarIngestionService:
    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self.qdrant_client = QdrantClient("localhost", port=6333) if _HAS_DEPS else None
        # 보안: 환경변수에서 패스워드 로드 (하드코딩 제거)
        neo4j_password = os.getenv("NEO4J_PASSWORD", "")
        self.neo4j_driver = (
            GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", neo4j_password))
            if _HAS_DEPS and neo4j_password
            else None
        )

        # Collection settings
        self.collection_name = "afokingdom_knowledge"

        if not self.dry_run and self.qdrant_client:
            self._init_qdrant()

    def _init_qdrant(self) -> None:
        # Create collection if not exists
        try:
            self.qdrant_client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
            )
            print(f"✅ Qdrant collection '{self.collection_name}' ready.")
        except Exception as e:
            print(f"⚠️ Qdrant init failed: {e}")

    def ingest_directory(self, path: str) -> None:
        print(f"🔍 Scanning {path}...")
        files = glob.glob(os.path.join(path, "*.md"))
        print(f"📚 Found {len(files)} markdown files in {path}.")

        for file_path in files:
            self.process_file(file_path)

    def process_file(self, file_path: str) -> None:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return

        filename = os.path.basename(file_path)
        chunks = self._chunk_text(content)

        print(f"📄 Processing {filename}: {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            # In a real scenario, we'd use OpenAI to get embedding.
            # For this MVP/DryRun, we use random or mock if API key missing.
            embedding = self._get_embedding(chunk)

            if self.dry_run:
                print(f"  [DRY RUN] Would upsert chunk {i} to Qdrant & Neo4j")
                # Entity extraction simulation
                entities = self._extract_entities(chunk)
                if entities:
                    print(f"  [DRY RUN] Extracted Entities: {entities}")
            else:
                self._upsert_qdrant(filename, i, chunk, embedding)
                self._upsert_neo4j(filename, i, chunk, self._extract_entities(chunk))

    def _chunk_text(self, text: str) -> list[str]:
        # Simple paragraph splitter for MVP
        return [p for p in text.split("\n\n") if len(p.strip()) > 50]

    def _get_embedding(self, text: str) -> list[float]:
        # Use services.hybrid_rag.get_embedding if available, else random
        from AFO.services.hybrid_rag import get_embedding

        # Mock client for now or real
        return get_embedding(text, None)

    def _extract_entities(self, text: str) -> list[str]:
        # Rule-based simple extraction for MVP
        # Identify Capitalized phrases or specific keywords
        keywords = [
            "眞",
            "善",
            "美",
            "孝",
            "永",
            "Chancellor",
            "Commander",
            "Qdrant",
            "PostgreSQL",
            "Neo4j",
        ]
        found = [k for k in keywords if k in text]
        return list(set(found))

    def _upsert_qdrant(self, filename: str, chunk_id: int, text: str, vector: list[float]) -> None:
        if not self.qdrant_client:
            return
        point_id = f"{filename}_{chunk_id}"
        # Hashing ID to UUID/Int is better but string ID supported in some versions?
        # Qdrant prefers UUID or Int. We'll use UUID generator from string.
        import uuid

        uid = str(uuid.uuid5(uuid.NAMESPACE_DNS, point_id))

        try:
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=uid,
                        vector=vector,
                        payload={"source": filename, "content": text},
                    )
                ],
            )
        except Exception as e:
            print(f"Error upserting Qdrant: {e}")

    def _upsert_neo4j(self, filename: str, chunk_id: int, text: str, entities: list[str]) -> None:
        if not self.neo4j_driver:
            return
        try:
            with self.neo4j_driver.session() as session:
                for entity in entities:
                    session.run(
                        """
                        MERGE (e:Entity {name: $entity})
                        MERGE (d:Document {name: $filename})
                        MERGE (d)-[:MENTIONS]->(e)
                        """,
                        entity=entity,
                        filename=filename,
                    )
        except Exception as e:
            print(f"Error upserting Neo4j: {e}")


if __name__ == "__main__":
    import sys

    dry = "--dry-run" in sys.argv
    service = ScholarIngestionService(dry_run=dry)
    # Ingest paths
    service.ingest_directory("docs")
    service.ingest_directory(".")
