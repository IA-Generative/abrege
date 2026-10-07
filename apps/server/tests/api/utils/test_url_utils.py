from api.utils.url import is_valid_url


def test_is_valid_url():
    actual = is_valid_url(url="dsqdsqd")
    assert actual is False
    actual = is_valid_url(url="http://google.fr")
    assert actual is True
    actual = is_valid_url(url="tps://google.fr")
    assert actual is False
