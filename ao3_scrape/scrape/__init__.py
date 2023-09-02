import asyncio
import random
import time
from typing import Awaitable, Callable
from aiohttp import ClientResponse
import ssl
import certifi

from bs4 import BeautifulSoup

from ao3_scrape.metrics import DOWNLOAD_TIME, DOWNLOADED, DOWNLOADED_BYTES


class RatelimitError(Exception):
    pass


class ParseError(Exception):
    doc_name: str
    doc_shortname: str

    def __init__(self, doc_name: str, doc_shortname: str):
        super().__init__(f"Failed to parse {doc_name}.")

        self.doc_name = doc_name
        self.doc_shortname = doc_shortname

    def save_html(self, soup: BeautifulSoup):
        with open(f"{self.doc_shortname}.html", "w") as f:
            f.write(soup.prettify())


BASE_URL = "https://archiveofourown.org"

RATELIMIT_TIMEOUT = 600
RATELIMIT_JITTER = 60

ssl_context = ssl.create_default_context(cafile=certifi.where())


def downloader(
    doc_type: str = None,
) -> Callable[[Callable[..., Awaitable[ClientResponse]]], Awaitable[BeautifulSoup]]:
    def decorator(func: Callable[..., Awaitable[ClientResponse]]):
        async def wrapper(*args, **kwargs):
            try:
                start = time.time()
                res = await func(*args, **kwargs)

                if res.status == 429:
                    raise RatelimitError()

                if res.status != 200:
                    raise Exception(f"HTTP {res.status_code} {res.reason}")

                text = await res.text()
                elapsed = time.time() - start

                DOWNLOADED.labels(doc_type=doc_type).inc()
                DOWNLOADED_BYTES.labels(doc_type=doc_type).inc(len(text))
                DOWNLOAD_TIME.labels(doc_type=doc_type).observe(elapsed)

                return BeautifulSoup(text, "html.parser")

            except RatelimitError:
                backoff = RATELIMIT_TIMEOUT + RATELIMIT_JITTER * random.random()
                print(f"Ratelimited, sleeping for {backoff} seconds...")
                await asyncio.sleep(backoff)

                return await wrapper(*args, **kwargs)

        return wrapper

    return decorator
