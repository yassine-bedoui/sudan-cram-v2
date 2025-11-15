from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from typing import List, Dict
import os
import uuid


load_dotenv()


class VectorStore:
    def __init__(self):
        print("🔧 Initializing Vector Store...")

        # Connect to Qdrant Cloud
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=60,
        )

        self.collection_name = "sudan_events"

        # Load multilingual embedding model
        print("📦 Loading embedding model...")
        self.encoder = SentenceTransformer(
            "Alibaba-NLP/gte-multilingual-base",
            trust_remote_code=True,
        )
        print("✅ Embedding model loaded")

        self._init_collection()

    def _init_collection(self):
        """Initialize Qdrant collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=768,
                        distance=Distance.COSINE,
                    ),
                )
                print(f"✅ Created collection: {self.collection_name}")
            else:
                print(f"✅ Collection exists: {self.collection_name}")

        except Exception as e:
            print(f"❌ Error initializing collection: {e}")
            raise

    def add_event(self, event_id: str, text: str, metadata: Dict) -> bool:
        """
        Add an event to the vector store.

        - event_id: your logical ID, e.g. 'gdelt-123', 'acled-456'
        - We convert it to a UUID for Qdrant's point ID requirement,
          and keep the original event_id in the payload.
        """
        try:
            embedding = self.encoder.encode(text).tolist()

            # Qdrant IDs must be uint or UUID. Use a deterministic UUID5
            # so the same event_id always maps to the same point ID.
            point_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(event_id))

            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=str(point_id),
                        vector=embedding,
                        payload={**metadata, "event_id": event_id},
                    )
                ],
            )
            return True
        except Exception as e:
            print(f"❌ Error adding {event_id}: {e}")
            return False

    def semantic_search(
        self,
        query: str,
        filters: Dict | None = None,
        top_k: int = 10,
    ) -> List[Dict]:
        """Search for relevant events using semantic similarity."""
        try:
            query_embedding = self.encoder.encode(query).tolist()

            qdrant_filter = None
            if filters:
                conditions = [
                    {"key": k, "match": {"value": v}} for k, v in filters.items()
                ]
                qdrant_filter = {"must": conditions} if conditions else None

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True,
            )

            return [
                {
                    "id": r.id,
                    "score": r.score,
                    "metadata": r.payload,
                }
                for r in results
            ]

        except Exception as e:
            print(f"❌ Search error: {e}")
            return []

    def get_event_count(self) -> int:
        """Get total number of points stored in the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count
        except Exception as e:
            print(f"❌ Error getting event count: {e}")
            return 0
