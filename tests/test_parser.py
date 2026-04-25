from pathlib import Path

from src.core.models import Listing
from src.scraper.parsers import parse_search_results


def test_parse_search_results_from_next_data_fixture():
    html = Path("tests/fixtures/search_next_data.html").read_text(encoding="utf-8")

    listings = parse_search_results(html)

    assert len(listings) == 3
    assert all(isinstance(listing, Listing) for listing in listings)
    assert listings[0].external_id == "111"
    assert listings[0].title == "iPhone 13 128GB sem defeito"
    assert listings[0].price_cents == 230000
    assert listings[0].location == "Sao Paulo"
