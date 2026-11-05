from backend import main


def test_app_version_is_disabled_by_default(monkeypatch):
    for name in (
        "APP_MIN_ANDROID_VERSION_CODE",
        "APP_LATEST_ANDROID_VERSION_CODE",
        "APP_MIN_IOS_BUILD",
        "APP_LATEST_IOS_BUILD",
    ):
        monkeypatch.delenv(name, raising=False)

    data = main.app_version()

    assert data["android"]["min_version_code"] == 0
    assert data["android"]["latest_version_code"] == 0
    assert data["ios"]["min_build"] == 0
    assert data["ios"]["latest_build"] == 0
    assert data["android_store_url"].startswith("https://play.google.com/")
    assert data["ios_store_url"].startswith("https://apps.apple.com/")


def test_app_version_reads_store_builds_from_env(monkeypatch):
    monkeypatch.setenv("APP_MIN_ANDROID_VERSION_CODE", "76")
    monkeypatch.setenv("APP_LATEST_ANDROID_VERSION_CODE", "77")
    monkeypatch.setenv("APP_MIN_IOS_BUILD", "76")
    monkeypatch.setenv("APP_LATEST_IOS_BUILD", "77")

    data = main.app_version()

    assert data["android"]["min_version_code"] == 76
    assert data["android"]["latest_version_code"] == 77
    assert data["ios"]["min_build"] == 76
    assert data["ios"]["latest_build"] == 77


def test_app_version_ignores_invalid_values(monkeypatch):
    monkeypatch.setenv("APP_MIN_ANDROID_VERSION_CODE", "not-a-number")
    monkeypatch.setenv("APP_MIN_IOS_BUILD", "-4")

    data = main.app_version()

    assert data["android"]["min_version_code"] == 0
    assert data["ios"]["min_build"] == 0
