from persona_studio.style_model import StyleModel

def test_style_model_initialization():
    model = StyleModel()
    assert model.presets == ["cinematic", "anime", "commercial"]
    assert model.style_vector is None

def test_style_model_encodes_preset_and_tokens():
    model = StyleModel()
    profile = model.encode_style("anime style with blue hair")
    
    assert profile["preset"] == "anime"
    assert "anime" in profile["tokens"]
    assert "blue" in profile["tokens"]

def test_style_model_resolves_lora():
    model = StyleModel()
    # Implicit resolve through cinematic preset
    profile = model.encode_style("cinematic lighting")
    assert profile["lora"]["id"] == "portrait-consistency"
    
    # Explicit resolve
    lora = model.resolve_lora(style_input={"lora_id": "soft-daylight-pro", "lora_weight": 0.85})
    assert lora["id"] == "soft-daylight-pro"
    assert lora["weight"] == 0.85

def test_style_model_available_loras():
    loras = StyleModel.available_loras()
    assert len(loras) >= 10
    assert any(l["id"] == "brand-campaign" for l in loras)
    assert any(l["id"] == "campaign-poster" for l in loras)
    assert any(l["id"] == "editorial-illustration" for l in loras)
    assert any(l["id"] == "render-3d-polish" for l in loras)


def test_style_model_resolves_poster_lora_from_chinese_prompt():
    model = StyleModel()
    profile = model.encode_style("商业海报，中心产品主视觉，金色高光")
    assert profile["preset"] == "commercial"
    assert profile["lora"]["id"] == "campaign-poster"
    assert profile["camera_language"] == "centered poster hero composition"


def test_style_model_resolves_style_specific_loras():
    model = StyleModel()
    illustration = model.resolve_lora(style_input={"lora_id": "editorial-illustration", "lora_weight": 0.6})
    render = model.resolve_lora(style_input={"lora_id": "render-3d-polish", "lora_weight": 0.56})
    guofeng = model.resolve_lora(style_input={"lora_id": "guofeng-palette", "lora_weight": 0.6})

    assert illustration["label"] == "插画质感"
    assert render["label"] == "3D 材质"
    assert guofeng["label"] == "国风色彩"
