import os
import csv
import time
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

logging.basicConfig(
    filename='debug.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AcmScraper:
    BASE_URL = "https://dl.acm.org"
    HEADERS = ["Title",
               "Authors", 
               "Publisher",
               "Year", 
               "Abstract", 
               "Journal", 
               "Volume/Issue", 
               "Cited By"]
    CSV_FILE = "./output/acm_data.csv"
    EXECUTED_URLS_FILE = "./executed_urls.csv"
    HEADERS = ["Title", "Authors", "Publisher", "Year", "Abstract", "Journal", "Volume/Issue", "Cited By"]

    def __init__(self, queries: list[str]):
        self.queries = queries
        self.scraped_count = 0
        self.executed_urls = self._load_executed_urls()
        self.driver = self._setup_driver()
        self.logger = self._setup_logger()

    def _load_executed_urls(self):
        if not os.path.exists(self.EXECUTED_URLS_FILE):
            return set()
        with open(self.EXECUTED_URLS_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            return set(row[0] for row in reader)

    def _setup_logger(self):
        logging.basicConfig(
            filename='debug.log',
            filemode='a',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def _setup_driver(self):
        options = uc.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("user-agent=Mozilla/5.0 ...")
        return uc.Chrome(options=options)

    def scrape(self):
        for query in self.queries:
            scraped_count = 0
            for page in range(1, 300):  # First 30 pages
                search_url = (
                    f"{self.BASE_URL}/action/doSearch?"
                    f"AllField={query}&pageSize=20&startPage={page}&AfterYear=2000&BeforeYear=2020&ContentItemType=research-article&SeriesKey=todaes"
                )
                self.driver.get(search_url)

                try:
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "h3.issue-item__title"))
                    )
                    soup = BeautifulSoup(self.driver.page_source, "html.parser")
                    titles = soup.select("h3.issue-item__title")

                    for h3 in titles:
                        title = h3.get_text(strip=True)
                        link = self.BASE_URL + h3.find('a')['href']
                        
                        # Check if the link is already executed
                        if link in self.executed_urls:
                            print(f"⏩ Skipped already executed: {link}")
                            continue

                        self._scrape_article(link)
                        self.executed_urls.add(link)  # Add to set after scraping
                        self._save_executed_url(link)

                except Exception as e:
                    logger.warning(f"⚠️ Failed to load search page {page} for query '{query}': {e}")
                    continue

    def _scrape_article(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1[property='name']"))
            )
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            paper_title = soup.select_one("h1[property='name']").text.strip()
            authors = [a.get_text(strip=True) for a in soup.select(
                "span[property='author'] span[property='givenName'], span[property='author'] span[property='familyName']")]
            abstract_section = soup.select_one("section#abstract > div[role='paragraph']")
            published_span = soup.select_one("div.core-published span.core-date-published")
            published_date = published_span.get_text(strip=True) if published_span else "Unknown"
            published_year = published_date.split()[-1] if published_date != "Unknown" else "Unknown"
            abstract = abstract_section.get_text(strip=True) if abstract_section else "No abstract found"
            journal_info = soup.select_one("div.core-enumeration a")

            journal = volume = issue = "Unknown"
            if journal_info:
                journal = journal_info.select_one("span[property='name']").get_text(
                    strip=True) if journal_info.select_one("span[property='name']") else "Unknown"
                volume = journal_info.select_one("span[property='volumeNumber']").get_text(
                    strip=True) if journal_info.select_one("span[property='volumeNumber']") else "N/A"
                issue = journal_info.select_one("span[property='issueNumber']").get_text(
                    strip=True) if journal_info.select_one("span[property='issueNumber']") else "N/A"

            data = {
                "Title": paper_title,
                "Authors": ", ".join(authors),
                "Publisher": "ACM",
                "Year": f"{published_year}",
                "Abstract": abstract,
                "Journal": journal,
                "Volume/Issue": f"Volume:{volume}/Issue:{issue}",
                "Cited By": "N/A"
            }
            self.scraped_count += 1
            print(f"✅ Scraped item {self.scraped_count}")
            self._save_to_csv(data)

        except Exception as e:
            logger.warning(f"⚠️ Error scraping article: {e}")

    def _save_to_csv(self, row_data):
        file_exists = os.path.exists(self.CSV_FILE)
        with open(self.CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.HEADERS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row_data)

    def _save_executed_url(self, url):
        with open(self.EXECUTED_URLS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([url])

    def cleanup(self):
        self.driver.quit()
