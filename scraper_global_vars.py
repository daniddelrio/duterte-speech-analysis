import os

req_headers = {"user-agent": os.getenv("USER_AGENT")}

SLEEP_TIME = 15
DF_NAME = "tika_transcript.csv"
# Change according to the Python package you want to use
READERS = ["PyPDF2", "slate", "tika", "pdfplumber"]
PDF_READER = READERS[2]

LOGS_NAME = "scrape_logs.txt"
