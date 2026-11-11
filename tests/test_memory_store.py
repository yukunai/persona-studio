from persona_studio.memory_store import MemoryStore

def test_memory_store_add_entry():
    store = MemoryStore()
    store.add_entry("walking", "img1.png", "standing", 0.9)
    assert len(store.logs) == 1
    assert store.logs[0]["success_score"] == 0.9

def test_memory_store_initialization():
    store = MemoryStore()
    assert store.logs == []

def test_memory_store_recommends_best_angles():
    store = MemoryStore()
    store.add_entry("studio headshot", "img1.png", "front", 0.8, character_id="lina", style="commercial")
    store.add_entry("rainy street", "img2.png", "three-quarter", 0.93, character_id="lina", style="cinematic")
    store.add_entry("bad backlight", "img3.png", "side", 0.2, character_id="lina", style="harsh-neon")

    angles = store.get_best_angles("lina")
    failures = store.avoid_failure_styles()

    assert angles[0]["pose"] == "three-quarter"
    assert "harsh-neon" in failures["blocked_styles"]

def test_memory_store_character_preferences():
    store = MemoryStore()
    store.add_entry("coffee shop", "img1.png", "front", 0.9, character_id="lina", style="soft daylight")
    store.add_entry("studio", "img2.png", "front", 0.8, character_id="lina", style="soft daylight")

    preferences = store.character_preferences("lina")

    assert preferences["average_success_score"] == 0.85
    assert preferences["preferred_styles"][0]["style"] == "soft daylight"
