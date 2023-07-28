import sqlite3

from .scrape.work import Work

def open_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.isolation_level = None

    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS works (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        author_pseud TEXT NOT NULL,
        summary TEXT,
        notes TEXT,
        published TEXT NOT NULL,
        updated TEXT,
        words INTEGER NOT NULL,
        chapters_published INTEGER NOT NULL,
        chapters_total INTEGER,
        language TEXT NOT NULL,
        hits INTEGER NOT NULL,
        kudos INTEGER NOT NULL,
        comments INTEGER NOT NULL,
        bookmarks INTEGER NOT NULL,
        content TEXT
    );

    CREATE TABLE IF NOT EXISTS chapters (
        id INTEGER PRIMARY KEY,
        work_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        FOREIGN KEY (work_id) REFERENCES works (id)
    );

    CREATE TABLE IF NOT EXISTS taggings (
        tag TEXT NOT NULL,
        work_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        PRIMARY KEY (tag, work_id),
        FOREIGN KEY (work_id) REFERENCES works (id)
    );
    """);

    return conn

def write_work(conn: sqlite3.Connection, work: Work):
    cur = conn.cursor()

    cur.execute("BEGIN TRANSACTION;")

    if isinstance(work["content"], list):
        cur.executemany(
            f"""
            INSERT OR REPLACE INTO chapters VALUES (
                :id,
                {work["id"]},
                :title,
                :content
            );
            """,
            work["content"]
        )

        work["content"] = None
    
    cur.execute(
        """
        INSERT OR REPLACE INTO works VALUES (
            :id,
            :title,
            :author,
            :author_pseud,
            :summary,
            :notes,
            :published,
            :updated,
            :words,
            :chapters_published,
            :chapters_total,
            :language,
            :hits,
            :kudos,
            :comments,
            :bookmarks,
            :content
        );
        """,
        work
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
            { "tag": tag, "work_id": work["id"], "type": ty }
            for ty, tags in {
                "rating": work["rating_tags"],
                "warning": work["warning_tags"],
                "category": work["category_tags"],
                "fandom": work["fandom_tags"],
                "character": work["character_tags"],
                "relationship": work["relationship_tags"],
                "freeform": work["freeform_tags"]
            }.items()
            for tag in tags
        ]
    )

    cur.execute("COMMIT;")
