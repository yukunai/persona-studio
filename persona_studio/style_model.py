import hashlib
import math
from typing import Any, Dict, Iterable, List


class StyleModel:
    DEFAULT_LORAS = [
        {
            "id": "portrait-consistency",
            "name": "Portrait Consistency LoRA",
            "label": "人像一致性",
            "preset": "cinematic",
            "rank": 16,
            "default_weight": 0.72,
            "trigger_tokens": ["identity-lock", "face-structure", "skin-tone-safe"],
            "description": "Keeps face structure stable across realistic portrait scenes.",
        },
        {
            "id": "soft-daylight-pro",
            "name": "Soft Daylight Pro LoRA",
            "label": "柔和日光",
            "preset": "cinematic",
            "rank": 8,
            "default_weight": 0.58,
            "trigger_tokens": ["soft-daylight", "natural-bokeh", "warm-skin"],
            "description": "Adds natural outdoor daylight, shallow depth of field, and skin-safe color.",
        },
        {
            "id": "anime-clean-line",
            "name": "Anime Clean Line LoRA",
            "label": "动漫线稿",
            "preset": "anime",
            "rank": 12,
            "default_weight": 0.64,
            "trigger_tokens": ["clean-line", "anime-face", "soft-glow"],
            "description": "Controls clean anime character rendering without losing the identity anchor.",
        },
        {
            "id": "brand-campaign",
            "name": "Brand Campaign LoRA",
            "label": "商业广告",
            "preset": "commercial",
            "rank": 16,
            "default_weight": 0.62,
            "trigger_tokens": ["campaign-light", "product-ready", "studio-polish", "glass-reflection"],
            "description": "Adds commercial product lighting, golden highlights, and campaign-ready polish.",
        },
        {
            "id": "campaign-poster",
            "name": "Campaign Poster LoRA",
            "label": "商业海报",
            "preset": "commercial",
            "rank": 16,
            "default_weight": 0.64,
            "trigger_tokens": ["hero-packshot", "poster-layout", "golden-campaign"],
            "description": "Adds poster hero composition, centered product layout, and premium reflective finish.",
        },
        {
            "id": "editorial-illustration",
            "name": "Editorial Illustration LoRA",
            "label": "插画质感",
            "preset": "cinematic",
            "rank": 12,
            "default_weight": 0.6,
            "trigger_tokens": ["brush-texture", "paper-grain", "editorial-color"],
            "description": "Adds painterly texture, paper grain, and editorial poster color.",
        },
        {
            "id": "render-3d-polish",
            "name": "3D Render Polish LoRA",
            "label": "3D 材质",
            "preset": "cinematic",
            "rank": 12,
            "default_weight": 0.56,
            "trigger_tokens": ["subsurface", "material-polish", "studio-render"],
            "description": "Adds 3D material polish, controlled studio lighting, and render depth.",
        },
        {
            "id": "drama-still",
            "name": "Drama Still LoRA",
            "label": "剧照光影",
            "preset": "cinematic",
            "rank": 12,
            "default_weight": 0.62,
            "trigger_tokens": ["moody-practical", "cinematic-still", "contrast-grade"],
            "description": "Adds cinematic still lighting, low-key contrast, and practical color separation.",
        },
        {
            "id": "guofeng-palette",
            "name": "Guofeng Palette LoRA",
            "label": "国风色彩",
            "preset": "cinematic",
            "rank": 10,
            "default_weight": 0.6,
            "trigger_tokens": ["ink-wash", "oriental-palette", "silk-texture"],
            "description": "Adds restrained Chinese palette, silk texture, and ink-wash composition.",
        },
        {
            "id": "healing-daylight",
            "name": "Healing Daylight LoRA",
            "label": "治愈柔光",
            "preset": "cinematic",
            "rank": 8,
            "default_weight": 0.54,
            "trigger_tokens": ["gentle-daylight", "pastel-air", "soft-life"],
            "description": "Adds soft healing daylight, pastel air, and warm lifestyle calm.",
        },
    ]

    def __init__(self, embedding_dim: int = 256):
        self.embedding_dim = embedding_dim
        self.style_vector = None
        self.presets = ["cinematic", "anime", "commercial"]
        self.lora_registry = {lora["id"]: lora for lora in self.DEFAULT_LORAS}
        self.style_profile = None

    def encode_style(self, style_input: Any) -> Dict[str, Any]:
        """
        Input: style image, prompt, or preset.
        Process: CLIP embedding / LoRA / style token compatible contract.
        Output: style vector and controllable visual language.
        """
        normalized_input = self._normalize_input(style_input)
        preset = self._resolve_preset(normalized_input)
        lora_profile = self.resolve_lora(style_input, preset=preset, text=normalized_input)
        preset = self._align_preset_with_lora(preset, lora_profile)
        tokens = self._extract_tokens(normalized_input, preset, lora_profile)
        vector = self._vector_from_text("|".join(tokens + [lora_profile["id"], str(lora_profile["weight"])]), self.embedding_dim)

        self.style_vector = vector
        self.style_profile = {
            "vector": vector,
            "preset": preset,
            "tokens": tokens,
            "lora": lora_profile,
            "photography": self._photography_controls(tokens, preset),
            "lighting": self._lighting_controls(tokens, preset),
            "color": self._color_controls(tokens, preset),
            "camera_language": self._camera_controls(tokens, preset),
        }
        return self.style_profile

    @classmethod
    def available_loras(cls) -> List[Dict[str, Any]]:
        return [dict(lora) for lora in cls.DEFAULT_LORAS]

    def resolve_lora(self, style_input: Any = None, preset: str = "cinematic", text: str = "") -> Dict[str, Any]:
        requested_id = self._extract_lora_id(style_input, text)
        if requested_id not in self.lora_registry:
            requested_id = self._default_lora_for_preset(preset)
        base = dict(self.lora_registry[requested_id])
        base["weight"] = self._extract_lora_weight(style_input, base["default_weight"])
        base["enabled"] = base["weight"] > 0
        return base

    def _normalize_input(self, style_input: Any) -> str:
        if isinstance(style_input, dict):
            parts = []
            for key in sorted(style_input):
                value = style_input[key]
                if isinstance(value, (list, tuple, set)):
                    parts.extend(str(item) for item in value)
                else:
                    parts.append(str(value))
            return " ".join(parts).strip().lower()
        if isinstance(style_input, (list, tuple, set)):
            return " ".join(str(item) for item in style_input).strip().lower()
        return str(style_input or "").strip().lower()

    def _resolve_preset(self, text: str) -> str:
        for preset in self.presets:
            if preset in text:
                return preset
        if any(token in text for token in ["anime", "manga", "cel", "动漫", "二次元"]):
            return "anime"
        if any(
            token in text
            for token in [
                "ad",
                "brand",
                "product",
                "commercial",
                "poster",
                "campaign",
                "packshot",
                "商业广告",
                "商业海报",
                "广告",
                "海报",
            ]
        ):
            return "commercial"
        return "cinematic"

    def _align_preset_with_lora(self, preset: str, lora_profile: Dict[str, Any]) -> str:
        lora_id = str(lora_profile.get("id") or "").strip()
        lora_preset = (self.lora_registry.get(lora_id) or {}).get("preset")
        return lora_preset or preset

    def _extract_tokens(self, text: str, preset: str, lora_profile: Dict[str, Any]) -> List[str]:
        words = [word.strip(".,;:/[](){}") for word in text.split() if word.strip()]
        tokens = [preset] + words + list(lora_profile.get("trigger_tokens", []))
        return list(dict.fromkeys(tokens))[:32]

    def _extract_lora_id(self, style_input: Any, text: str) -> str:
        if isinstance(style_input, dict):
            requested = style_input.get("lora_id") or style_input.get("lora") or style_input.get("adapter")
            if isinstance(requested, dict):
                requested = requested.get("id")
            if requested:
                return str(requested).strip()
        for lora in self.DEFAULT_LORAS:
            if lora["id"] in text or lora["label"].lower() in text:
                return lora["id"]
        return ""

    def _extract_lora_weight(self, style_input: Any, default: float) -> float:
        value = None
        if isinstance(style_input, dict):
            value = style_input.get("lora_weight")
            if value is None and isinstance(style_input.get("lora"), dict):
                value = style_input["lora"].get("weight")
        try:
            return round(max(0.0, min(1.0, float(default if value is None else value))), 2)
        except (TypeError, ValueError):
            return round(float(default), 2)

    def _default_lora_for_preset(self, preset: str) -> str:
        if preset == "anime":
            return "anime-clean-line"
        if preset == "commercial":
            return "brand-campaign"
        return "portrait-consistency"

    def _photography_controls(self, tokens: Iterable[str], preset: str) -> str:
        token_set = set(tokens)
        if "anime" in token_set:
            return "clean illustrated character render"
        if {"product", "packshot", "product-ready", "hero-packshot", "luxury-product"} & token_set:
            return "polished product campaign packshot"
        if "commercial" in token_set or preset == "commercial":
            return "polished brand campaign portrait"
        return "cinematic portrait photography"

    def _lighting_controls(self, tokens: Iterable[str], preset: str) -> str:
        token_set = set(tokens)
        if {"soft", "daylight"} & token_set:
            return "soft daylight"
        if {"night", "neon", "rainy"} & token_set:
            return "moody night practicals"
        if preset == "commercial":
            return "controlled studio key light"
        return "natural high dynamic range light"

    def _color_controls(self, tokens: Iterable[str], preset: str) -> str:
        token_set = set(tokens)
        if {"warm", "morning", "golden"} & token_set:
            return "warm golden palette"
        if {"golden-light", "golden-campaign"} & token_set:
            return "premium golden product palette"
        if {"rainy", "night", "neon"} & token_set:
            return "cool contrast palette"
        if preset == "anime":
            return "clean saturated palette"
        return "balanced skin-tone-safe palette"

    def _camera_controls(self, tokens: Iterable[str], preset: str) -> str:
        token_set = set(tokens)
        if "50mm" in token_set or "portrait" in token_set:
            return "50mm portrait lens, shallow depth of field"
        if "wide" in token_set:
            return "environmental wide shot"
        if {"poster", "hero-packshot", "product-poster"} & token_set:
            return "centered poster hero composition"
        if preset == "commercial":
            return "campaign-ready medium shot"
        return "portrait medium close-up"

    def _vector_from_text(self, text: str, dimensions: int) -> List[float]:
        values = []
        counter = 0
        seed = text.encode("utf-8")
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
