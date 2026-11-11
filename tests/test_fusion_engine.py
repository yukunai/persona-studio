import pytest
from persona_studio.fusion_engine import FusionEngine

def test_fusion_engine_weight_constraint():
    # Valid weights: Identity (0.7) > Style (0.6)
    engine = FusionEngine(identity_weight=0.7, style_weight=0.6)
    # This should not raise an error when calling fuse
    engine.fuse(None, None, "prompt", "calm")

def test_fusion_engine_invalid_weights():
    # Invalid weights: Identity <= Style
    engine = FusionEngine(identity_weight=0.5, style_weight=0.5)
    with pytest.raises(ValueError, match="Identity weight must be higher than style weight"):
        engine.fuse(None, None, "prompt", "calm")

    engine = FusionEngine(identity_weight=0.4, style_weight=0.8)
    with pytest.raises(ValueError, match="Identity weight must be higher than style weight"):
        engine.fuse(None, None, "prompt", "calm")

def test_fusion_engine_can_skip_identity_priority_for_non_character_subjects():
    engine = FusionEngine(identity_weight=0.4, style_weight=0.8, enforce_identity_priority=False)

    packet = engine.fuse(None, None, "product poster prompt", "calm")

    assert packet["identity_priority"] is False
    assert packet["weights"]["identity"] == 0.4
    assert packet["weights"]["style"] == 0.8
    assert packet["drift_risk"] == "high"

def test_default_weights():
    engine = FusionEngine()
    assert engine.identity_weight == 0.7
    assert engine.style_weight == 0.6

def test_fusion_engine_returns_conditioning_packet():
    engine = FusionEngine()

    packet = engine.fuse([1.0, 0.0], [0.0, 1.0], "walking in morning light", "calm")

    assert len(packet["conditioning_vector"]) == 512
    assert packet["weights"]["identity"] > packet["weights"]["style"]
    assert packet["identity_priority"] is True
    assert packet["controlnet"]["face_lock"] == 0.7
