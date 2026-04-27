from src.scraper.client import OLXClient


def test_client_builds_search_url_and_browser_headers():
    client = OLXClient()
    try:
        url = client.build_search_url("iphone 13", min_price=1500, max_price=2500)

        assert "https://www.olx.com.br/brasil?" in url
        assert "q=iphone-13" in url
        assert "ps=1500" in url
        assert "pe=2500" in url
        assert "User-Agent" in client.browser_headers
        assert "Accept-Language" in client.browser_headers
    finally:
        client.close()


def test_client_builds_rio_de_janeiro_search_url():
    client = OLXClient()
    try:
        url = client.build_search_url("macbook", location="rio de janeiro", max_price=4500, page=2)

        assert "https://www.olx.com.br/estado-rj?" in url
        assert "q=macbook" in url
        assert "pe=4500" in url
        assert "o=2" in url
    finally:
        client.close()
