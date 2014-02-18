#/usr/bin/python

from bs4 import BeautifulSoup
import gzip
import re
import io
import urllib.request, urllib.error, urllib.parse
from Crawler import Crawler

class Batoto(Crawler):
	def __init__(self, url):
		if url == None:
			self.page = None
		else:
			self.page = BeautifulSoup(self.open_url(url))

	# Returns the series page for an individual chapter URL. Useful for scraping series metadata for an individual chapter.
	def chapter_series(self, url):
		chapter = BeautifulSoup(self.open_url(url))
		series_url = chapter.select('a[href*="http://www.batoto.net/comic/_/"]')[0].get('href')
		return series_url

	# Returns a dictionary containing chapter number, chapter name and chapter URL.
	def chapter_info(self, chapter_data):
		chapter = BeautifulSoup(str(chapter_data))
		chapter_url = chapter.a['href']
		chapter_number = re.search(r'Ch\.(.*?)[:\s].*', chapter.a.text).group(1)
		try:
			chapter_name = re.search(r'Ch\..*: *(.*)', chapter.a.text).group(1)
		except AttributeError:
			chapter_name = None
		return {"chapter": chapter_number, "name": chapter_name, "url": chapter_url}

	# Returns a list of chapter image URLs.
	def chapter_pages(self, chapter_url):
		chapter = BeautifulSoup(self.open_url(chapter_url))

		page_urls = chapter.find("select", {"name": "page_select"}).find_all("option")

		url_list = []
		for page in page_urls:
			url_list.append(page["value"])
		return url_list

	# Returns the image URL for the page.
	def chapter_images(self, chapter_url):
		pages = self.chapter_pages(chapter_url)

		image_list = []
		for page_url in pages:
			page = BeautifulSoup(self.open_url(page_url))

			image_url = page.find("div", {"id": "full_image"}).find("img")["src"]
			image_list.append(image_url)
		return image_list

	# Function designed to create a request object with correct headers, open the URL and decompress it if it's gzipped.
	def open_url(self, url):
		req = urllib.request.Request(url, headers={'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36', 'Accept-encoding': 'gzip'})
		response = urllib.request.urlopen(req)
		if response.info().get('Content-Encoding') == 'gzip':
			buf = io.BytesIO(response.read())
			data = gzip.GzipFile(fileobj=buf, mode="rb")
			return data
		else:
			return reponse.read()

	def series_chapters(self):
		chapter_row = self.page.find_all("tr", {"class": "row lang_English chapter_row"})
		chapters = []
		for chapter in chapter_row:
			chapters.append(self.chapter_info(chapter))
		return chapters

	def series_info(self, search):
		def title():
			description = self.page.find("meta", {"name":"description"})['content']
			return re.search(r'(.*)\n', description).group(1)

		def description():
			description = self.page.find("meta", {"name":"description"})['content']
			return re.search(r'.*\n\s(.*)', description).group(1)

		def author():
			return self.page.select('a[href*="http://www.batoto.net/search?artist_name"]')[0].text.title()

		def artist():
			return self.page.select('a[href*="http://www.batoto.net/search?artist_name"]')[1].text.title()

		options = {"title": title, "description": description, "author": author, "artist": artist}
		return options[search]()
