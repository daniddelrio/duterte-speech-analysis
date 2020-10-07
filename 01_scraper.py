"""
Things to do:
Try out packages: tika and pdfplumber
Save the PDFs into a folder
Have two CSVs: one for tika and the other for pdfplumber
"""

import requests
from bs4 import BeautifulSoup
import os, io
import time
import PyPDF2
import pandas as pd
from datetime import datetime
import sys
import traceback
import slate3k as slate
from scraper_functions import parallel_process
from scraper_global_vars import *

# Access .env file for the user agent header
from dotenv import load_dotenv

load_dotenv()

if len(sys.argv) >= 2 and sys.argv[1] == "restart":
    df = pd.DataFrame(columns=["title", "date", "text"])
    page_num = 1
else:
    last_line = ""
    with open(LOGS_NAME, "r") as f:
        last_line = f.readlines()[-1]

    df = pd.read_csv(DF_NAME, index_col=0)
    page_num = int(last_line.split()[-2])

# Argument as the page number
try:
    page_num = int(sys.argv[1])
except:
    pass

url_func = lambda num: "https://pcoo.gov.ph/presidential-speech/page/{}/".format(num)
url = url_func(page_num)

if __name__ == '__main__':
    try:
        page = requests.get(url, headers=req_headers)
        soup = BeautifulSoup(page.content.decode("utf-8", "ignore"), "html.parser")

        while "error404" not in soup.body["class"]:
            print("Scraping: " + url)

            # Use parallel processing to process all the speeches per page
            df = parallel_process(df, page_num, soup.find_all(class_="focus-feature row"))

            page_num += 1
            url = url_func(page_num)

            # Get next page of speeches
            time.sleep(SLEEP_TIME)
            page = requests.get(url, headers=req_headers)
            soup = BeautifulSoup(page.content.decode("utf-8", "ignore"), "html.parser")

    except Exception as ex:
        traceback.print_exc()
        print("Error in opening URL {}".format(url))

# Source: https://www.scrapehero.com/how-to-prevent-getting-blacklisted-while-scraping/
