from sys import argv
from ao3_scrape import database, scrape

if __name__ == '__main__':
    db = database.open_db("ao3.db")
    
    work = scrape.get_work(int(argv[1]))
    if work is not None:
        database.write_work(db, work)
