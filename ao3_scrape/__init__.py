from re import U
from typing import Optional, TypedDict
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote

class Work(TypedDict):
    id: int

    title: str
    author: str
    author_pseud: str

    summary: Optional[str]
    notes: Optional[str]
    endnotes: Optional[str]

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

class Chapter(TypedDict):
    id: int

    title: str
    content: str

def get_work(work_id: int) -> Optional[Work]:
    res = requests.get(f"https://archiveofourown.org/works/{work_id}?view_full_work=true")

    if res.status_code == 404:
        return None
    
    soup = BeautifulSoup(res.text, "html.parser")

    return {
        "id": work_id,

        "title": work_title(soup),
        "author": work_author(soup),
        "author_pseud": work_author_pseud(soup),

        "summary": work_module(soup, "summary"),
        "notes": work_module(soup, "notes"),
        "endnotes": work_module(soup, "end notes"),

        "published": work_published(soup),
        "updated": work_updated(soup),
        "words": work_words(soup),
        "chapters_published": work_chapters_published(soup),
        "chapters_total": work_chapters_total(soup),
        "language": work_language(soup),

        "hits": work_hits(soup),
        "kudos": work_kudos(soup),
        "comments": work_comments(soup),
        "bookmarks": work_bookmarks(soup),

        "rating_tags": work_tag_set(soup, "rating"),
        "warning_tags": work_tag_set(soup, "warning"),
        "category_tags": work_tag_set(soup, "category"),
        "fandom_tags": work_tag_set(soup, "fandom"),
        "relationship_tags": work_tag_set(soup, "relationship"),
        "character_tags": work_tag_set(soup, "character"),
        "freeform_tags": work_tag_set(soup, "freeform"),
    }

def work_title(soup: BeautifulSoup) -> str:
    return soup.find("h2").text.strip()

def work_author(soup: BeautifulSoup) -> str:
    return unquote(soup.find("a", rel="author")["href"].split("/")[2])

def work_author_pseud(soup: BeautifulSoup) -> str:
    return unquote(soup.find("a", rel="author")["href"].split("/")[4])

def work_module(soup: BeautifulSoup, name: str) -> Optional[str]:
    container = soup.find(class_=f"{name} module")
    if container is None:
        return None
    
    return container.p.text

def work_published(soup: BeautifulSoup) -> str:
    return soup.find("dd", class_="published").text

def work_updated(soup: BeautifulSoup) -> Optional[str]:
    tag = soup.find("dd", class_="status")
    if tag is None:
        return None
    
    return tag.text

def work_words(soup: BeautifulSoup) -> int:
    return int(soup.find("dd", class_="words").text.replace(",", ""))

def work_chapters_published(soup: BeautifulSoup) -> int:
    return int(soup.find("dd", class_="chapters").text.split("/")[0])

def work_chapters_total(soup: BeautifulSoup) -> Optional[int]:
    text = soup.find("dd", class_="chapters").text.split("/")[1]

    if text == "?":
        return None
    else:
        return int(text)

def work_language(soup: BeautifulSoup) -> str:
    return soup.find("dd", class_="language").text.strip()

def work_hits(soup: BeautifulSoup) -> int:
    return int(soup.find("dd", class_="hits").text.replace(",", ""))

def work_kudos(soup: BeautifulSoup) -> int:
    return int(soup.find("dd", class_="kudos").text.replace(",", ""))

def work_comments(soup: BeautifulSoup) -> int:
    tag = soup.find("dd", class_="comments")
    if tag is None:
        return 0

    return int(tag.text.replace(",", ""))

def work_bookmarks(soup: BeautifulSoup) -> int:
    tag = soup.find("dd", class_="bookmarks")
    if tag is None:
        return 0

    return int(tag.text.replace(",", ""))

def work_tag_set(soup: BeautifulSoup, name: str) -> list[str]:
    container = soup.find(class_=f"{name} tags")
    if container is None:
        return []

    return [tag.text for tag in container.find_all("a")]