#/usr/bin/python

from __main__ import print_info
from bs4 import BeautifulSoup
from Crawler import Crawler
import gzip
import io
import logging
import re
import urllib.request, urllib.error, urllib.parse

class KissManga(Crawler):
	uses_groups = False

	def __init__(self, url):
		self.url = url
		if re.match(r'.*kissmanga\.com/Manga/.*/', url, flags=re.IGNORECASE):
			self.page = BeautifulSoup(self.open_url(self.chapter_series(url)))
			self.init_with_chapter = True
			logging.debug('Object initialized with chapter')
		else:
			self.page = BeautifulSoup(self.open_url(url))
			self.init_with_chapter = False
			logging.debug('Object initialized with series')
		logging.debug('Object created with ' + url)

	# Returns the series page for an individual chapter URL. Useful for scraping series metadata for an individual chapter.
	def chapter_series(self, url):
		logging.debug('Fetching series URL')
		series_url = re.match(r'(.*kissmanga\.com/Manga/.*)/.*', url, flags=re.IGNORECASE).group(1)
		logging.debug('Series URL: ' + series_url)
		return series_url

	# Returns a dictionary containing chapter number, chapter name and chapter URL.
	def chapter_info(self, chapter_data):
		logging.debug('Fetching chapter info')
		chapter = BeautifulSoup(str(chapter_data))
		chapter_url = 'http://kissmanga.com' + chapter.a['href']
		chapter_number = re.search(r'{} (Ch\.)?([0-9\.]*).*'.format(self.series_info('title')), chapter.a.text).group(2)
		if chapter_number == '':
			chapter_number = re.search(r'{} .* ([0-9\.]*) -.*'.format(self.series_info('title')), chapter.a.text).group(1)

		try:
			chapter_name = re.search(r'.*: (.*)', chapter.a.text).group(1)
		except AttributeError:
			chapter_name = None

		logging.debug('Chapter number: ' + chapter_number)
		logging.debug('Chapter name: ' + str(chapter_name))
		logging.debug('Chapter URL: ' + chapter_url)

		return {"chapter": chapter_number, "name": chapter_name, "url": chapter_url}

	# Returns the image URL for the page.
	def chapter_images(self, chapter_url):
		logging.debug('Fetching chapter images')
		image_list = []

		page = BeautifulSoup(self.open_url(chapter_url.encode('ascii', 'ignore').decode('utf-8')))
		scripts = page.find("div", {"id": "containerRoot"}).find_all('script')
		for script in scripts:
			if re.search(r'lstImages', script.text):
				for match in re.findall(r'lstImages\.push\(".*"\);', script.text):
					image_list.append(re.search(r'lstImages\.push\("(.*)"\);', match).group(1))
				break

		logging.debug('Chapter images: ' + str(image_list))
		return image_list

	def download_chapter(self, chapter, download_directory, download_name):
		files = []
		warnings = []

		logging.debug('Downloading chapter {}.'.format(chapter["url"]))
		page = BeautifulSoup(self.open_url(chapter["url"].encode('ascii', 'ignore').decode('utf-8')))
		scripts = page.find("div", {"id": "containerRoot"}).find_all('script')
		for script in scripts:
			if re.search(r'lstImages', script.text):
				matches = re.findall(r'lstImages\.push\(".*"\);', script.text)
				image_count = len(matches)
				for image_name, match in enumerate(matches, start=1):
					print_info("Download: Page {0:04d}".format(image_name) + " / {0:04d}".format(image_count))
					image_url = re.search(r'lstImages\.push\("(.*)"\);', match).group(1)
					file_extension = re.search(r'.*\.([A-Za-z]*)', image_url).group(1)
					req = urllib.request.Request(image_url, headers={'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36', 'Accept-encoding': 'gzip'})

					try:
						response = urllib.request.urlopen(req)
					except urllib.error.HTTPError as e:
						print_info('WARNING: Unable to download file ({}).'.format(str(e)))
						warnings.append('Download of page {}, chapter {}, series "{}" failed.'.format(image_name, chapter["chapter"], self.series_info('title')))
						continue

					filename = download_directory + "/" + str(image_name) + "." + file_extension
					f = open(filename, 'wb')
					f.write(response.read())
					f.close()
					files.append(filename)
				break

		filename = download_directory + '/' + download_name
		self.zip_files(files, filename)
		return warnings

	# Function designed to create a request object with correct headers, open the URL and decompress it if it's gzipped.
	def open_url(self, url):
		logging.debug(url)
		req = urllib.request.Request(url, headers={'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36', 'Accept-encoding': 'gzip', 'Cookie': 'vns_Adult=yes'})
		response = urllib.request.urlopen(req)

		if response.info().get('Content-Encoding') == 'gzip':
			buf = io.BytesIO(response.read())
			data = gzip.GzipFile(fileobj=buf, mode="rb")
			return data
		else:
			return reponse.read()

	def series_chapters(self, all_chapters=False):
		logging.debug('Fetching series chapters')
		chapter_row = self.page.find("table", {"class": "listing"}).find_all("tr")[2:]
		chapters = []
		for chapter in chapter_row:
			chapters.append(self.chapter_info(chapter))

		# If the object was initialized with a chapter, only return the chapters.
		if self.init_with_chapter == True and all_chapters == False:
			logging.debug('Searching for specified chapter')
			for chapter in chapters:
				if self.url == chapter["url"]:
					logging.debug('Chapter found: ' + str(chapter))
					return [chapter]

		return chapters

	def series_info(self, search):
		def title():
			return self.page.find("a", {"class":"bigChar"}).text

		def description():
			description = self.page.find("div", {"class":"barContent"}).find_all("div")[1].find_all("div")[0].text
			return description.strip('\n')

		def author():
			return self.page.select('a[href*="/AuthorArtist/"]')[0].text.title()

		options = {"title": title, "description": description, "author": author}
		return options[search]()
