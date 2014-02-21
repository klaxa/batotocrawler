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
		chapter_group = chapter.select('a[href*="http://www.batoto.net/group/"]')[0].text
		
		try:
			chapter_version = re.search(r'v([0-9]*)', chapter.a.text).group(1)
		except AttributeError:
			chapter_version = '1'
		if chapter_version == '':
			chapter_version = '1'

		try:
			chapter_name = re.search(r'Ch\..*: *(.*)', chapter.a.text).group(1)
		except AttributeError:
			chapter_name = None

		return {"chapter": chapter_number, "name": chapter_name, "url": chapter_url, "group": chapter_group, "version": int(chapter_version)}

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
		image_list = []

		try:
			pages = self.chapter_pages(chapter_url)

			for page_url in pages:
				page = BeautifulSoup(self.open_url(page_url))
				image_url = page.find("div", {"id": "full_image"}).find("img")["src"]
				image_list.append(image_url)
		except AttributeError:
			page = BeautifulSoup(self.open_url(chapter_url))
			images = page.find_all('img', src=re.compile("img[0-9]*\.batoto\.net/comics/.*/.*/.*/.*/read.*/"))
			
			for image in images:
				image_list.append(image['src'])

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

	def series_chapters(self, all_chapters=False):
		chapter_row = self.page.find_all("tr", {"class": "row lang_English chapter_row"})
		chapters = []
		for chapter in chapter_row:
			chapters.append(self.chapter_info(chapter))

		# Remove the v2 part from chapters that have it after the number (34v2) so zip files will be named correctly later.
		for chapter in chapters:
			if re.match(r'^[0-9]*[Vv][0-9]*', chapter["chapter"]):
				chapter["chapter"] = re.search(r'^([0-9]*)[Vv][0-9]*', chapter["chapter"]).group(1)

		'''If the optional parameter all_chapters is not True, keep the highest version
		number of a chapter only if a series has v1s and v2s present at the same time.'''
		if all_chapters == False:
			for num, chapter in enumerate(chapters):
				for chapter2 in chapters[num+1:]:
					if chapter["chapter"] == chapter2["chapter"]:
						if chapter["version"] > chapter2["version"]:
							chapters.remove(chapter2)
						elif chapter["version"] < chapter2["version"]:
							chapters.remove(chapter)

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
