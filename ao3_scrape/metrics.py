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
    buckets=[0.1, 0.5, 1, 2, 5, 10, 15, 30, 60],
)
DOWNLOAD_TIME.labels(doc_type="page")
DOWNLOAD_TIME.labels(doc_type="work")

PAGE = Gauge("page", "Start of curreng chunk of pages being downloaded.")

WORK_UPDATED_TIME = Gauge("work_updated", "Update time of last work downloaded.")
