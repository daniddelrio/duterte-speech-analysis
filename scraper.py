import requests
from bs4 import BeautifulSoup
import os, io
import time
import PyPDF2
import pandas

# Access .env file for the user agent header
from dotenv import load_dotenv
load_dotenv()
req_headers = {'user-agent': os.getenv('USER_AGENT')}

page_num = 1
url_func = lambda num: 'https://pcoo.gov.ph/presidential-speech/page/{}/'.format(num)
url = url_func(page_num)

SLEEP_TIME = 15

df = pandas.DataFrame(columns=['title', 'date', 'text'])
index = 0

try:
	page = requests.get(url, headers=req_headers)
	soup = BeautifulSoup(page.content, 'html.parser')

	while 'error404' not in soup.body['class']:
		print('Scraping: ' + url)

		# Iterate through each speech
		for row in soup.find_all(class_='focus-feature row'):
			title = row.find('h3').get_text().strip()
			date = row.find('small').get_text()

			# To get the page of the specific speech
			url = row.find('h3').find('a').get('href')
			time.sleep(SLEEP_TIME)
			page_speech = requests.get(url, headers=req_headers)
			soup_speech = BeautifulSoup(page_speech.content, 'html.parser')

			# To get the page of the PDF of the transcript
			url = soup_speech.find('a', string='Full Transcript').get('href')
			time.sleep(SLEEP_TIME)
			page_pdf = requests.get(url, headers=req_headers)
			soup_pdf = BeautifulSoup(page_pdf.content, 'html.parser')
			file = io.BytesIO()
			pdf_reader = PyPDF2.PdfFileReader(file)
			speech_text = '\n\n'.join([page.extractText() for page in pdf_reader.pages])

			df.loc[index] = {'title': title, 'date': date, 'text': speech_text}
			index += 1

		page_num += 1
		url = url_func(page_num)

		# Get next page of speeches
		time.sleep(SLEEP_TIME)
		page = requests.get(url, headers=req_headers)
		soup = BeautifulSoup(page.content, 'html.parser')
except Exception as ex:
	print(ex)
	print('Error in opening URL {}'.format(url))

df.to_csv('transcript.csv')


# Source: https://www.scrapehero.com/how-to-prevent-getting-blacklisted-while-scraping/