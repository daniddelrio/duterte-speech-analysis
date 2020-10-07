from urllib.parse import urlparse
import re
import slate3k as slate
import PyPDF2
from tika import parser
import requests
from bs4 import BeautifulSoup
from multiprocessing import cpu_count, Pool #for multiprocessing data
cores = cpu_count()
from datetime import datetime
import time
import sys   
sys.setrecursionlimit(10000)

from scraper_global_vars import *

def is_absolute(url):
    return bool(urlparse(url).netloc)

def has_no_words(string):
    return re.match(r"\A[\W]+\Z", string) is not None

def extract_pdf(file_name, pdf_reader="PyPDF2"):
    if pdf_reader == "PyPDF2" or pdf_reader == "slate":
        reader = PyPDF2.PdfFileReader(file_name)
        first_text = reader.getPage(0).extractText()
        # If PyPDF returns empty text, use Slate instead
        if first_text == "" or has_no_words(first_text):
            try:
                with open(file_name, "wb") as file:
                    return " ".join(slate.PDF(file)).replace("\x0c", "")
            except Exception as ex:
                return ""
        else:
            return "\n\n".join([str(page.extractText()) for page in reader.pages])
    elif pdf_reader == "tika":
        rawText = parser.from_file(file_name)
        return rawText['content']
    elif pdf_reader == "pdfplumber":
        reader = pdfplumber.open(file_name)
        text = "\n\n".join([page.extract_text() for page in reader.pages])
        reader.close()
        return text

def extract_page(row, df):
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
        temp_url = soup_speech.find("a", string="Full Transcript")
        if temp_url is None:
            return None
        temp_url = temp_url.get("href")

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
            # file = io.BytesIO(page_pdf.content)
            converted_date = datetime.strptime(date, "%B %d, %Y").strftime("%Y%m%d")
            speech_text = ""
            file_name = "pdfs/{}_{}.pdf".format(converted_date, " ".join(title.split()[:5]))
            with open(file_name, "wb") as file:
                file.write(page_pdf.content)

            speech_text = extract_pdf(file_name, PDF_READER)

        return {"title": title, "date": date, "text": speech_text}

    return None

def parallel_process(df, page_num, rows, n_cores=cores):
    from functools import partial
    pool = Pool(n_cores)
    speech_data = pool.map(partial(extract_page, df=df), rows)

    for speech in speech_data:
        if speech:
            # if df is still empty
            if df.shape[0] == 0:
                index = 0
            else:
                index = df.index[-1] + 1
            df.loc[index] = speech

            with open(LOGS_NAME, "a") as logs:
                logs.write(
                    "{} {} {}\n".format(
                        datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
                        str(page_num),
                        str(index),
                    )
                )

    df.to_csv(DF_NAME)

    pool.close()
    pool.join()
    return df
