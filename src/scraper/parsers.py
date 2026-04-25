from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.core.dates import parse_publication_date
from src.core.models import Listing
from src.core.prices import parse_price_to_cents


OLX_BASE_URL = "https://www.olx.com.br"


def parse_search_results(html_content: str) -> list[Listing]:
    """
    Le o HTML da OLX e retorna anuncios normalizados.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    script_tag = soup.find('script', id='__NEXT_DATA__')
    if script_tag and script_tag.string:
        try:
            data = json.loads(script_tag.string)
            listings = [_listing_from_json(item) for item in _find_listing_dicts(data)]
            listings = [listing for listing in listings if listing is not None]
            if listings:
                return _unique_listings(listings)
        except json.JSONDecodeError:
            pass

    return _parse_search_results_from_html(soup)


def _find_listing_dicts(data: Any) -> Iterable[dict[str, Any]]:
    if isinstance(data, dict):
        if _looks_like_listing(data):
            yield data
        for value in data.values():
            yield from _find_listing_dicts(value)
    elif isinstance(data, list):
        for item in data:
            yield from _find_listing_dicts(item)


def _looks_like_listing(item: dict[str, Any]) -> bool:
    return bool(
        item.get("listId")
        or item.get("adId")
        or (item.get("subject") and item.get("url"))
        or (item.get("title") and item.get("url"))
    )


def _listing_from_json(item: dict[str, Any]) -> Listing | None:
    external_id = item.get("listId") or item.get("adId") or item.get("id")
    title = item.get("subject") or item.get("title")
    url = item.get("url") or item.get("href")
    if not external_id or not title or not url:
        return None

    raw_date = item.get("date") or item.get("publishedAt") or item.get("listTime") or item.get("createdAt")
    price = item.get("price") or item.get("priceValue") or item.get("displayPrice")

    return Listing(
        external_id=str(external_id),
        title=str(title).strip(),
        price_cents=parse_price_to_cents(price),
        url=urljoin(OLX_BASE_URL, str(url)),
        published_at=parse_publication_date(raw_date),
        raw_date=str(raw_date) if raw_date is not None else None,
        location=_extract_location(item),
        metadata={"raw": item},
    )


def _extract_location(item: dict[str, Any]) -> str | None:
    location = item.get("location") or item.get("region") or item.get("municipality")
    if isinstance(location, dict):
        return location.get("label") or location.get("name")
    if location:
        return str(location)
    return None


def _parse_search_results_from_html(soup: BeautifulSoup) -> list[Listing]:
    listings: list[Listing] = []
    links = soup.find_all('a', href=re.compile(r'olx\.com\.br/.+-\d+'))

    for link in links:
        url = link.get('href', '')
        match_id = re.search(r'-(\d+)$', url)
        if not match_id:
            continue

        title_tag = link.find('h2')
        title = title_tag.text.strip() if title_tag else "Sem Titulo"

        price_tag = link.find(string=re.compile(r'R\$'))
        date_tag = link.find(string=re.compile(r'\b(hoje|ontem|há|ha|\d{1,2}/\d{1,2}/\d{2,4})\b', re.I))

        listings.append(
            Listing(
                external_id=match_id.group(1),
                title=title,
                price_cents=parse_price_to_cents(price_tag),
                url=urljoin(OLX_BASE_URL, url),
                published_at=parse_publication_date(date_tag),
                raw_date=str(date_tag).strip() if date_tag else None,
            )
        )

    return _unique_listings(listings)


def _unique_listings(listings: list[Listing]) -> list[Listing]:
    seen: set[str] = set()
    unique: list[Listing] = []
    for listing in listings:
        key = f"{listing.source}:{listing.external_id}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(listing)
    return unique
