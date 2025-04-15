import time
import openpyxl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import os
import csv
import threading

class IEEEScraper:
    stop_scraping = False

    def __init__(self, queries, excel_filename="./output/ieee_data.xlsx", total_items_to_scrape=100000, items_per_page=20):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--ignore-certificate-errors")
        # chrome_options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.excel_filename = excel_filename
        self.original_window = None
        self.total_items_to_scrape = total_items_to_scrape
        self.items_per_page = items_per_page
        self.queries = queries
        self.create_excel_file()
        threading.Thread(target=self.wait_for_key, daemon=True).start()

    def wait_for_key(self):
        input("🔴 Press ENTER anytime to stop scraping...\n")
        IEEEScraper.stop_scraping = True

    def create_excel_file(self):
        try:
            self.wb = openpyxl.load_workbook(self.excel_filename)
            self.ws = self.wb.active
        except FileNotFoundError:
            self.wb = openpyxl.Workbook()
            self.ws = self.wb.active
            self.ws.title = "IEEE Results"
            headers = ["Title", "Authors", "Journal", "Year", "Volume/Issue", "Publisher", "Cited By", "Abstract"]
            self.ws.append(headers)

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

        return [title, authors, journal, year, f"{volume} | {issue}", publisher, cited_by, abstract]

    def save_data_to_excel(self, data):
        self.ws.append(data)
        self.save_to_excel()

    def save_to_excel(self):
        self.wb.save(self.excel_filename)

    def extract_results(self, limit):
        scraped_count = 0
        try:
            results = self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "List-results-items")))
            for item in results:
                if scraped_count >= limit or IEEEScraper.stop_scraping:
                    return scraped_count
                try:
                    data = self.extract_item_data(item)
                    self.save_data_to_excel(data)
                    scraped_count += 1
                    print(f"✅ Scraped item {scraped_count}")
                except Exception as e:
                    print(f"❌ Failed on item {scraped_count + 1}: {e}")
        except:
            print("⚠️ No results found on this page.")
            return None
        return scraped_count

    def encode_spaces(self, text: str) -> str:
        return text.replace(" ", "%20")

    def scrape(self):
        for query in self.queries:
            if IEEEScraper.stop_scraping:
                print("🛑 Scraping manually stopped by user.")
                break

            encoded_query = self.encode_spaces(query)
            print(f"\n🔍 Query: {query}")
            current_page = 1
            scraped_count = 0

            while scraped_count < self.total_items_to_scrape:
                if IEEEScraper.stop_scraping:
                    print("🛑 Scraping manually stopped by user.")
                    break

                url = f"https://ieeexplore.ieee.org/search/searchresult.jsp?contentType=periodicals&queryText={encoded_query}&highlight=true&returnType=SEARCH&matchPubs=true&rowsPerPage={self.items_per_page}&returnFacets=ALL&ranges=2001_2020_Year&refinements=ContentType:Journals&pageNumber={current_page}"

                print(f"\n🔍 Query: {query} — Page {current_page} — {url}")
                self.open_site(url)
                scraped_now = self.extract_results(self.items_per_page)

                if scraped_now is None:
                    print("⚠️ No results found, moving to next query.")
                    break

                scraped_count += scraped_now
                current_page += 1
                time.sleep(5)
        self.close()
        print("✅ Done scraping all queries.")

    def close(self):
        self.driver.quit()



class SpringerScraper:
    def __init__(self, queries):
        self.queries = queries
        self.driver = self._setup_driver()

    def _setup_driver(self):
        # Setup Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument('--headless=new')
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')

        # Setup WebDriver
        service = Service('./general/chromedriver.exe')
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
        # image_tag = item.find('img', {'data-test': 'image'})
        # image_url = image_tag['src'] if image_tag else 'N/A'

        return title, detail_link, content_type, published

    def _get_detail_page_info(self, detail_link):
        # Open detail page in new tab
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get(detail_link)
        # time.sleep(2)

        detail_soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Extract overview
        overview = detail_soup.find('div', {'data-test': 'darwin-journal-homepage-promo-text'})
        overview_text = overview.get_text(strip=True, separator=' ') if overview else 'N/A'

        # Extract Editor-in-Chief
        editor = detail_soup.find('dl', {'data-test': 'journal-editor-links'})
        editor_name = editor.find('li').get_text(strip=True) if editor else 'N/A'

        # Extract Metrics
        metrics = {}
        metric_labels = detail_soup.select('dl > dt[data-test]')
        for label in metric_labels:
            key = label.get_text(strip=True)
            value_tag = label.find_next_sibling('dd')
            metrics[key] = value_tag.get_text(strip=True) if value_tag else 'N/A'

        return overview_text, editor_name, metrics

    def scrape(self):
        output_file = "./output/springer.csv"
        file_exists = os.path.isfile(output_file)

        with open(output_file, mode='a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'link', 'type', 'year', 'overview', 'editor', 'metrics']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            for search_query in self.queries:
                print(f"\n🔍 Searching for: {search_query}")
                results = self._get_search_results(search_query)

                for item in results:
                    title, detail_link, content_type, published = self._extract_details_from_item(item)
                    overview_text, editor_name, metrics = self._get_detail_page_info(detail_link)

                    writer.writerow({
                        'title': title,
                        'link': detail_link,
                        'type': content_type,
                        'year': published,
                        'overview': overview_text,
                        'editor': editor_name,
                        'metrics': str(metrics)
                    })

                    # Close detail tab and return to the main page
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])


    def cleanup(self):
        self.driver.quit()