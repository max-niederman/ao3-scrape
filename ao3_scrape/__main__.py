from ipaddress import IPv4Network, IPv6Network
import ipaddress
from lib2to3.pgen2.token import OP
import sqlite3
from typing import Annotated, Any, Coroutine, Optional, TypeVar
import typer
import asyncio
from ao3_scrape import database
from ao3_scrape.scrape import work, search
import httpx


def main(
    time_ago: int,
    time_unit: search.TimeUnit,
    db: str = "ao3.db",
    ip_network: Annotated[Optional[IPv6Network], typer.Option(parser=ipaddress.ip_network)] = None,
):
    db_conn = database.open_db(db)

    asyncio.run(download_works(db_conn, ip_network, time_ago, time_unit))


async def download_works(
    db: sqlite3.Connection,
    ip_network: Optional[IPv4Network | IPv6Network],
    time_ago: int,
    time_unit: search.TimeUnit,
    chunk_size_pages: int = 10,
):
    for t in range(0, time_ago):
        print(f"== Downloading works updated {t} {time_unit.value}s ago.")
        for chunk in range(1, 5000, chunk_size_pages):
            await gather_monotonic_optional(
                [
                    download_page(db, ip_network, t, time_unit, chunk + page)
                    for page in range(1, 21)
                ]
            )


async def download_page(
    db: sqlite3.Connection,
    ip_network: Optional[IPv4Network | IPv6Network],
    t: int,
    time_unit: search.TimeUnit,
    page: int,
) -> Optional[int]:
    transport = httpx.AsyncHTTPTransport(
        local_address=(ip_network and ip_network[page % ip_network.num_addresses - 1])
    )
    async with httpx.AsyncClient(transport=transport) as client:
        print(f"= Downloading page {page}.")

        work_ids = await search.get_page(client, t, time_unit, page)
        if work_ids == []:
            return None

        for work_id in work_ids:
            print(f"Downloading work {work_id}.")
            parsed = await work.get_work(client, work_id)
            database.write_work(db, parsed)

        return page + 1


T = TypeVar("T")


def gather_monotonic_optional(
    coros: list[Coroutine[Any, None, Optional[T]]]
) -> Coroutine[Any, None, list[Optional[T]]]:
    async def cancel_following(
        coro: Coroutine[Any, None, Optional[T]], following: asyncio.Task[Optional[T]]
    ) -> Optional[T]:
        try:
            res = await coro
        except asyncio.CancelledError:
            res = None

        if res is None:
            following.cancel()

        return res

    tasks = [asyncio.create_task(coros[-1])]
    for coro in reversed(coros[:-1]):
        tasks.append(asyncio.create_task(cancel_following(coro, tasks[-1])))
    tasks.reverse()

    return asyncio.gather(*tasks)


if __name__ == "__main__":
    typer.run(main)
