from datetime import datetime
from ipaddress import IPv4Network, IPv6Network
import random
import sqlite3
from typing import Any, Optional, Tuple, Type
import aiohttp
import asyncio
import socket
from ao3_scrape import database
from ao3_scrape.metrics import PAGE, WORK_UPDATED_TIME
from ao3_scrape.scrape import work, search


async def scrape_works(
    db: sqlite3.Connection,
    ip_network: Optional[IPv4Network | IPv6Network],
    page_concurrency: int,
    search_unit: search.TimeUnit,
    search_time: int,
    start_page: int,
):
    for chunk in range(start_page, 5001, page_concurrency):
        pages = await asyncio.gather(
            *[
                scrape_page(db, ip_network, search_time, search_unit, chunk + page)
                for page in range(page_concurrency)
            ]
        )

        PAGE.set(chunk)

        if pages[-1] is None:
            break


async def scrape_page(
    db: sqlite3.Connection,
    ip_network: Optional[IPv4Network | IPv6Network],
    search_time: int,
    search_unit: search.TimeUnit,
    page: int,
) -> Optional[int]:
    local_addr = (
        ip_network and ip_network[random.randint(0, ip_network.num_addresses - 1)]
    )
    connector = FreebindTCPConnector(local_addr=local_addr)

    async with aiohttp.ClientSession(connector=connector) as client:
        print(f"= Downloading page {page} from {local_addr or 'default address'}.")

        work_ids = await search.get_page(client, search_time, search_unit, page)
        if work_ids == []:
            return None

        for work_id in work_ids:
            print(f"Downloading work {work_id}.")

            parsed = await work.get_work(client, work_id)
            if parsed is None:
                print(f"Work {work_id} linked by search but not found upon request.")
                continue

            WORK_UPDATED_TIME.set(
                datetime.fromisoformat(
                    parsed["updated"] or parsed["published"]
                ).timestamp()
            )

            database.write_work(db, parsed)

        return page + 1


IP_FREEBIND = 15


class FreebindTCPConnector(aiohttp.TCPConnector):
    async def _wrap_create_connection(
        self,
        factory,
        host,
        port,
        req: "aiohttp.ClientRequest",
        timeout: "aiohttp.ClientTimeout",
        client_error: Type[Exception] = aiohttp.ClientConnectorError,
        # added
        ssl=None,
        family: int = 0,
        proto: int = 0,
        flags: int = 0,
        server_hostname: str | None = None,
        local_addr=None,
    ) -> Tuple[asyncio.Transport, Any]:
        try:
            async with aiohttp.helpers.ceil_timeout(timeout.sock_connect):
                sock = socket.socket(family=family, proto=proto)

                if local_addr:
                    sock.setsockopt(socket.SOL_IP, IP_FREEBIND, 1)
                    sock.bind((str(local_addr), 0))

                sock.connect((host, port))

                return await self._loop.create_connection(
                    factory,
                    ssl=ssl,
                    sock=sock,
                    server_hostname=server_hostname,
                )  # type: ignore[return-value]  # noqa
        except aiohttp.client_exceptions.cert_errors as exc:
            raise aiohttp.ClientConnectorCertificateError(
                req.connection_key, exc
            ) from exc
        except aiohttp.client_exceptions.ssl_errors as exc:
            raise aiohttp.ClientConnectorSSLError(req.connection_key, exc) from exc
        except OSError as exc:
            if exc.errno is None and isinstance(exc, asyncio.TimeoutError):
                raise
            raise client_error(req.connection_key, exc) from exc
