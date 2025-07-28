from api.utils.url import check_url, is_accessible_url, is_valid_url


def test_is_valid_url():
    actual = is_valid_url(url="dsqdsqd")
    assert not actual
    actual = is_valid_url(url="http://google.fr")
    assert actual


def test_is_accessible_url():
    actual = is_accessible_url(url="https://google.fr")
    assert actual
    actual = is_accessible_url(url="https://22221111.fr")
    assert not actual


def test_check_url():
    actual = check_url(url="https://google.fr")
    assert actual
    actual = check_url(url="tps://google.fr")
    assert not actual
    actual = check_url(url="https://22221111.fr")
    assert not actual
