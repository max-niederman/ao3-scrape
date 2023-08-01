import asyncio
from dataclasses import dataclass
from typing import Callable, TypeVar

from bs4 import BeautifulSoup


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


R = TypeVar("R")


def with_backoff(func: Callable[..., R]) -> Callable[..., R]:
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except RatelimitError:
            print("Ratelimited. Waiting 10 minutes and trying again.")
            await asyncio.sleep(600)
            return await wrapper(*args, **kwargs)

    return wrapper
