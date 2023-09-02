import asyncio
import ipaddress
from typing import Annotated, Optional
import prometheus_client
import typer
from ao3_scrape import database, scrape_works, metrics
from ao3_scrape.metrics import PAGE_CONCURRENCY
from ao3_scrape.scrape import search

app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
def scrape(
    db: str = "ao3.db",
    ip_network: Annotated[
        Optional[ipaddress.IPv6Network], typer.Option(parser=ipaddress.ip_network)
    ] = None,
    page_concurrency: int = 1,
    search_unit: search.TimeUnit = "day",
    search_time: int = 1,
    start_page: int = 1,
    continue_backwards: bool = False,
    prometheus_metrics: bool = True,
):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    db_conn = database.open_db(db)

    PAGE_CONCURRENCY.set(page_concurrency)

    loop.create_task(metrics.update_database_size_worker(db, period=1))
    loop.create_task(
        database.incremental_maintenance_worker(
            db_conn, interval=300, pause=60, load=0.75
        )
    )

    if prometheus_metrics:
        prometheus_client.start_http_server(8000)

    while True:
        print(f"== Downloading works updated {search_time} {search_unit.value}s ago.")

        loop.run_until_complete(
            scrape_works(
                db_conn,
                ip_network,
                page_concurrency,
                search_unit,
                search_time,
                start_page,
            )
        )

        if not continue_backwards:
            break

        search_time -= 1


@app.command()
def init_db(db: str = "ao3.db"):
    conn = database.open_db(db)
    database.init_db(conn)


if __name__ == "__main__":
    app()
