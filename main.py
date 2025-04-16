import pandas as pd
from journal_collectors.scrap_ieee import IEEEScraper
from journal_collectors.springer_scrap import SpringerScraper

QUERY_FILE = "./journal_collectors/query_data.csv"
SUPPORTED_PUBLISHERS = ["SPRINGER", "IEEE"]

def load_queries(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path, skiprows=1)

def process_query(row):
    journal_name = row[0] if not pd.isna(row[0]) else "Unknown Journal"
    query = row[1]
    publisher = str(row[4]).strip().upper()

    if "SPRINGER" in publisher:
        print(f"\n🔍 Springer Query: {query}")
        scraper = SpringerScraper([query])
        scraper.scrape()
        scraper.cleanup()

    elif  "IEEE" in publisher:
        print(f"\n🔍 IEEE Query: {query}")
        scraper = IEEEScraper(queries=[query])
        scraper.scrape()

    else:
        print(f"⏭️ Skipping {journal_name} - Publisher '{publisher}' not supported")

def main():
    df = load_queries(QUERY_FILE)
    for _, row in df.head(20).iterrows():
        process_query(row)
        

if __name__ == "__main__":
    main()
