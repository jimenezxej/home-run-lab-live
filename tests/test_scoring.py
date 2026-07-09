from backend.model.scoring import score_player

def test_score_player_basic():
    h = {"name":"Test Hitter","team":"AAA","order":7,"barrel":12,"hardHit":45,"avgEV":91,"maxEV":112,"pullAir":30,"last7":70,"last14":65,"last30":60,"xslg":.520}
    p = {"name":"Test Pitcher","barrelA":10,"hardHitA":46,"hr9":1.7,"fb":44,"gb":35}
    g = {"temp":88,"wind":12,"windDir":"Out to LF"}
    out = score_player(h,p,g)
    assert out["scores"]["hr_edge"] > 50
    assert out["scores"]["longshot_bonus"] > 0
    assert out["reasons"]
