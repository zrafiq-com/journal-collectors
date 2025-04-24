import os
import csv
import time
import threading
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(
    filename='debug.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IEEEScraper:
    stop_scraping = False

    def __init__(self, queries, total_items_to_scrape=100000, items_per_page=20):
        chrome_options = Options()
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.csv_filename = "/home/dev/Desktop/clone scrap/journal-collectors/output/scraped_data.csv"
        self.executed_urls_file = "executed_urls.csv"

        self.original_window = None
        self.total_items_to_scrape = total_items_to_scrape
        self.items_per_page = items_per_page
        self.queries = queries
        self.executed_urls = set()

        self.create_csv_file()
        self.load_executed_urls()
        threading.Thread(target=self.wait_for_key, daemon=True).start()

    def wait_for_key(self):
        input("🔴 Press ENTER anytime to stop scraping...\n")
        IEEEScraper.stop_scraping = True

    def create_csv_file(self):
        os.makedirs(os.path.dirname(self.csv_filename), exist_ok=True)
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=["Title",  "Authors", "Publisher", "Year", "Abstract", "Journal", "Volume/Issue", "Cited By"])
                writer.writeheader()
        if not os.path.exists(self.executed_urls_file):
            with open(self.executed_urls_file, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["URL"])

    def load_executed_urls(self):
        if os.path.exists(self.executed_urls_file):
            with open(self.executed_urls_file, mode="r", encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader, None)
                for row in reader:
                    if row:
                        self.executed_urls.add(row[0])

    def save_data_to_csv(self, data):
        with open(self.csv_filename, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["Title", "Authors", "Publisher", "Year", "Abstract", "Journal", "Volume/Issue", "Cited By"])
            writer.writerow({
                "Title": data[0],
                "Authors": data[1],
                "Publisher": data[2],
                "Year": data[3],
                "Abstract": data[4],
                "Journal": data[5],
                "Volume/Issue": data[6],
                "Cited By": data[7]
            })

    def save_executed_url(self, url):
        if url not in self.executed_urls:
            with open(self.executed_urls_file, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([url])
            self.executed_urls.add(url)

    def is_url_executed(self, url):
        return url in self.executed_urls

    def open_site(self, url):
        self.driver.get(url)
        self.original_window = self.driver.current_window_handle

    def safe_find(self, parent, by, value, default="N/A", script_remove_class=False):
        try:
            element = parent.find_element(by, value)
            if script_remove_class:
                self.driver.execute_script("arguments[0].classList.remove('hide');", element)
            return element.text.strip()
        except:
            return default

    def extract_abstract(self, link):
        self.driver.execute_script("window.open(arguments[0]);", link)
        self.wait.until(EC.number_of_windows_to_be(2))
        new_window = [w for w in self.driver.window_handles if w != self.original_window][0]
        self.driver.switch_to.window(new_window)
        try:
            abstract_element = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "abstract-text")))
            abstract = abstract_element.text.strip()
        except:
            abstract = "N/A"
        self.driver.close()
        self.driver.switch_to.window(self.original_window)
        return abstract

    def extract_item_data(self, item):
        title_element = item.find_element(By.CSS_SELECTOR, "h3 a")
        title = title_element.text.strip()
        link = title_element.get_attribute("href")

        authors = self.safe_find(item, By.CSS_SELECTOR, ".author")
        journal = self.safe_find(item, By.CSS_SELECTOR, ".description a")
        year = self.safe_find(item, By.XPATH, ".//span[contains(text(), 'Year')]")
        volume = self.safe_find(item, By.XPATH, ".//span[contains(text(), 'Volume')]")
        issue = self.safe_find(item, By.XPATH, ".//a[contains(text(), 'Issue')]")
        publisher = self.safe_find(item, By.XPATH, ".//span[contains(text(), 'Publisher')]//following-sibling::span")
        cited_by = self.safe_find(item, By.XPATH, ".//a[contains(@href, '/citations')]")

        abstract = self.extract_abstract(link)

        return [title, authors, publisher, year, abstract, journal, f"{volume} | {issue}", cited_by, link]

    def extract_results(self, limit):
        scraped_count = 0
        try:
            results = self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "List-results-items")))
            for item in results:
                if scraped_count >= limit or IEEEScraper.stop_scraping:
                    return scraped_count
                try:
                    data = self.extract_item_data(item)
                    link = data[8]

                    if self.is_url_executed(link):
                        print(f"⏩ Skipping already executed item: {link}")
                        continue

                    self.save_data_to_csv(data)
                    self.save_executed_url(link)
                    scraped_count += 1
                    print(f"✅ Scraped item {scraped_count}")
                except Exception as e:
                    logger.warning(f"❌ Failed on item {scraped_count + 1}: {e}")
        except:
            logger.warning("⚠️ No results found on this page.")
            return None
        return scraped_count

    def encode_spaces(self, text: str) -> str:
        return text.replace(" ", "%20")

    def scrape(self):
        for query in self.queries:
            if IEEEScraper.stop_scraping:
                logger.info("🛑 Scraping manually stopped by user.")
                break

            encoded_query = self.encode_spaces(query)
            logger.info(f"\n🔍 Query: {query}")
            current_page = 1
            scraped_count = 0

            while scraped_count < self.total_items_to_scrape:
                if IEEEScraper.stop_scraping:
                    logger.info("🛑 Scraping manually stopped by user.")
                    break

                url = (
                    f"https://ieeexplore.ieee.org/search/searchresult.jsp?"
                    f"action=search&matchBoolean=true&"
                    f"queryText=(%22All%20Metadata%22:{encoded_query})%20AND%20(%22Publication%20Title%22:{encoded_query})&"
                    f"ranges=2000_2022_Year&highlight=true&returnFacets=ALL&returnType=SEARCH&"
                    f"matchPubs=true&refinements=ContentType:Journals&pageNumber={current_page}"
                )

                if self.is_url_executed(url):
                    print(f"⏩ Skipping already executed page: {url}")
                    current_page += 1
                    continue

                print(f"\n🔍 Query: {query} — Page {current_page}")
                self.open_site(url)
                scraped_now = self.extract_results(self.items_per_page)

                if scraped_now is None:
                    logger.warning("⚠️ No results found, moving to next query.")
                    break

                self.save_executed_url(url)
                scraped_count += scraped_now
                current_page += 1
                time.sleep(5)
        self.close()
        logger.info("✅ Done scraping all queries.")

    def close(self):
        self.driver.quit()
