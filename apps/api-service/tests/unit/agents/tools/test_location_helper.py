from app.api.v1.chat.schemas import LocationHint
from app.utils.tools.location import build_web_search_location


def test_location_helper_requires_opt_in():
    hint = LocationHint(city="Austin")
    assert build_web_search_location(hint, share_location=False) is None


def test_location_helper_filters_empty_values():
    hint = LocationHint(city="  ", region="Texas")
    loc = build_web_search_location(hint, share_location=True)
    assert loc == {"type": "approximate", "region": "Texas"}


def test_location_helper_returns_none_when_all_empty():
    hint = LocationHint()
    assert build_web_search_location(hint, share_location=True) is None
