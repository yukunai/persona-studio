from persona_studio.memory_store import MemoryStore

def test_memory_intelligence_ranking_logic():
    store = MemoryStore()
    
    # Setup multiple entries with same score but different usage
    # Pose 'front' used 3 times with 0.9
    for _ in range(3):
        store.add_entry("front pose", "img.png", "front", 0.9, character_id="lina")
    
    # Pose 'side' used 1 time with 0.95
    store.add_entry("side pose", "img.png", "side", 0.95, character_id="lina")
    
    # Pose 'top' used 5 times with 0.8
    for _ in range(5):
        store.add_entry("top pose", "img.png", "top", 0.8, character_id="lina")
        
    best_angles = store.get_best_angles("lina", limit=5)
    
    # 1. side (0.95)
    # 2. front (0.9)
    # 3. top (0.8)
    assert best_angles[0]["pose"] == "side"
    assert best_angles[1]["pose"] == "front"
    assert best_angles[2]["pose"] == "top"
    assert best_angles[1]["uses"] == 3

def test_memory_intelligence_tied_scores_sort_by_uses():
    store = MemoryStore()
    
    # Two poses with same average score 0.9
    # 'a' has 2 uses
    store.add_entry("a1", "img.png", "a", 0.9, character_id="lina")
    store.add_entry("a2", "img.png", "a", 0.9, character_id="lina")
    
    # 'b' has 5 uses
    for i in range(5):
        store.add_entry(f"b{i}", "img.png", "b", 0.9, character_id="lina")
        
    best = store.get_best_angles("lina")
    
    # Tied score (0.9) should sort by uses
    assert best[0]["pose"] == "b"
    assert best[1]["pose"] == "a"

def test_memory_intelligence_character_isolation():
    store = MemoryStore()
    store.add_entry("lina high", "img.png", "front", 0.99, character_id="lina")
    store.add_entry("kira low", "img.png", "front", 0.1, character_id="kira")
    
    lina_angles = store.get_best_angles("lina")
    kira_angles = store.get_best_angles("kira")
    
    assert lina_angles[0]["average_score"] == 0.99
    assert len(kira_angles) == 0 # below minimum_score 0.72

def test_memory_intelligence_failure_avoidance():
    store = MemoryStore()
    store.add_entry("bad cinematic", "img.png", "front", 0.2, style="cinematic")
    store.add_entry("good anime", "img.png", "front", 0.9, style="anime")
    
    # Test global failure check
    global_failures = store.avoid_failure_styles()
    assert "cinematic" in global_failures["blocked_styles"]
    assert "anime" not in global_failures["blocked_styles"]
    
    # Test specific style check
    cinematic_failures = store.avoid_failure_styles(current_style="cinematic")
    assert "cinematic" in cinematic_failures["blocked_styles"]
    
    anime_failures = store.avoid_failure_styles(current_style="anime")
    assert len(anime_failures["blocked_styles"]) == 0


def test_failure_avoidance_is_scoped_per_character():
    # One character's failures must not poison another character's advice.
    store = MemoryStore()
    store.add_entry("A fails", "img.png", "front", 0.1, character_id="A", style="cinematic")
    store.add_entry("B succeeds", "img.png", "front", 0.95, character_id="B", style="cinematic")

    a_advice = store.avoid_failure_styles("cinematic", character_id="A")
    b_advice = store.avoid_failure_styles("cinematic", character_id="B")
    global_advice = store.avoid_failure_styles("cinematic")

    assert a_advice["blocked_styles"] == ["cinematic"]
    assert b_advice["blocked_styles"] == []  # B never failed; A's failure must not leak
    assert global_advice["blocked_styles"] == ["cinematic"]  # global view still aggregates
