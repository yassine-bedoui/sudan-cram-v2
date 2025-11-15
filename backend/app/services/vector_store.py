# backend/app/services/vector_store.py

import os
from typing import List, Dict
from uuid import uuid4

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    PayloadSchemaType,
)
from sentence_transformers import SentenceTransformer

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
        # ⬇️ trust_remote_code=True is required for Alibaba-NLP/gte-multilingual-base
        self.encoder = SentenceTransformer(
            "Alibaba-NLP/gte-multilingual-base",
            trust_remote_code=True,
        )
        print("✅ Embedding model loaded")

        self._init_collection()
        self._ensure_region_index()

    def _init_collection(self):
        """Initialize Qdrant collection"""
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

    def _ensure_region_index(self):
        """Make sure 'region' is indexed for filtering"""
        try:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="region",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            print("✅ Created payload index for 'region'")
        except Exception as e:
            # Qdrant will complain if index already exists – that's fine
            msg = str(e)
            if "already exists" in msg or "index with name" in msg:
                print("ℹ️ Payload index for 'region' already exists")
            else:
                print(f"❌ Error creating 'region' index: {e}")

    def add_event(self, event_id: str, text: str, metadata: Dict) -> bool:
        """
        Add event to vector store.

        Qdrant requires point IDs to be:
        - an unsigned integer, or
        - a valid UUID

        We generate a UUID for the internal point ID, and store the logical
        ID (e.g. 'gdelt-138') inside the payload as `event_id`.
        """
        try:
            embedding = self.encoder.encode(text).tolist()
            qdrant_id = str(uuid4())  # ✅ valid UUID for Qdrant

            payload = {
                "event_id": event_id,  # your logical ID
                **metadata,
            }

            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=qdrant_id,
                        vector=embedding,
                        payload=payload,
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
        """Search for relevant events"""
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
        """Get total events in collection"""
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count
        except Exception:
            return 0
