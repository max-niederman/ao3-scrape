from enum import Enum
from bs4 import BeautifulSoup
import requests

from . import RatelimitError

class TimeUnit(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

def get_page(time_ago: int, time_unit: TimeUnit, page: int) -> list[int]:
    soup = download_page(time_ago, time_unit, page)
    return parse_page(soup)

def download_page(time_ago: int, time_unit: TimeUnit, page: int) -> BeautifulSoup:
    res = requests.get(
        f"https://archiveofourown.org/works/search?work_search%5Brevised_at%5D={str(time_ago)}+{time_unit.value}?page={page}&work_search%5Bquery%5D=&work_search%5Btitle%5D=&work_search%5Bcreators%5D=&work_search%5Bcomplete%5D=&work_search%5Bcrossover%5D=&work_search%5Bsingle_chapter%5D=0&work_search%5Bword_count%5D=&work_search%5Blanguage_id%5D=&work_search%5Bfandom_names%5D=&work_search%5Brating_ids%5D=&work_search%5Bcharacter_names%5D=&work_search%5Brelationship_names%5D=&work_search%5Bfreeform_names%5D=&work_search%5Bhits%5D=&work_search%5Bkudos_count%5D=&work_search%5Bcomments_count%5D=&work_search%5Bbookmarks_count%5D=&work_search%5Bsort_column%5D=revised_at&work_search%5Bsort_direction%5D=desc&commit=Search"
    )

    if res.status_code == 429:
        raise RatelimitError
    
    if res.status_code != 200:
        raise Exception(f"HTTP {res.status_code} {res.reason}")

    return BeautifulSoup(res.text, "html.parser")

def parse_page(soup: BeautifulSoup) -> list[int]:
    return [int(li["id"][5:]) for li in soup.select("li.work.blurb.group")]