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
from scraper_functions import is_absolute, has_no_words

# Access .env file for the user agent header
from dotenv import load_dotenv

load_dotenv()
req_headers = {"user-agent": os.getenv("USER_AGENT")}

SLEEP_TIME = 15
DF_NAME = "transcript.csv"
LOGS_NAME = "scrape_logs.txt"

if len(sys.argv) >= 2 and sys.argv[1] == "restart":
    df = pd.DataFrame(columns=["title", "date", "text"])
    page_num = 1
else:
    last_line = ""
    with open(LOGS_NAME, "r") as f:
        last_line = f.readlines()[-1]

    df = pd.read_csv(DF_NAME, index_col=0)
    page_num = int(last_line.split()[-2])

index = df.shape[0]

# Argument as the page number
try:
    page_num = int(sys.argv[1])
except:
    pass

url_func = lambda num: "https://pcoo.gov.ph/presidential-speech/page/{}/".format(num)
url = url_func(page_num)

try:
    page = requests.get(url, headers=req_headers)
    soup = BeautifulSoup(page.content.decode("utf-8", "ignore"), "html.parser")

    while "error404" not in soup.body["class"]:
        print("Scraping: " + url)

        # Iterate through each speech
        for row in soup.find_all(class_="focus-feature row"):
            title = row.find("h3").get_text().strip()
            date = row.find("small").get_text()

            if (
                title not in df["title"].values
                or (date not in df[df["title"] == title]["date"].values)
            ) or (
                not df[(df["title"] == title) & (df["date"] == date)]["text"]
                .isna()
                .iloc[-1]
                and has_no_words(
                    df[(df["title"] == title) & (df["date"] == date)]["text"].values[-1]
                )
            ):
                # To get the page of the specific speech
                url = row.find("h3").find("a").get("href")
                time.sleep(SLEEP_TIME)
                print("Scraping: " + url)
                page_speech = requests.get(url, headers=req_headers)
                soup_speech = BeautifulSoup(
                    page_speech.content.decode("utf-8", "ignore"), "html.parser"
                )

                # To get the page of the PDF of the transcript
                temp_url = soup_speech.find("a", string="Full Transcript").get("href")
                if is_absolute(temp_url):
                    url = temp_url
                else:
                    # Example: one href was a relative path that can be made valid by just appending to the previous URL
                    url += temp_url
                time.sleep(SLEEP_TIME)
                print("Scraping: " + url)
                page_pdf = requests.get(url, headers=req_headers)

                if page_pdf.status_code == 404:
                    speech_text = ""
                else:
                    file = io.BytesIO(page_pdf.content)
                    pdf_reader = PyPDF2.PdfFileReader(file)
                    first_text = pdf_reader.getPage(0).extractText()
                    if first_text == "" or has_no_words(first_text):
                        try:
                            file = io.BytesIO(page_pdf.content)
                            speech_text = " ".join(slate.PDF(file)).replace("\x0c", "")
                        except Exception as ex:
                            speech_text = ""
                    else:
                        speech_text = "\n\n".join(
                            [str(page.extractText()) for page in pdf_reader.pages]
                        )

                df.loc[index] = {"title": title, "date": date, "text": speech_text}

                with open(LOGS_NAME, "a") as logs:
                    logs.write(
                        "{} {} {}\n".format(
                            datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
                            str(page_num),
                            str(index),
                        )
                    )
                df.to_csv(DF_NAME)

                index += 1

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
