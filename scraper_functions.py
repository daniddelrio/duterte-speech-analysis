from urllib.parse import urlparse
import re

def is_absolute(url):
    return bool(urlparse(url).netloc)

def has_no_words(string):
	return re.match(r'\A[\W]+\Z', string) is not None