from enum import Enum
import aiohttp
from bs4 import BeautifulSoup

from . import BASE_URL, ParseError, RatelimitError, downloader


class TimeUnit(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


async def get_page(
    client: aiohttp.ClientSession, time_ago: int, time_unit: TimeUnit, page: int
) -> list[int]:
    soup = await download_page(client, time_ago, time_unit, page)
    try:
        return parse_page(soup)
    except Exception as underlying:
        error = ParseError(
            f"page {page} of search of works updated {time_ago} {time_unit.value}s ago",
            f"page_{time_ago}_{time_unit.value}_{page}",
        )
        error.save_html(soup)
        raise error from underlying


@downloader(doc_type="page")
async def download_page(
    client: aiohttp.ClientSession, time_ago: int, time_unit: TimeUnit, page: int
) -> BeautifulSoup:
    return await client.get(
        f"{BASE_URL}/works/search",
        params={
            "work_search[revised_at]": f"{str(time_ago)}+{time_unit.value}",
            "page": page,
            "work_search[query]": "",
            "work_search[title]": "",
            "work_search[creators]": "",
            "work_search[complete]": "",
            "work_search[crossover]": "",
            "work_search[single_chapter]": 0,
            "work_search[word_count]": "",
            "work_search[language_id]": "",
            "work_search[fandom_names]": "",
            "work_search[rating_ids]": "",
            "work_search[character_names]": "",
            "work_search[relationship_names]": "",
            "work_search[freeform_names]": "",
            "work_search[hits]": "",
            "work_search[kudos_count]": "",
            "work_search[comments_count]": "",
            "work_search[bookmarks_count]": "",
            "work_search[sort_column]": "revised_at",
            "work_search[sort_direction]": "desc",
            "commit": "Search",
        },
    )


def parse_page(soup: BeautifulSoup) -> list[int]:
    return [int(li["id"][5:]) for li in soup.select("li.work.blurb.group")]
