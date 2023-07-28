from sys import argv
from ao3_scrape import database
from ao3_scrape.scrape import work, search

if __name__ == '__main__':
    db = database.open_db("ao3.db")
    
    time_ago = int(argv[1])
    time_unit = search.TimeUnit(argv[2])

    for t in range(0, time_ago):
        print(f"== Downloading works updated {t} {time_unit.value}s ago.")
        page = 1
        while search.get_page(t, time_unit, page):
            print(f"= Downloading page {page}.")

            work_ids = search.get_page(t, time_unit, page)
            if work_ids == []:
                break
            
            for work_id in work_ids:
                print(f"Downloading work {work_id}.")
                database.write_work(db, work.get_work(work_id))

            page += 1