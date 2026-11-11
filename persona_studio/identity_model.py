import hashlib
import math
import os
from typing import Any, Dict, Iterable, List


class IdentityModel:
    """Deterministic identity encoder used by the product prototype.

    Real deployments can replace ``_vector_from_payload`` with ArcFace,
    InsightFace, or a custom ViT encoder. The public contract stays the same:
    3-20 reference faces become one normalized identity vector plus a feature
    bundle that the fusion engine can weight above style conditioning.
    """

    def __init__(self, embedding_dim: int = 512, min_faces: int = 3, max_faces: int = 20):
        self.embedding_dim = embedding_dim
        self.min_faces = min_faces
        self.max_faces = max_faces
        self.latent_identity_vector = None
        self.constraints = {
            "eye_distance": None,
            "jaw_shape": None,
            "nose_bridge": None,
            "age_distribution": None,
        }
        self.feature_bundle = None

    def encode_faces(self, face_images: Iterable[Any]) -> Dict[str, Any]:
        """
        Input: 3-20 face references.
        Process: Face Encoder (ArcFace / InsightFace compatible contract).
        Output: latent identity vector + face structure constraints.
        """
        images = list(face_images or [])
        if not self.min_faces <= len(images) <= self.max_faces:
            raise ValueError(f"IdentityModel requires {self.min_faces}-{self.max_faces} face images.")

        reference_vectors = [
            self._vector_from_payload(self._payload_bytes(image, index), self.embedding_dim)
            for index, image in enumerate(images)
        ]
        identity_vector = self._normalize(self._mean_vector(reference_vectors))
        constraints = self._derive_constraints(identity_vector, reference_vectors)

        self.latent_identity_vector = identity_vector
        self.constraints = constraints
        self.feature_bundle = {
            "vector": identity_vector,
            "constraints": constraints,
            "reference_count": len(images),
            "embedding_dim": self.embedding_dim,
            "encoder": "deterministic-prototype",
        }
        return self.feature_bundle

    def verify_consistency(self, generated_image: Any, threshold: float = 0.72) -> bool:
        """Return whether a generated image still matches the locked identity."""
        if self.latent_identity_vector is None:
            return False
        return self.consistency_report(generated_image, threshold)["match"]

    def consistency_report(self, generated_image: Any, threshold: float = 0.72) -> Dict[str, Any]:
        if self.latent_identity_vector is None:
            raise ValueError("encode_faces must be called before consistency_report.")

        generated_vector = self._vector_from_payload(
            self._payload_bytes(generated_image, "generated"),
            self.embedding_dim,
        )
        score = self._cosine_similarity(self.latent_identity_vector, generated_vector)
        return {
            "score": round(score, 4),
            "threshold": threshold,
            "match": score >= threshold,
            "constraints": self.constraints,
        }

    def _payload_bytes(self, payload: Any, salt: Any) -> bytes:
        if isinstance(payload, bytes):
            raw = payload
        elif isinstance(payload, str) and os.path.isfile(payload):
            with open(payload, "rb") as file:
                raw = file.read()
        else:
            raw = repr(payload).encode("utf-8")
        return repr(salt).encode("utf-8") + b":" + raw

    def _derive_constraints(self, identity_vector: List[float], references: List[List[float]]) -> Dict[str, Any]:
        jaw_shapes = ["oval", "soft_square", "heart", "angular"]
        eye_distance = 0.42 + self._unit_interval(identity_vector[0]) * 0.24
        nose_bridge = 0.32 + self._unit_interval(identity_vector[3]) * 0.52
        stability = 1.0 - min(1.0, self._average_vector_distance(references) / 1.4)

        young = self._unit_interval(identity_vector[7])
        adult = self._unit_interval(identity_vector[11])
        mature = self._unit_interval(identity_vector[17])
        total = young + adult + mature or 1.0

        return {
            "eye_distance": round(eye_distance, 3),
            "jaw_shape": jaw_shapes[int(self._unit_interval(identity_vector[1]) * len(jaw_shapes)) % len(jaw_shapes)],
            "nose_bridge": round(nose_bridge, 3),
            "age_distribution": {
                "young_adult": round(young / total, 3),
                "adult": round(adult / total, 3),
                "mature": round(mature / total, 3),
            },
            "reference_stability": round(stability, 3),
        }

    def _average_vector_distance(self, vectors: List[List[float]]) -> float:
        if len(vectors) < 2:
            return 0.0
        centroid = self._normalize(self._mean_vector(vectors))
        distances = [1.0 - self._cosine_similarity(centroid, vector) for vector in vectors]
        return sum(distances) / len(distances)

    def _vector_from_payload(self, payload: bytes, dimensions: int) -> List[float]:
        values = []
        counter = 0
        while len(values) < dimensions:
            digest = hashlib.blake2b(
                payload + counter.to_bytes(4, "big"),
                digest_size=64,
            ).digest()
            values.extend((byte / 127.5) - 1.0 for byte in digest)
            counter += 1
        return self._normalize(values[:dimensions])

    def _mean_vector(self, vectors: List[List[float]]) -> List[float]:
        return [sum(vector[index] for vector in vectors) / len(vectors) for index in range(len(vectors[0]))]

    def _normalize(self, vector: List[float]) -> List[float]:
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return [0.0 for _ in vector]
        return [value / magnitude for value in vector]

    def _cosine_similarity(self, left: List[float], right: List[float]) -> float:
        return sum(a * b for a, b in zip(left, right))

    def _unit_interval(self, value: float) -> float:
        return max(0.0, min(1.0, (value + 1.0) / 2.0))
