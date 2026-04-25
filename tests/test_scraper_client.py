from src.scraper.client import OLXClient


def test_client_builds_search_url_and_browser_headers():
    client = OLXClient()
    try:
        url = client.build_search_url("iphone 13", max_price=2500)

        assert "https://www.olx.com.br/brasil?" in url
        assert "q=iphone-13" in url
        assert "pe=2500" in url
        assert "User-Agent" in client.browser_headers
        assert "Accept-Language" in client.browser_headers
    finally:
        client.close()
