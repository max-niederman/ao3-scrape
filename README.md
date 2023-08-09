# AO3 Scrape

My first foray into web scraping.
A python script which downloads work metadata and chapter text from all works updated in a given time period.

I've used this to scrape a few days worth of works into a ~8GB SQLite database,
but I don't know if I'll ever scrape all of them because it's just kind of a pain to work with that much data:

- I need to find a VPS which:
  - Has a /64 or bigger IPv6 subnet (that's routed properly -- looking at you, Vultr)
  - Has >1TB of storage.
  - Doesn't empty my bank account.
- I should probably set up some way to compress the dataset, at _least_ with LZ4.
- Once I actually have all the data, I need some place to host it indefinitely.
  - The-Eye?
  - Just seeding it?
