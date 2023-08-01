import asyncio
import ipaddress
from typing import Annotated, Optional
import typer
from ao3_scrape import database, scrape_works
from ao3_scrape.scrape import search

app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
def main(
    time_ago: int,
    time_unit: search.TimeUnit,
    db: str = "ao3.db",
    ip_network: Annotated[
        Optional[ipaddress.IPv6Network], typer.Option(parser=ipaddress.ip_network)
    ] = None,
    chunk_size_pages: int = 10,
):
    db_conn = database.open_db(db)

    asyncio.run(
        scrape_works(db_conn, ip_network, time_ago, time_unit, chunk_size_pages)
    )


if __name__ == "__main__":
    app()
