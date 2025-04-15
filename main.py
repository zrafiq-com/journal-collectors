from general.scraper_main import *
import pandas as pd
df = pd.read_csv("./general/query_data.csv", skiprows=1)

for _, row in df[:20].iterrows():
    query = row[1]  # Column B
    publisher = str(row[4]).strip().upper()  # Column E
    journal_name = row[0] if not pd.isna(row[0]) else "Unknown Journal"

    if "SPRINGER" in publisher:
        print(f"\n🔍 Springer Query: {query}")
        scraper = SpringerScraper([query])
        scraper.scrape()
        scraper.cleanup()

    elif "IEEE" in publisher:
        print(f"\n🔍 IEEE Query: {query}")
        # scraper = IEEEScraper(queries=[query])
        # scraper.scrape()

    else:
        print(f"⏭️ Skipping {journal_name} - Publisher {publisher} not supported")


