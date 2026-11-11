import hashlib
import math
from typing import Any, Dict, List


class FusionEngine:
    def __init__(
        self,
        identity_weight=0.7,
        style_weight=0.6,
        prompt_weight=1.0,
        state_weight=0.4,
        embedding_dim=512,
        enforce_identity_priority=True,
    ):
        self.identity_weight = identity_weight
        self.style_weight = style_weight
        self.prompt_weight = prompt_weight
        self.state_weight = state_weight
        self.embedding_dim = embedding_dim
        self.enforce_identity_priority = enforce_identity_priority

    def fuse(self, identity_vector, style_vector, prompt, state) -> Dict[str, Any]:
        """
        weighted conditioning -> diffusion sampling
        """
        # Identity priority is mandatory only when face identity is part of conditioning.
        if self.enforce_identity_priority and self.identity_weight <= self.style_weight:
            # According to architecture: "Identity 权重必须高于 style，否则会漂脸"
            raise ValueError("Identity weight must be higher than style weight to prevent face drift.")

        identity = self._coerce_vector(identity_vector, self.embedding_dim)
        style = self._coerce_vector(style_vector, self.embedding_dim)
        prompt_vector = self._text_vector(prompt, self.embedding_dim)
        state_vector = self._text_vector(state, self.embedding_dim)

        weighted = [
            identity[index] * self.identity_weight
            + style[index] * self.style_weight
            + prompt_vector[index] * self.prompt_weight
            + state_vector[index] * self.state_weight
            for index in range(self.embedding_dim)
        ]

        conditioning_vector = self._normalize(weighted)
        return {
            "conditioning_vector": conditioning_vector,
            "weights": {
                "identity": self.identity_weight,
                "style": self.style_weight,
                "prompt": self.prompt_weight,
                "state": self.state_weight,
            },
            "identity_priority": self.identity_weight > self.style_weight,
            "drift_risk": self._drift_risk(),
            "prompt": prompt,
            "state": state,
            "controlnet": {
                "face_lock": self.identity_weight,
                "pose_lock": self.state_weight,
                "style_guidance": self.style_weight,
            },
        }

    def _drift_risk(self) -> str:
        margin = self.identity_weight - self.style_weight
        if margin >= 0.2:
            return "low"
        if margin >= 0.08:
            return "medium"
        return "high"

    def _coerce_vector(self, value: Any, dimensions: int) -> List[float]:
        if value is None:
            return [0.0] * dimensions
        if isinstance(value, dict):
            for key in ("vector", "latent_identity_vector", "style_vector", "conditioning_vector"):
                if key in value:
                    return self._fit_dimensions(list(value[key]), dimensions)
            return self._text_vector(value, dimensions)
        if isinstance(value, (list, tuple)):
            return self._fit_dimensions([float(item) for item in value], dimensions)
        return self._text_vector(value, dimensions)

    def _fit_dimensions(self, vector: List[float], dimensions: int) -> List[float]:
        if not vector:
            return [0.0] * dimensions
        if len(vector) < dimensions:
            repeats = (dimensions + len(vector) - 1) // len(vector)
            vector = (vector * repeats)[:dimensions]
        elif len(vector) > dimensions:
            vector = vector[:dimensions]
        return self._normalize(vector)

    def _text_vector(self, value: Any, dimensions: int) -> List[float]:
        seed = repr(value).encode("utf-8")
        values = []
        counter = 0
        while len(values) < dimensions:
            digest = hashlib.blake2b(seed + counter.to_bytes(4, "big"), digest_size=64).digest()
            values.extend((byte / 127.5) - 1.0 for byte in digest)
            counter += 1
        return self._normalize(values[:dimensions])

    def _normalize(self, vector: List[float]) -> List[float]:
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return [0.0 for _ in vector]
        return [value / magnitude for value in vector]
