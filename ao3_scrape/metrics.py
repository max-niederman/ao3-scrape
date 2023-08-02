import asyncio
import os
from telnetlib import GA
from prometheus_client import Counter, Gauge, Histogram

PAGE_CONCURRENCY = Gauge("page_concurrency", "Number of pages downloaded concurrently.")

DOWNLOADED = Counter("downloaded", "Number of documents downloaded.", ["doc_type"])
DOWNLOADED.labels(doc_type="page")
DOWNLOADED.labels(doc_type="work")

DOWNLOADED_BYTES = Counter(
    "downloaded_bytes", "Number of bytes downloaded.", ["doc_type"]
)
DOWNLOADED_BYTES.labels(doc_type="page")
DOWNLOADED_BYTES.labels(doc_type="work")

DOWNLOAD_TIME = Histogram(
    "download_time",
    "Time taken to download documents.",
    ["doc_type"],
    buckets=[0.1, 0.25, 0.5, 0.75, 1, 2, 5, 10],
)
DOWNLOAD_TIME.labels(doc_type="page")
DOWNLOAD_TIME.labels(doc_type="work")

PAGE = Gauge("page", "Start of curreng chunk of pages being downloaded.")

WORK_UPDATED_TIME = Gauge("work_updated", "Update time of last work downloaded.")

DATABASE_SIZE = Gauge("database_size", "Size of database in bytes.")


def update_database_size(db: str):
    DATABASE_SIZE.set(os.path.getsize(db))


async def update_database_size_worker(db: str, period: float = 1):
    while True:
        update_database_size(db)
        await asyncio.sleep(period)
