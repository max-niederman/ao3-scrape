import asyncio
import os
import sqlite3

from .scrape.work import Work

SQLITE_ZSTD_PATH = os.environ["SQLITE_ZSTD_PATH"]


def open_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.isolation_level = None

    conn.enable_load_extension(True)
    conn.load_extension(f"{SQLITE_ZSTD_PATH}/libsqlite_zstd.so")

    cur = conn.cursor()
    cur.executescript(
        """
        PRAGMA auto_vacuum = full;
        PRAGMA journal_mode = wal;
        PRAGMA foreign_keys = on;
        """
    )

    return conn


def init_db(conn: sqlite3.Connection):
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE works (
            id INTEGER PRIMARY KEY, title TEXT NOT NULL,
            author TEXT NOT NULL,
            author_pseud TEXT NOT NULL,
            summary TEXT,
            notes TEXT,
            published INTEGER NOT NULL,
            updated INTEGER,
            words INTEGER NOT NULL,
            chapters_published INTEGER NOT NULL,
            chapters_total INTEGER,
            language TEXT NOT NULL,
            hits INTEGER NOT NULL,
            kudos INTEGER NOT NULL,
            comments INTEGER NOT NULL,
            bookmarks INTEGER NOT NULL
        );

        CREATE TABLE chapters (
            id INTEGER PRIMARY KEY,
            work_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (work_id) REFERENCES works (id)
        );

        CREATE TABLE taggings (
            tag TEXT NOT NULL,
            work_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            PRIMARY KEY (tag, work_id),
            FOREIGN KEY (work_id) REFERENCES works (id)
        );

        CREATE INDEX works_by_published ON works (published);
        CREATE INDEX works_by_updated ON works (updated);
        CREATE INDEX works_by_words ON works (words);
        CREATE INDEX works_by_language ON works (language);
        CREATE INDEX works_by_hits ON works (hits);
        CREATE INDEX works_by_kudos ON works (kudos);
        CREATE INDEX works_by_comments ON works (comments);
        CREATE INDEX works_by_bookmarks ON works (bookmarks);

        CREATE INDEX chapters_by_work_id ON chapters (work_id);

        CREATE INDEX taggings_by_work_id ON taggings (work_id);
        CREATE INDEX taggings_by_tag ON taggings (tag);

        SELECT zstd_enable_transparent('{
            \"table\": \"chapters\",
            \"column\": \"content\",
            \"compression_level\": 19,
            \"dict_chooser\": \"SELECT language FROM works WHERE id = work_id LIMIT 1\"
        }');
        """
    )


def write_work(conn: sqlite3.Connection, work: Work):
    cur = conn.cursor()

    cur.execute("BEGIN TRANSACTION;")

    cur.execute(
        """
        INSERT OR REPLACE INTO works VALUES (
            :id,
            :title,
            :author,
            :author_pseud,
            :summary,
            :notes,
            unixepoch(:published),
            unixepoch(:updated),
            :words,
            :chapters_published,
            :chapters_total,
            :language,
            :hits,
            :kudos,
            :comments,
            :bookmarks
        );
        """,
        work,
    )

    cur.executemany(
        f"""
        INSERT OR REPLACE INTO chapters VALUES (
            :id,
            {work["id"]},
            :title,
            :content
        );
        """,
        work["content"],
    )

    cur.executemany(
        """
        INSERT OR REPLACE INTO taggings VALUES (
            :tag,
            :work_id,
            :type
        );
        """,
        [
            {"tag": tag, "work_id": work["id"], "type": ty}
            for ty, tags in {
                "rating": work["rating_tags"],
                "warning": work["warning_tags"],
                "category": work["category_tags"],
                "fandom": work["fandom_tags"],
                "character": work["character_tags"],
                "relationship": work["relationship_tags"],
                "freeform": work["freeform_tags"],
            }.items()
            for tag in tags
        ],
    )

    cur.execute("COMMIT;")


def run_incremental_maintenance(conn: sqlite3.Connection, duration, load):
    cur = conn.cursor()

    cur.executescript(
        f"""
        SELECT zstd_incremental_maintenance({duration}, {load});
        """
    )


async def incremental_maintenance_worker(
    conn: sqlite3.Connection,
    interval: float = 300,
    pause: float = 60,
    load: float = 0.75,
):
    while True:
        run_incremental_maintenance(conn, pause, load)
        await asyncio.sleep(interval)
