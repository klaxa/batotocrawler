#/usr/bin/python

from __main__ import print_info
from bs4 import BeautifulSoup
from Scrapers.Crawler import Crawler
import gzip
import io
import logging
import re
import urllib.request, urllib.error, urllib.parse

class DynastyReader(Crawler):
	site_name = 'Dynasty Reader'
	uses_groups = False

	def __init__(self, url):
		self.url = url
		if re.match(r'.*dynasty-scans\.com/series/.*', url):
			self.page = BeautifulSoup(self.open_url(url))
			self.init_with_chapter = False
			logging.debug('Object initialized with series')
		elif re.match(r'.*dynasty-scans\.com/chapters/.*', url):
			self.page = BeautifulSoup(self.open_url(self.chapter_series(url)))
			self.init_with_chapter = True
			logging.debug('Object initialized with chapter')
		else:
			self.page = None
			self.init_with_chapter = False
			logging.debug('Empty object initialized')
		logging.debug('Object created with ' + url)

	# Returns the series page for an individual chapter URL. Useful for scraping series metadata for an individual chapter.
	def chapter_series(self, url):
		logging.debug('Fetching series URL')
		chapter = BeautifulSoup(self.open_url(url))
		series_url = 'http://dynasty-scans.com/' + chapter.find('a', href=re.compile(r'/series/'))['href']
		logging.debug('Series URL: ' + series_url)
		return series_url

	# Returns a dictionary containing chapter number, chapter name and chapter URL.
	def chapter_info(self, chapter_data):
		logging.debug('Fetching chapter info')
		chapter = BeautifulSoup(str(chapter_data))
		chapter_url = 'http://dynasty-scans.com' + chapter.a['href']
		try:
			chapter_number = re.search(r'Chapter (.*?)(:|$)', chapter.a.text).group(1)
		except:
			chapter_number = chapter.a.text
		
		try:
			chapter_number = float(chapter_number)
		except:
			pass

		try:
			chapter_name = re.search(r'Chapter\s.*:\s(.*)', chapter.a.text).group(1)
		except AttributeError:
			chapter_name = None

		logging.debug('Chapter number: {}'.format(chapter_number))
		logging.debug('Chapter name: ' + str(chapter_name))
		logging.debug('Chapter URL: ' + chapter_url)

		return {"chapter": chapter_number, "name": chapter_name, "url": chapter_url}

	def download_chapter(self, chapter, download_directory, download_name):
		files = []
		warnings = []

		logging.debug('Downloading chapter {}.'.format(chapter["url"]))
		page = BeautifulSoup(self.open_url(chapter["url"]))
		scripts = page.find_all("script")
		for script in scripts:
			if re.search(r'var pages', script.text):
				matches = re.findall(r'"image":"(.*?)"', script.text)
				image_count = len(matches)
				for image_name, match in enumerate(matches, start=1):
					print_info("Download: Page {0:04d} / {1:04d}".format(image_name, image_count))
					image_url = 'http://dynasty-scans.com/' + match
					file_extension = re.search(r'.*\.([A-Za-z]*)', image_url).group(1)
					req = urllib.request.Request(image_url, headers={'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36', 'Accept-encoding': 'gzip'})

					try:
						response = urllib.request.urlopen(req)
					except urllib.error.HTTPError as e:
						print_info('WARNING: Unable to download file ({}).'.format(str(e)))
						warnings.append('Download of page {}, chapter {:g}, series "{}" failed.'.format(image_name, chapter["chapter"], self.series_info('title')))
						continue

					filename = '{}/{:06d}.{}'.format(download_directory, image_name, file_extension)
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
		headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36', 'Accept-encoding': 'gzip'}
		req = urllib.request.Request(url, headers=headers)
		response = urllib.request.urlopen(req)

		if response.info().get('Content-Encoding') == 'gzip':
			buf = io.BytesIO(response.read())
			data = gzip.GzipFile(fileobj=buf, mode="rb")
			return data
		else:
			return response.read()

	def series_chapters(self, all_chapters=False):
		logging.debug('Fetching series chapters')
		chapter_row = self.page.find("dl", class_="chapter-list").find_all("dd")
		chapters = []
		for chapter in chapter_row:
			chapters.append(self.chapter_info(chapter))

		# If the object was initialized with a chapter, only return the chapters.
		if self.init_with_chapter == True:
			logging.debug('Searching for specified chapter')
			for chapter in chapters:
				if re.match(self.url, chapter["url"]):
					logging.debug('Chapter found: ' + str(chapter))
					return [chapter]

		return sorted(chapters, key=lambda k: (type(k['chapter']) is str, k['chapter']), reverse=True)

	def series_info(self, search):
		def title():
			return self.page.find("h2", class_="tag-title").b.text.strip()

		def description():
			try:
				return self.page.find("div", class_="description").text
			except:
				return None

		def author():
			urls = self.page.find("h2", class_="tag-title").find_all('a', href=re.compile('authors'))
			author = ''
			for url in urls:
				if author == '':
					author = url.text
				else:
					author += ', ' + url.text
			return author

		options = {"title": title, "description": description, "author": author, "artist": author}
		return options[search]()
