import pytest
from fastapi import HTTPException

from backend.main import profile_link_landing


def test_profile_landing_links_to_app_and_stores():
    profile_id = '05b5479c-3147-4200-9340-1fdbe7a2f17f'
    html = profile_link_landing(profile_id)
    assert f'com.fastastrology.fast://profile/{profile_id}' in html
    assert 'play.google.com/store/apps/details?id=com.fastastrology.fast' in html
    assert 'apps.apple.com/app/id6827527304' in html


@pytest.mark.parametrize('profile_id', ['bad', '<script>alert(1)</script>', '1234567890abcdef1234567890abcdef'])
def test_invalid_profile_id_is_rejected(profile_id):
    with pytest.raises(HTTPException) as exc:
        profile_link_landing(profile_id)
    assert exc.value.status_code == 404
