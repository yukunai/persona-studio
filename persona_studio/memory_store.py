from collections import defaultdict
from typing import Any, Dict, List, Optional


class MemoryStore:
    def __init__(self):
        self.logs = []  # List of scene logs: prompt, image, pose, style, score.

    def add_entry(
        self,
        prompt: str,
        image: Any,
        pose: str,
        success_score: float,
        character_id: Optional[str] = None,
        style: Optional[str] = None,
        state: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        metadata = metadata or {}
        score = max(0.0, min(1.0, float(success_score)))
        entry = {
            "id": metadata.get("memory_id"),
            "character_id": character_id,
            "prompt": prompt,
            "image": image,
            "pose": pose,
            "style": style,
            "state": state,
            "success_score": score,
            "created_at": metadata.get("created_at"),
            "metadata": metadata,
        }
        if entry["id"] is None:
            entry.pop("id")
        if entry["created_at"] is None:
            entry.pop("created_at")
        self.logs.append(entry)
        return entry

    def get_best_angles(self, character_id: Optional[str] = None, minimum_score: float = 0.72, limit: int = 3) -> List[Dict[str, Any]]:
        """
        自动推荐“她最好看的角度”.
        """
        pose_scores = defaultdict(list)
        for entry in self._entries_for_character(character_id):
            if entry["success_score"] >= minimum_score and entry["pose"]:
                pose_scores[entry["pose"]].append(entry)

        ranked = []
        for pose, entries in pose_scores.items():
            average_score = sum(entry["success_score"] for entry in entries) / len(entries)
            best_entry = max(entries, key=lambda item: item["success_score"])
            ranked.append(
                {
                    "pose": pose,
                    "average_score": round(average_score, 3),
                    "uses": len(entries),
                    "example_prompt": best_entry["prompt"],
                    "example_image": best_entry["image"],
                }
            )
        return sorted(ranked, key=lambda item: (item["average_score"], item["uses"]), reverse=True)[:limit]

    def avoid_failure_styles(
        self,
        current_style: Optional[str] = None,
        threshold: float = 0.45,
        character_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        自动避免“失败风格”.

        When ``character_id`` is provided, only that character's scene logs are
        considered so one character's failures never poison another's advice.
        """
        failures = [
            entry
            for entry in self._entries_for_character(character_id)
            if (
                (
                    entry["success_score"] <= threshold
                    or (entry.get("metadata", {}).get("quality") or {}).get("status") == "fail"
                )
                and (current_style is None or entry.get("style") == current_style)
            )
        ]
        blocked_styles = sorted({entry["style"] for entry in failures if entry.get("style")})
        failed_prompts = [entry["prompt"] for entry in failures[:5]]
        return {
            "blocked_styles": blocked_styles,
            "failed_prompts": failed_prompts,
            "reason": "No repeated low-score styles found." if not failures else "Low-scoring scene memory matched this style.",
        }

    def character_preferences(self, character_id: Optional[str] = None) -> Dict[str, Any]:
        entries = list(self._entries_for_character(character_id))
        if not entries:
            return {"best_angles": [], "preferred_styles": [], "average_success_score": 0.0}

        style_scores = defaultdict(list)
        for entry in entries:
            if entry.get("style"):
                style_scores[entry["style"]].append(entry["success_score"])

        preferred_styles = sorted(
            (
                {"style": style, "average_score": round(sum(scores) / len(scores), 3), "uses": len(scores)}
                for style, scores in style_scores.items()
            ),
            key=lambda item: (item["average_score"], item["uses"]),
            reverse=True,
        )
        average_score = sum(entry["success_score"] for entry in entries) / len(entries)
        return {
            "best_angles": self.get_best_angles(character_id),
            "preferred_styles": preferred_styles[:3],
            "average_success_score": round(average_score, 3),
        }

    def _entries_for_character(self, character_id: Optional[str]):
        for entry in self.logs:
            if character_id is None or entry.get("character_id") == character_id:
                yield entry
