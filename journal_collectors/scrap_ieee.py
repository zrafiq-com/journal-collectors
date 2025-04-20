import os
import csv
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
import logging



logging.basicConfig(
    filename='debug.log',  # or use 'logs/ieee_scraper.log' in a logs folder
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
        self.csv_filename = "/home/darkside/PycharmProjects/journal-collectors/output/scraped_data.csv"
        self.original_window = None
        self.total_items_to_scrape = total_items_to_scrape
        self.items_per_page = items_per_page
        self.queries = queries
        self.create_csv_file()
        threading.Thread(target=self.wait_for_key, daemon=True).start()

    def wait_for_key(self):
        input("🔴 Press ENTER anytime to stop scraping...\n")
        IEEEScraper.stop_scraping = True

    def create_csv_file(self):
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=["Title", "Authors", "Publisher", "Year", "Abstract", "Journal", "Volume/Issue", "Cited By"])
                writer.writeheader()

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

        return [title, authors, publisher, year, abstract, journal, f"{volume} | {issue}", cited_by]

    def extract_results(self, limit):
        scraped_count = 0
        try:
            results = self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "List-results-items")))
            for item in results:
                if scraped_count >= limit or IEEEScraper.stop_scraping:
                    return scraped_count
                try:
                    data = self.extract_item_data(item)
                    self.save_data_to_csv(data)
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

                # url = f"https://ieeexplore.ieee.org/search/searchresult.jsp?contentType=periodicals&queryText={encoded_query}&highlight=true&returnType=SEARCH&matchPubs=true&rowsPerPage={self.items_per_page}&returnFacets=ALL&ranges=2001_2020_Year&refinements=ContentType:Journals&pageNumber={current_page}"
                url = (
                    f"https://ieeexplore.ieee.org/search/searchresult.jsp?"
                    f"action=search&matchBoolean=true&"
                    f"queryText=(%22All%20Metadata%22:{encoded_query})%20AND%20(%22Publication%20Title%22:{encoded_query})&"
                    f"ranges=2000_2022_Year&highlight=true&returnFacets=ALL&returnType=SEARCH&"
                    f"matchPubs=true&refinements=ContentType:Journals"
                )

                print(f"\n🔍 Query: {query} — Page {current_page} — {url}")
                self.open_site(url)
                scraped_now = self.extract_results(self.items_per_page)

                if scraped_now is None:
                    logger.warning("⚠️ No results found, moving to next query.")
                    break

                scraped_count += scraped_now
                current_page += 1
                time.sleep(5)
        self.close()
        logger.info("✅ Done scraping all queries.")

    def close(self):
        self.driver.quit()
