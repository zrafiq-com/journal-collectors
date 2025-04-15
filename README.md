# IEEE Journal Scraper 🔍

This Python project automates the process of scraping journal information from IEEE Xplore using Selenium. It reads a list of queries from a CSV file (`query_data.csv`) and stores the results in an Excel file (`ieee_data.xlsx`).

---

## 📁 Project Structure

```bash
├── main.py                # Main script to run the scraper
├── query_data.csv         # CSV file with search queries (start from B column, row 2)
├── ieee_data.xlsx         # Excel file to store scraped data (auto-created)
├── requirements.txt       # Required Python packages
└── README.md              # This guide


⚠️ Important Note
Do NOT open the ieee_data.xlsx file while the script is running.
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



