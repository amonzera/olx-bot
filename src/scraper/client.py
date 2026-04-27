from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from curl_cffi import requests

from src.core.config import settings
from src.core.models import SearchLocation

logger = logging.getLogger(__name__)


LOCATION_PATHS = {
    SearchLocation.BRASIL.value: "brasil",
    SearchLocation.RIO_DE_JANEIRO.value: "estado-rj",
}


class OLXClient:
    def __init__(self):
        self.base_url = "https://www.olx.com.br"
        self.session = requests.Session(impersonate="chrome120")
        self.browser_headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Referer": self.base_url,
            "Upgrade-Insecure-Requests": "1",
        }

    def build_search_url(
        self,
        search_term: str,
        *,
        location: str = SearchLocation.BRASIL.value,
        min_price: int | None = None,
        max_price: int | None = None,
        page: int = 1,
    ) -> str:
        formatted_term = search_term.replace(" ", "-").lower()
        params = {"q": formatted_term}
        if min_price:
            params["ps"] = str(min_price)
        if max_price:
            params["pe"] = str(max_price)
        if page > 1:
            params["o"] = str(page)
        path = LOCATION_PATHS.get(location, LOCATION_PATHS[SearchLocation.BRASIL.value])
        return f"{self.base_url}/{path}?{urlencode(params)}"

    def fetch_search_page(
        self,
        search_term: str,
        *,
        location: str = SearchLocation.BRASIL.value,
        min_price: int | None = None,
        max_price: int | None = None,
        page: int = 1,
    ) -> str | None:
        """Fetch a search page using only HTTP requests and a persistent session."""
        url = self.build_search_url(
            search_term,
            location=location,
            min_price=min_price,
            max_price=max_price,
            page=page,
        )

        for attempt in range(settings.REQUEST_RETRIES + 1):
            try:
                response = self.session.get(
                    url,
                    headers=self.browser_headers,
                    timeout=settings.REQUEST_TIMEOUT_SECONDS,
                )

                if response.status_code == 200 and self._looks_like_search_page(response.text):
                    return response.text

                logger.warning(
                    "OLX request returned unexpected response",
                    extra={"status_code": response.status_code, "attempt": attempt, "url": url},
                )
                self._dump_debug_html(response.text, prefix=f"olx_status_{response.status_code}")
            except Exception:
                logger.exception(
                    "Unexpected error while fetching OLX search page",
                    extra={"attempt": attempt},
                )

            if attempt < settings.REQUEST_RETRIES:
                time.sleep(settings.REQUEST_BACKOFF_SECONDS * (attempt + 1))

        return None

    def _looks_like_search_page(self, html: str) -> bool:
        lowered = html.lower()
        return "__next_data__" in lowered or "olx" in lowered

    def _dump_debug_html(self, html: str, prefix: str) -> Path | None:
        try:
            dump_dir = settings.debug_dump_dir
            dump_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = dump_dir / f"{prefix}_{stamp}.html"
            path.write_text(html, encoding="utf-8")
            return path
        except OSError:
            logger.exception("Could not write debug HTML dump")
            return None

    def close(self):
        self.session.close()
