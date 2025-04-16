# IEEE Journal Scraper 🔍

This Python project automates the process of scraping journal information from IEEE Xplore using Selenium. It reads a list of queries from a CSV file (`query_data.csv`) and stores the results in an Excel file (`ieee_data.xlsx`).

---

## 📁 Project Structure

# 🔍 Journal Scraper (IEEE, Springer, ACM)

This Python project automates scraping journal information from multiple academic publishers including **IEEE**, **Springer**, and **ACM** using **Selenium** and **BeautifulSoup**. It reads a list of queries from a CSV file and stores the results in a CSV file (`scraped_data.csv`), appending new data without overwriting existing results.

---

## 📁 Project Structure

```bash
├── main.py                      # Main entry point to run all scrapers
├── journal_collectors/
│   ├── scrap_ieee.py            # IEEE scraper logic
│   ├── springer_scrap.py        # Springer scraper logic
│   └── acm_scraper.py           # ACM scraper logic
├── query_data.csv               # CSV file with search queries (used by all scrapers)
├── scraped_data.csv             # Output file (auto-created & updated)
├── requirements.txt             # Required Python packages
└── README.md                    # This file



⚠️ Important Note
Do NOT open the scraped_data.xlsx file while the script is running.
Excel locks the file and will crash the script when trying to write data.


1. Create & Activate Virtual Environment


Windows:
python -m venv venv
venv\Scripts\activate
2. install all pakeges 
pip install -r requirements.txt

python main.py



📄 CSV Format for Queries
Your query_data.csv should look like this:

"Sr. No."	"Journal title"  "ISSN"	 "eISSN"	"Publisher name"



🧹 After Run
Once finished, your results will be saved to ieee_data.xlsx. You can open it to view the data after the script is fully done.



🧪 Features
✅ Multi-publisher support (IEEE, Springer, ACM)

🧠 Uses undetected_chromedriver to avoid bot detection

📄 Appends data to scraped_data.csv (no overwrite)

📊 Columns: Title, Authors, Publisher, Year, Abstract, Journal, Volume/Issue, Cited By

📅 Filters ACM search results by year (e.g., AfterYear=2000, BeforeYear=2020)

🔢 Prints count of how many items were scraped

🧹 Automatically cleans up browser sessions



📦 Output: scraped_data.csv
This file stores all journal data in the following order:
Title, Authors, Publisher, Year, Abstract, Journal, Volume/Issue, Cited By
Each run adds new data without overwriting old entries.


⚠️ Notes
Don't open scraped_data.csv while the script is running — it may cause write errors.

Make sure Chrome is installed and up to date.

If ACM scraping is slow or fails, increase the delay or check internet/captcha issues.



🚀 Extend It
You can add more scrapers (e.g., Elsevier, Wiley) using the same class-based pattern. Just follow the structure of existing scrapers and plug into main.py.


Let me know if you want this converted to a PDF or want to generate badges (PyPI, Python version, etc.) for GitHub.
