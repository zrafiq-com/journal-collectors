import csv
import os
import time
import pandas as pd 
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException
from urllib3.exceptions import MaxRetryError
        
        
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
# Ensure dependencies
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    import undetected_chromedriver as uc
    import time
except ImportError:
    os.system('pip install selenium webdriver-manager beautifulsoup4')
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options

def load_scraped_titles(csv_file="./output/elsevier_data.csv"):
    if not os.path.exists(csv_file):
        return set()
    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return {row["Title"].strip() for row in reader if row.get("Title")}

class ScienceDirectScraperDetails:
    BASE_URL = "https://www.sciencedirect.com/search"
    def __init__(self, url, shared_driver, journal_name=""):
        self.url = url
        self.driver = shared_driver
        self.journal_name = journal_name
        self.article_data = {
            "title": "", "writers": "", "Publisher": "",
            "publish_date": "", "abstract": "", "Journal": journal_name,
            "Volume/Issue": "N/A", "Cited By": "N/A",
        }

        self.soup = None

    def load_page(self):
        try:
            print(f"🔗 Loading page: {self.url}")
            self.driver.get(self.url)
            time.sleep(1)
           
            for i in range(3):
                scroll_point = self.driver.execute_script("return document.body.scrollHeight") * (i + 1) / 3
                self.driver.execute_script(f"window.scrollTo(0, {scroll_point});")
                
            self.driver.execute_script("window.scrollTo(0, 0);")
            
        except Exception as e:
            print(f"❌ Failed to load page {self.url}: {e}")
            self.driver.save_screenshot("load_page_crash.png")
            raise


    def handle_cookie_consent(self):
        try:
            cookie_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(),'Accept') or contains(text(),'Agree') or contains(text(),'Accept All')]")
            if cookie_buttons:
                print("Clicking cookie consent button...")
                cookie_buttons[0].click()
                time.sleep(1)
        except Exception as e:
            print(f"No cookie dialog or error: {e}")

    def parse_article(self):
        if "Your browser is outdated" in self.driver.page_source:
            print("Still detected as automation. Taking screenshot...")
            self.driver.save_screenshot("browser_detection.png")
            return False

        self.soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Title
        title_elem = self.soup.find('h1', id='screen-reader-main-title')
        if title_elem:
            title_span = title_elem.find('span', class_='title-text')
            if title_span:
                self.article_data["title"] = title_span.text.strip()
                print(f"title: {self.article_data['title']}")

        banner = self.soup.find('div', id='banner')
        if banner:
            wrapper = banner.find('div', class_='wrapper')
            if wrapper:
                # Writers
                writer_spans = wrapper.find_all('span', class_='react-xocs-alternative-link')
                writers = []
                for span in writer_spans:
                    writer_text = span.get_text().strip()
                    if writer_text:
                        writers.append(writer_text)
                if writers:
                    self.article_data['writers'] = ', '.join(writers)
                    # print(f" publisher: {self.article_data['writers']}")

                # Try click show more
                try:
                    show_more_btn = self.driver.find_element(By.ID, "show-more-btn")
                    show_more_btn.click()
                    time.sleep(1)
                    self.soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    banner = self.soup.find('div', id='banner')
                    wrapper = banner.find('div', class_='wrapper') if banner else None
                except Exception as e:
                    print(f"Note: Could not click 'Show more' button: {e}")

                # Affiliation
                if wrapper:
                    aff_dl = wrapper.find('dl', class_='affiliation')
                    if aff_dl:
                        self.article_data["Publisher"] = aff_dl.get_text().strip()
                        # print(f" affiliation: {self.article_data['affiliation']}")

                    pub_p = wrapper.find('p', class_='u-margin-s-bottom')
                    if pub_p:
                        self.article_data["publish_date"] = pub_p.get_text().strip()
                        # print(f" Year: {self.article_data['publish_date']}")

        # Abstract
        abstract_elem = self.soup.find('div', class_='abstract author')
        if abstract_elem:
            abstract_content = abstract_elem.find('div', class_='u-margin-s-bottom')
            if abstract_content:
                self.article_data["abstract"] = abstract_content.get_text().strip()
                # print(f"abstract ({self.article_data['abstract']} characters)")
        self.article_data["references"] = []
        # Keywords
        keywords_div = self.soup.find('div', id='aep-keywords-id4')
        if keywords_div:
            keyword_divs = keywords_div.find_all('div', class_='keyword')
            keywords = []
            for kw_div in keyword_divs:
                keyword_text = kw_div.get_text().strip()
                if keyword_text:
                    keywords.append(keyword_text)
            self.article_data["keywords"] = keywords
            # print(f"Found keywords: {self.article_data['keywords']}")

        # References
# References
        references_li = self.soup.find_all('li', class_='bib-reference')
        for item in references_li:
            authors = item.find('span', class_='author')
            title_tag = item.find('a', class_='title')
            host = item.find('span', class_='host')

            ref = {
                "authors": authors.get_text(strip=True) if authors else "",
                "title": title_tag.get_text(strip=True) if title_tag else "",
                "host": host.get_text(strip=True) if host else "",
            }

            self.article_data["references"].append(ref)

        # print(f"Found {self.article_data['references']} references")



        return True

    def save_data(self):
            csv_file = "./output/elsevier_data.csv"
            
            
            HEADERS = [
                "Title", "Authors", "Publisher",
                "Year", "Abstract", "Journal",
                "Volume/Issue", "Cited By",
            ]

            row_data = {
                "Title": self.article_data["title"],
                "Authors": self.article_data["writers"],
                "Publisher": "Elsevier",
                "Year": self.article_data["publish_date"],
                "Abstract": self.article_data["abstract"],
                "Journal": self.journal_name,
                "Volume/Issue": "N/A",
                "Cited By": "N/A",
                
            }

            file_exists = os.path.isfile(csv_file)

            with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=HEADERS)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row_data)

            print(f"Data appended to {csv_file}")


    def run(self):
        try:
            self.load_page()
            self.handle_cookie_consent()
            if self.parse_article():
                self.save_data()
        except Exception as e:
            print(f"Error scraping details: {e}")

class ScienceDirectScraper:
    BASE_URL = "https://www.sciencedirect.com/search"

    def __init__(self, journal=None, start_year=2000, end_year=2020, offset=0, show=100):
        self.journal = journal
        self.start_year = start_year
        self.end_year = end_year
        self.offset = offset
        self.show = show
        self.driver = self._setup_driver()

    @classmethod
    def build_query_url(cls, journal, start_year, end_year, offset=0, show=100):
        journal = journal.replace(" ", "%20").replace("&", "%26")
        return f"{cls.BASE_URL}?pub={journal}&date={start_year}-{end_year}&show={show}&offset={offset}"
    
    def safe_driver_get(self, url, retries=3):
        for attempt in range(1, retries + 1):
            try:
                print(f"🌐 Navigating to: {url} (Attempt {attempt})")
                self.driver.get(url)
                return True
            except (InvalidSessionIdException, WebDriverException, MaxRetryError, ConnectionRefusedError) as e:
                print(f"⚠️ Attempt {attempt} failed: {e}")
                try:
                    self.driver.quit()
                except:
                    pass
                print("♻️ Restarting Chrome driver...")
                time.sleep(2)
                try:
                    self.driver = self._setup_driver()
                except Exception as setup_error:
                    print(f"🚨 Could not restart driver: {setup_error}")
                    return False
                time.sleep(3)
        print(f"❌ All {retries} attempts failed for: {url}")
        return False
    
    def _setup_driver(self):

        options = uc.ChromeOptions()

        # Debugging: show the browser (remove --headless)
        # options.add_argument('--headless')  # keep this disabled for now
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")

        try:
            driver = uc.Chrome(options=options)
            driver.set_page_load_timeout(30)
            time.sleep(2)  # give Chrome time to fully start
            return driver
        except Exception as e:
            print(f"❌ Failed to start ChromeDriver: {e}")
            raise

    def get_dynamic_url(self):
        final_url = self.build_query_url(
            journal=self.journal,
            start_year=self.start_year,
            end_year=self.end_year,
            offset=self.offset,
            show=self.show
        )
        return final_url

    def scrape(self):
        url = self.get_dynamic_url()
        print(f"🔗 Scraping URL: {url}")

        if not self.safe_driver_get(url):
            return []

        time.sleep(2)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        results = soup.find_all("div", class_="result-item-container")

        data = []
        for item in results:
            a_tag = item.find("a", class_="result-list-title-link")
            if a_tag:
                title = a_tag.get_text(strip=True)
                link = "https://www.sciencedirect.com" + a_tag['href']
                data.append({'title': title, 'url': link})
        return data



    def open_each_url_sequentially(self, articles, wait_time=2):
        scraped_titles = load_scraped_titles()

        for article in articles:
            if article['title'].strip() in scraped_titles:
                print(f"⏩ Skipping already scraped: {article['title']}")
                continue

            print(f"🔍 Scraping: {article['title']}")
            print(f"Link: {article['url']}")
            scraper = ScienceDirectScraperDetails(article['url'], self.driver, journal_name=self.journal)
            scraper.run()
            print("-" * 50)
            time.sleep(wait_time)

        self.driver.quit()


    def run(self):
        total_scraped = 0
        while True:
            articles = self.scrape()
            if not articles:
                print("No more articles found. Exiting...")
                break

            print(f"Offset: {self.offset} | Articles scraped: {len(articles)}")
            total_scraped += len(articles)
            self.open_each_url_sequentially(articles)

            self.offset += self.show  # move to next page
        print(f"✅ Total articles scraped: {total_scraped}")


        