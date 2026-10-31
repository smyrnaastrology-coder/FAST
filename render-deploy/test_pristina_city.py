import pytest

from core.utils import sehir_ara, sehir_bul, sehir_veritabani_yukle


def test_pristina_is_in_kosovo_country_list():
    city = sehir_veritabani_yukle()['Kosova']['Priştine']
    assert city['lat'] == pytest.approx(42.6629)
    assert city['lon'] == pytest.approx(21.1655)


@pytest.mark.parametrize('query', ['Priştine', 'Pristina', 'Prishtina', 'Prishtinë', 'Phriştine', 'prisht'])
def test_pristina_aliases_are_searchable(query):
    results = sehir_ara(query, limit=50)
    assert any(r['sehir'] == 'Priştine' and r['ulke'] == 'Kosova' for r in results)


@pytest.mark.parametrize('query', ['Priştine, Kosova', 'Pristina, Kosova', 'Prishtinë, Kosovo'])
def test_pristina_qualified_geocode_is_local(query):
    result = sehir_bul(query)
    assert result['kaynak'] == 'yerel'
    assert result['sehir'] == 'Priştine'
    assert result['ulke'] == 'Kosova'
    assert result['lat'] == pytest.approx(42.6629)
