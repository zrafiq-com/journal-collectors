import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import os
import csv
from webdriver_manager.chrome import ChromeDriverManager
import sys
import signal
import logging


logging.basicConfig(
    filename='debug.log',  # or use 'logs/ieee_scraper.log' in a logs folder
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



class SpringerScraper:
    def __init__(self, queries):
        self.queries = queries
        self.driver = self._setup_driver()

    def _setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')

        # ✅ Auto-manage chromedriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def _get_search_results(self, search_query):
        formatted_query = search_query.replace(' ', '+')
        url = f'https://link.springer.com/search?new-search=true&query={formatted_query}&content-type=journal&dateFrom=&dateTo=&sortBy=relevance'
        self.driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        return soup.find_all('li', class_='app-card-open')

    def _extract_details_from_item(self, item):
        title_tag = item.find('h3', class_='app-card-open__heading')
        title = title_tag.get_text(strip=True) if title_tag else 'N/A'
        link_tag = title_tag.find('a') if title_tag else None
        detail_link = link_tag['href'] if link_tag else 'N/A'
        content_type = item.find('span', {'data-test': 'content-type'})
        content_type = content_type.get_text(strip=True) if content_type else 'N/A'
        published = item.find('span', {'data-test': 'published'})
        published = published.get_text(strip=True) if published else 'N/A'
        return title, detail_link, content_type, published

    def _get_detail_page_info(self, detail_link):
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get(detail_link)

        detail_soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        overview = detail_soup.find('div', {'data-test': 'darwin-journal-homepage-promo-text'})
        overview_text = overview.get_text(strip=True, separator=' ') if overview else 'N/A'

        editor = detail_soup.find('dl', {'data-test': 'journal-editor-links'})
        editor_name = editor.find('li').get_text(strip=True) if editor else 'N/A'

        metrics = {}
        metric_labels = detail_soup.select('dl > dt[data-test]')
        for label in metric_labels:
            key = label.get_text(strip=True)
            value_tag = label.find_next_sibling('dd')
            metrics[key] = value_tag.get_text(strip=True) if value_tag else 'N/A'

        return overview_text, editor_name, metrics

    def scrape(self):
        output_file = "/home/darkside/PycharmProjects/journal-collectors/output/scraped_data.csv"
        file_exists = os.path.isfile(output_file)

        try:
            with open(output_file, mode='a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["Title", "Authors", "Publisher", "Year", "Abstract", "Journal", "Volume/Issue", "Cited By"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                for search_query in self.queries:
                    logger.info(f"\n🔍 Searching for: {search_query}")
                    results = self._get_search_results(search_query)

                    for item in results:
                        title, detail_link, content_type, published = self._extract_details_from_item(item)
                        overview_text, editor_name, metrics = self._get_detail_page_info(detail_link)

                        writer.writerow({
                            "Title": title,
                            "Authors": editor_name,  # You can parse actual authors if needed
                            "Publisher": 'SPRINGER',  # Assuming editor is considered publisher
                            "Year": f"Year:{published}",
                            "Abstract": overview_text,
                            "Journal": content_type,
                            "Volume/Issue": "N/A",  # Placeholder, you can extract if available
                            "Cited By": "N/A"  # Placeholder, you can extract if available
                        })

                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])

        except PermissionError as e:
            logger.error(f"PermissionError: {e}. Please close the file if it's open in another program.")
        except ConnectionResetError as e:
            logger.error(f"ConnectionResetError: {e}. The connection was forcibly closed by the remote host.")
        except KeyboardInterrupt:
            logger.info("\nProcess interrupted by the user. Exiting gracefully...")
            self.cleanup()
            sys.exit(0)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

    def cleanup(self):
        try:
            self.driver.quit()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise

# Setup for graceful termination on program exit
def signal_handler(sig, frame):
    logger.info("Process interrupted, cleaning up...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
