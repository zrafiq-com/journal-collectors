import pandas as pd
from journal_collectors.elsevier_scrap import ScienceDirectScraper

QUERY_FILE = "./input.csv"
SUPPORTED_PUBLISHERS = ["SPRINGER", "IEEE","ASSOC","ELSEVIER"]


def load_queries(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path, skiprows=1)


def process_query(row):
    journal_name = row.iloc[0] if not pd.isna(row.iloc[0]) else "Unknown Journal"
    query = row.iloc[1]
    publisher = str(row.iloc[4]).strip().upper()
 
    if "ELSEVIER" in publisher:
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
