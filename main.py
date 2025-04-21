import pandas as pd
from journal_collectors.scrap_ieee import IEEEScraper
from journal_collectors.springer_scrap import SpringerScraper
from journal_collectors.acm_scrap import AcmScraper
from journal_collectors.elsevier_scrap import ScienceDirectScraper

QUERY_FILE = "/home/darkside/PycharmProjects/journal-collectors/input.csv"
SUPPORTED_PUBLISHERS = ["SPRINGER", "IEEE","ASSOC","ELSEVIER"]


def load_queries(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path, skiprows=1)


def process_query(row):
    journal_name = row.iloc[0] if not pd.isna(row.iloc[0]) else "Unknown Journal"
    query = row.iloc[1]
    publisher = str(row.iloc[4]).strip().upper()

    if "SPRINGER" in publisher:
        print(f"\n🔍 Springer Query: {query}")
        scraper = SpringerScraper([query])
        scraper.scrape()
        scraper.cleanup()

    elif "IEEE" in publisher:
        print(f"\n🔍 IEEE Query: {query}")
        scraper = IEEEScraper(queries=[query])
        scraper.scrape()

    elif "ASSOC" in publisher:
        print(f"\n🔍 ACM Query: {query}")
        scraper = AcmScraper(queries=[query])
        scraper.scrape()
        scraper.cleanup()
        
    elif "ELSEVIER" in publisher:
        print(f"Processing ELSEVIER journal: {query}")
        scraper = ScienceDirectScraper(journal=query)
        scraper.run()
    else:
        print(f"⏭️ Skipping {journal_name} - Publisher '{publisher}' not supported")


def main():
    df= pd.read_csv(QUERY_FILE)
    for _, row in df[4:20].iterrows():
        process_query(row)


if __name__ == "__main__":
    main()
