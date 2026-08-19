"""Small hybrid-memory POC for the optional Day 19 challenge.

The class is deliberately usable without an LLM or a running Feast server.
A Feast FeatureStore can be passed in later; the in-memory profile/activity
adapter keeps the demo deterministic and makes the memory boundary visible.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from qdrant_client import QdrantClient, models

from app.embeddings import Embedder

COLLECTION = "bonus_hybrid_memory"


@dataclass
class Profile:
    preferred_language: str = "vi"
    reading_speed_wpm: int = 220
    topic_affinity: str = "cloud"
    queries_last_hour: list[str] = field(default_factory=list)


class HybridMemoryAgent:
    """Combine user-scoped episodic vectors with stable profile features."""

    def __init__(self, feature_store: Any | None = None) -> None:
        self.embedder = Embedder()
        self.client = QdrantClient(":memory:")
        self.feature_store = feature_store
        self.profiles: dict[str, Profile] = {}
        self._next_id = 0
        self.client.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=self.embedder.dim, distance=models.Distance.COSINE
            ),
        )

    @staticmethod
    def _chunks(text: str, max_chars: int = 420) -> list[str]:
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
        chunks: list[str] = []
        current = ""
        for sentence in sentences or [text.strip()]:
            if current and len(current) + len(sentence) + 1 > max_chars:
                chunks.append(current)
                current = ""
            current = f"{current} {sentence}".strip()
        if current:
            chunks.append(current)
        return chunks

    def _profile(self, user_id: str) -> Profile:
        return self.profiles.setdefault(user_id, Profile())

    def remember(self, text: str, user_id: str = "u_001") -> None:
        """Chunk and store one user's episodic memory with tenant isolation."""
        if not text.strip():
            raise ValueError("text must not be empty")
        chunks = self._chunks(text)
        vectors = list(self.embedder.embed(chunks))
        points = []
        for chunk, vector in zip(chunks, vectors):
            points.append(models.PointStruct(
                id=self._next_id,
                vector=vector.tolist(),
                payload={"user_id": user_id, "text": chunk, "memory_id": str(uuid.uuid4())},
            ))
            self._next_id += 1
        self.client.upsert(collection_name=COLLECTION, points=points)

    def _profile_values(self, user_id: str) -> dict[str, Any]:
        profile = self._profile(user_id)
        values: dict[str, Any] = {
            "preferred_language": profile.preferred_language,
            "reading_speed_wpm": profile.reading_speed_wpm,
            "topic_affinity": profile.topic_affinity,
            "queries_last_hour": profile.queries_last_hour[-5:],
        }
        if self.feature_store is None:
            return values
        try:
            result = self.feature_store.get_online_features(
                features=[
                    "user_profile_features:preferred_language",
                    "user_profile_features:reading_speed_wpm",
                    "user_profile_features:topic_affinity",
                    "query_velocity_features:queries_last_hour",
                ],
                entity_rows=[{"user_id": user_id}],
            ).to_dict()
            for key, raw in result.items():
                if raw and raw[0] is not None:
                    values[key] = raw[0]
        except Exception:
            # The POC remains useful before Feast apply/materialize.
            pass
        return values

    def recall(self, query: str, user_id: str = "u_001") -> str:
        """Return profile/activity context plus user-scoped hybrid memories."""
        if not query.strip():
            raise ValueError("query must not be empty")
        profile = self._profile(user_id)
        profile.queries_last_hour.append(query)
        query_vector = next(self.embedder.embed([query])).tolist()
        user_filter = models.Filter(must=[models.FieldCondition(
            key="user_id", match=models.MatchValue(value=user_id)
        )])
        semantic = self.client.query_points(
            collection_name=COLLECTION, query=query_vector, query_filter=user_filter, limit=8
        ).points
        lexical = []
        query_terms = set(query.lower().split())
        points, _ = self.client.scroll(
            collection_name=COLLECTION, scroll_filter=user_filter, limit=100, with_payload=True
        )
        for point in points:
            terms = set(point.payload["text"].lower().split())
            lexical.append((len(query_terms & terms), point))
        lexical.sort(key=lambda item: -item[0])
        ranked: dict[int, float] = {}
        payloads: dict[int, dict] = {}
        for rank, point in enumerate(semantic, 1):
            ranked[point.id] = ranked.get(point.id, 0.0) + 1 / (60 + rank)
            payloads[point.id] = point.payload
        for rank, (_, point) in enumerate(lexical[:8], 1):
            ranked[point.id] = ranked.get(point.id, 0.0) + 1 / (60 + rank)
            payloads[point.id] = point.payload
        memories = [payloads[point_id]["text"] for point_id, _ in
                    sorted(ranked.items(), key=lambda item: -item[1])[:3]]
        values = self._profile_values(user_id)
        recent = values.get("queries_last_hour", [])
        return (
            f"User profile: language={values.get('preferred_language')}, "
            f"speed={values.get('reading_speed_wpm')}wpm, "
            f"topic_affinity={values.get('topic_affinity')}.\n"
            f"Recent activity: {recent or '(none)'}.\n"
            f"Top memories for {user_id}: {memories or ['(none)']}"
        )
