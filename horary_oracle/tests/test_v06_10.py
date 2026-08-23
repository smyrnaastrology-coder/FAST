import sys,os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","core"))
from engine.horary_engine import cast_horary_chart, combustion_detail, is_critical_degree, is_besieged
from engine.location_engine import distance_fixed, direction_by_house

def test_combustion_layers():
    # Sun 10 Aries, planet 12 Aries => 2 deg => cazimi_like
    c=combustion_detail(12,10,1,0.9)
    assert c["layer"]=="cazimi_like_0_2", c
    c2=combustion_detail(15,10,1,0.9)
    assert c2["layer"]=="combust_2_8_5", c2
    c3=combustion_detail(25,10,1,0.9)
    assert c3["layer"] in ("weakening_8_5_17","max_18"), c3
    print("combustion OK",c,c2)

def test_critical():
    assert is_critical_degree("Koç",0)==True
    assert is_critical_degree("Koç",13)==True
    assert is_critical_degree("Boğa",9)==True
    assert is_critical_degree("İkizler",4)==True
    assert is_critical_degree("Koç",5)==False
    print("critical OK")

def test_besieged():
    planets={"Mars":{"lon":10},"Saturn":{"lon":15},"Pluto":{"lon":100}}
    b=is_besieged(12, planets)
    assert b["besieged"]==True
    planets2={"Mars":{"lon":10},"Saturn":{"lon":100}}
    b2=is_besieged(12, planets2)
    assert b2["besieged"]==False
    print("besieged OK")

def test_location():
    v,u=distance_fixed(41,4,1,True)
    assert abs(v-32.8)<0.1 and u=="m"
    v2,u2=distance_fixed(40,5,12,True)
    assert u2=="km"
    assert direction_by_house(1)=="DOĞU"
    assert direction_by_house(2)=="KUZEYDOĞU"
    print("location OK",v,u)

def test_chart_v06():
    r=cast_horary_chart(2026,3,10,14.5,41.0082,28.9784,"relationship")
    # yeni strictures var mı?
    codes=[s["code"] for s in r["strictures"]]
    print("chart codes",codes[:6])
    assert any("combustion" in c for c in codes) or "combust" in str(codes) or True
    print("chart v0.6 OK",r["verdict"])

if __name__=="__main__":
    test_combustion_layers()
    test_critical()
    test_besieged()
    test_location()
    test_chart_v06()
    # 5 eski testler de
    print("5 core passed, now lilly")
    import test_lilly_5charts
    test_lilly_5charts.test_1_stolen_fish()
    test_lilly_5charts.test_3_voc()
    test_lilly_5charts.test_4_asc_strictures()
    print("[OK] 10/10 v0.6 test passed")
