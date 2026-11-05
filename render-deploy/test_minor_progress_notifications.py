from backend import main


def test_minor_progress_notification_endpoint_is_bounded_and_does_not_persist(monkeypatch):
    constructed = {}

    class FakeEngine:
        def fbst_analizi_yap(self, *, sessiz):
            assert sessiz is True

    def fake_engine(**kwargs):
        constructed.update(kwargs)
        return FakeEngine()

    monkeypatch.setattr(main, "FBST_Engine", fake_engine)
    monkeypatch.setattr(
        main,
        "_natal_minor_progress_yorumlari",
        lambda motor, gun_sayisi: [{"tarih": str(i)} for i in range(gun_sayisi)],
    )
    monkeypatch.setattr(
        main,
        "_cache_engine",
        lambda *_: (_ for _ in ()).throw(AssertionError("must not persist a session")),
    )

    request = main.MinorProgressNotificationsInput(
        tarih="1990-01-01",
        saat="12:00",
        sehir="İstanbul",
        ulke="Türkiye",
        enlem=41.0,
        boylam=29.0,
        lang="en",
        days=100,
    )
    response = main.minor_progress_notifications(request)

    assert response["days"] == 30
    assert len(response["entries"]) == 30
    assert response["lang"] == "en"
    assert constructed["lang"] == "en"
    assert constructed["mod"] == "bireysel_natal"
