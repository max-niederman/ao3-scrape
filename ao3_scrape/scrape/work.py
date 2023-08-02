import re
from typing import Optional, TypedDict

import aiohttp
from bs4 import BeautifulSoup, PageElement
from urllib.parse import unquote

from . import BASE_URL, ParseError, downloader


class Work(TypedDict):
    id: int

    title: str
    author: str
    author_pseud: str

    summary: Optional[str]
    notes: Optional[str]

    published: str
    updated: Optional[str]
    words: int
    chapters_published: int
    chapters_total: Optional[int]
    language: str

    hits: int
    kudos: int
    comments: int
    bookmarks: int

    rating_tags: list[str]
    warning_tags: list[str]
    category_tags: list[str]
    fandom_tags: list[str]
    character_tags: list[str]
    additional_tags: list[str]
    freeform_tags: list[str]

    content: str | list["Chapter"]


class Chapter(TypedDict):
    id: int

    title: str
    content: str


async def get_work(client: aiohttp.ClientSession, work_id: int) -> Optional[Work]:
    soup = await download_work(client, work_id)
    if soup is None:
        return None

    try:
        return parse_work(soup, work_id)
    except Exception as underlying:
        error = ParseError(f"work {work_id}", f"work_{work_id}")
        error.save_html(soup)
        raise error from underlying


@downloader(doc_type="work")
async def download_work(
    client: aiohttp.ClientSession, work_id: int
) -> Optional[BeautifulSoup]:
    res = await client.get(
        f"{BASE_URL}/works/{work_id}",
        params={"view_adult": "true", "view_full_work": "true"},
    )

    if res.status == 404:
        return None

    return res


def parse_work(soup: BeautifulSoup, work_id: int) -> Work:
    return {
        "id": work_id,
        "title": parse_work_title(soup),
        "author": parse_work_author(soup),
        "author_pseud": parse_work_author_pseud(soup),
        "summary": parse_work_module(soup, "summary"),
        "notes": parse_work_module(soup, "notes"),
        "published": parse_work_published(soup),
        "updated": parse_work_updated(soup),
        "words": parse_work_words(soup),
        "chapters_published": parse_work_chapters_published(soup),
        "chapters_total": parse_work_chapters_total(soup),
        "language": parse_work_language(soup),
        "hits": parse_work_hits(soup),
        "kudos": parse_work_kudos(soup),
        "comments": parse_work_comments(soup),
        "bookmarks": parse_work_bookmarks(soup),
        "rating_tags": parse_work_tag_set(soup, "rating"),
        "warning_tags": parse_work_tag_set(soup, "warning"),
        "category_tags": parse_work_tag_set(soup, "category"),
        "fandom_tags": parse_work_tag_set(soup, "fandom"),
        "relationship_tags": parse_work_tag_set(soup, "relationship"),
        "character_tags": parse_work_tag_set(soup, "character"),
        "freeform_tags": parse_work_tag_set(soup, "freeform"),
        "content": parse_work_content(soup),
    }


def parse_work_title(soup: BeautifulSoup) -> str:
    return soup.find("h2").text.strip()


def parse_work_author(soup: BeautifulSoup) -> str:
    tag = soup.find("a", rel="author")
    if tag is None:
        return "Anonymous"

    return unquote(tag["href"].split("/")[2])


def parse_work_author_pseud(soup: BeautifulSoup) -> str:
    tag = soup.find("a", rel="author")
    if tag is None:
        return "Anonymous"

    return unquote(tag["href"].split("/")[4])


def parse_work_module(soup: BeautifulSoup, name: str) -> Optional[str]:
    container = soup.find(class_=f"{name} module")
    if container is None or container.p is None:
        return None

    return container.find("p").text


def parse_work_published(soup: BeautifulSoup) -> str:
    return soup.find("dd", class_="published").text


def parse_work_updated(soup: BeautifulSoup) -> Optional[str]:
    tag = soup.find("dd", class_="status")
    if tag is None:
        return None

    return tag.text


def parse_work_words(soup: BeautifulSoup) -> int:
    return int(soup.find("dd", class_="words").text.replace(",", ""))


def parse_work_chapters_published(soup: BeautifulSoup) -> int:
    return int(soup.find("dd", class_="chapters").text.split("/")[0].replace(",", ""))


def parse_work_chapters_total(soup: BeautifulSoup) -> Optional[int]:
    text = soup.find("dd", class_="chapters").text.split("/")[1]

    if text == "?":
        return None
    else:
        return int(text.replace(",", ""))


def parse_work_language(soup: BeautifulSoup) -> str:
    return soup.find("dd", class_="language").text.strip()


def parse_work_hits(soup: BeautifulSoup) -> int:
    return int(soup.find("dd", class_="hits").text.replace(",", ""))


def parse_work_kudos(soup: BeautifulSoup) -> int:
    tag = soup.find("dd", class_="kudos")
    if tag is None:
        return 0

    return int(tag.text.replace(",", ""))


def parse_work_comments(soup: BeautifulSoup) -> int:
    tag = soup.find("dd", class_="comments")
    if tag is None:
        return 0

    return int(tag.text.replace(",", ""))


def parse_work_bookmarks(soup: BeautifulSoup) -> int:
    tag = soup.find("dd", class_="bookmarks")
    if tag is None:
        return 0

    return int(tag.text.replace(",", ""))


def parse_work_tag_set(soup: BeautifulSoup, name: str) -> list[str]:
    container = soup.find("dd", class_=f"{name} tags")
    if container is None:
        return []

    return [tag.text for tag in container.find_all("a")]


def parse_work_content(soup: BeautifulSoup) -> str | list[Chapter]:
    container = soup.find(id="chapters")

    chapter_tags = container.find_all(id=re.compile("chapter-\d+"))
    if chapter_tags:
        return [parse_chapter(tag) for tag in chapter_tags]
    else:
        return "\n".join(map(str, container.find(class_="userstuff").contents))


def parse_chapter(tag: PageElement) -> Chapter:
    title_tag = tag.find("h3")

    return {
        "id": title_tag.a["href"].split("/")[4],
        "title": title_tag.contents[2][1:].strip(),
        "content": "\n".join(map(str, tag.find(role="article").contents[3:])),
    }
