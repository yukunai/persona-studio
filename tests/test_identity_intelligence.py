from persona_studio.identity_model import IdentityModel

def test_identity_determinism():
    model1 = IdentityModel()
    model2 = IdentityModel()
    
    # Same images should yield same vector and constraints
    images = ["img1", "img2", "img3"]
    bundle1 = model1.encode_faces(images)
    bundle2 = model2.encode_faces(images)
    
    assert bundle1["vector"] == bundle2["vector"]
    assert bundle1["constraints"] == bundle2["constraints"]

def test_identity_variation():
    model = IdentityModel()
    
    # Different images should yield different vectors
    bundle1 = model.encode_faces(["img1", "img2", "img3"])
    bundle2 = model.encode_faces(["img4", "img5", "img6"])
    
    assert bundle1["vector"] != bundle2["vector"]
    assert bundle1["constraints"] != bundle2["constraints"]

def test_consistency_report_determinism():
    model = IdentityModel()
    model.encode_faces(["face1", "face2", "face3"])
    
    # Same payload with salt "generated" should be deterministic
    report1 = model.consistency_report("face1")
    report2 = model.consistency_report("face1")
    assert report1["score"] == report2["score"]
    
    # But it is different from the reference vectors because they use numeric salts
    # Cosine similarity of random 512-d vectors is near 0
    assert abs(report1["score"]) < 0.2
