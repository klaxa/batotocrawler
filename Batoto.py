#/usr/bin/python

from __main__ import print_info
from bs4 import BeautifulSoup
from Crawler import Crawler
import gzip
import io
import logging
import re
import urllib.request, urllib.error, urllib.parse

class Batoto(Crawler):
	uses_groups = True

	def __init__(self, url, server=None):
		self.url = url
		if server == None:
			self.server = None
		elif server in ['img1', 'img2', 'img3', 'img4']:
			self.server = server
		else:
			print_info('Invalid server selection.')
			self.server = None
		
		if re.match(r'.*bato\.to/comic/.*', url):
			self.page = BeautifulSoup(self.open_url(url))
			self.init_with_chapter = False
			logging.debug('Object initialized with series')
		elif re.match(r'.*bato\.to/read/.*', url):
			try:
				self.page = BeautifulSoup(self.open_url(self.chapter_series(url)))
			except IndexError:
				print_info('ERROR: Unable to scrape chapter \'{}\'. If this is a new release, please try again later (Batoto bug).'.format(self.url))
				self.page = None
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
		series_url = chapter.select('a[href*="bato.to/comic/_/"]')[0].get('href')
		logging.debug('Series URL: ' + series_url)
		return series_url

	# Returns a dictionary containing chapter number, chapter name and chapter URL.
	def chapter_info(self, chapter_data):
		logging.debug('Fetching chapter info')
		chapter = BeautifulSoup(str(chapter_data))
		chapter_url = chapter.a['href']
		chapter_number = re.search(r'Ch\.(.*?)[:\s].*', chapter.a.text).group(1)
		if re.match(r'^[0-9]*[Vv][0-9]*', chapter_number):
			chapter_number = re.search(r'^([0-9]*)[Vv][0-9]*', chapter_number).group(1)
		chapter_group = chapter.select('a[href*="bato.to/group/"]')[0].text
		
		try:
			chapter_number = float(chapter_number)
		except:
			pass

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

		logging.debug('Chapter number: {}'.format(chapter_number))
		logging.debug('Chapter name: ' + str(chapter_name))
		logging.debug('Chapter URL: ' + chapter_url)
		logging.debug('Chapter version: ' + chapter_version)
		logging.debug('Chapter group: ' + chapter_group)

		return {"chapter": chapter_number, "name": chapter_name, "url": chapter_url, "group": chapter_group, "version": int(chapter_version)}

	# Returns a list of chapter image URLs.
	def chapter_pages(self, chapter_url):
		logging.debug('Fetching chapter pages')
		chapter = BeautifulSoup(self.open_url(chapter_url))
		page_urls = chapter.find("select", {"name": "page_select"}).find_all("option")

		url_list = []
		for page in page_urls:
			url_list.append(page["value"])

		logging.debug('Chapter pages: ' + str(url_list))
		return url_list

	# Returns the image URL for the page.
	def chapter_images(self, chapter_url):
		logging.debug('Fetching chapter images')
		image_list = []

		try:
			pages = self.chapter_pages(chapter_url)
			logging.debug('Per page mode')

			for page_url in pages:
				page = BeautifulSoup(self.open_url(page_url))
				image_url = page.find("div", {"id": "full_image"}).find("img")["src"]
				image_list.append(image_url)
		except AttributeError:
			logging.debug('Long strip mode')
			page = BeautifulSoup(self.open_url(chapter_url))
			images = page.find_all('img', src=re.compile("img[0-9]*\.bato\.to/comics/.*/.*/.*/.*/read.*/"))
			
			for image in images:
				image_list.append(image['src'])

		logging.debug('Chapter images: ' + str(image_list))
		return image_list

	def download_chapter(self, chapter, download_directory, download_name):
		chapter_url = chapter["url"]
		logging.debug('Downloading chapter {}.'.format(chapter_url))
		chapter = BeautifulSoup(self.open_url(chapter_url))
		files = []
		warnings = []

		try:
			page_urls = chapter.find("select", {"name": "page_select"}).find_all("option")
			pages = [page["value"] for page in page_urls]
			logging.debug('Per page mode')
			image_count = len(pages)

			for image_name, page_url in enumerate(pages, start=1):
				print_info("Download: Page {0:04d} / {1:04d}".format(image_name, image_count))
				page = BeautifulSoup(self.open_url(page_url))
				url = page.find("div", {"id": "full_image"}).find("img")["src"]
				if self.server != None:
					url = 'http://{}.bato.to{}'.format(self.server, re.search(r'.*\.bato\.to(.*)', url).group(1))
				file_extension = re.search(r'.*\.([A-Za-z]*)', url).group(1)

				req = urllib.request.Request(url, headers={'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36', 'Accept-encoding': 'gzip'})
				try:
					logging.debug('Downloading img {}'.format(url))
					response = urllib.request.urlopen(req)
				except urllib.error.HTTPError as e:
					print_info('WARNING: Unable to download file ({}).'.format(str(e)))
					warnings.append('Download of page {}, chapter {:g}, series {} failed.'.format(image_name, chapter["chapter"], self.series_info('title')))

				filename = '{}/{:06d}.{}'.format(download_directory, image_name, file_extension)
				f = open(filename, 'wb')
				f.write(response.read())
				f.close()
				files.append(filename)
		except AttributeError:
			logging.debug('Long strip mode')
			page = BeautifulSoup(self.open_url(chapter_url))
			images = page.find_all('img', src=re.compile("img[0-9]*\.bato\.to/comics/.*/.*/.*/.*/read.*/"))
			image_count = len(images)

			for image_name, image in enumerate(images, start=1):
				print_info("Download: Page {0:04d} / {1:04d}".format(image_name, image_count))
				url = image['src']
				file_extension = re.search(r'.*\.([A-Za-z]*)', url).group(1)
				req = urllib.request.Request(url, headers={'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36', 'Accept-encoding': 'gzip'})

				try:
					response = urllib.request.urlopen(req)
				except urllib.error.HTTPError as e:
					print_info('WARNING: Unable to download file ({}).'.format(str(e)))
					warnings.append('Download of page {}, chapter {:g}, series "{}" failed.'.format(image_name, chapter["chapter"], series_info('title')))
					continue

				filename = '{}/{:06d}.{}'.format(download_directory, image_name, file_extension)
				f = open(filename, 'wb')
				f.write(response.read())
				f.close()
				files.append(filename)

		filename = download_directory + '/' + download_name
		self.zip_files(files, filename)

		return warnings

	# Function designed to create a request object with correct headers, open the URL and decompress it if it's gzipped.
	def open_url(self, url):
		logging.debug(url)
		headers={'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36', 'Accept-encoding': 'gzip'}
		req = urllib.request.Request(url, headers=headers)
		
		'''Loop to fetch the URL a maximum of 3 times. If X-Cache header value is 'HIT', loop is broken.
		If final attempt does not return 'HIT', error message with URL is printed to user.'''
		for i in range(3):
			response = urllib.request.urlopen(req)
			if response.info().get('X-Cache') == 'HIT':
				break
			if i == 2:
				print("ERROR: Unable to open " + response.geturl() + ".")

		if response.info().get('Content-Encoding') == 'gzip':
			buf = io.BytesIO(response.read())
			data = gzip.GzipFile(fileobj=buf, mode="rb")
			return data
		else:
			return reponse.read()

	def series_chapters(self, all_chapters=False):
		logging.debug('Fetching series chapters')
		chapter_row = self.page.find_all("tr", {"class": "row lang_English chapter_row"})
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

		logging.debug('Removing old versions')
		for num, chapter in enumerate(chapters):
			for chapter2 in chapters[num+1:]:
				if chapter["chapter"] == chapter2["chapter"]:
					if chapter["version"] > chapter2["version"]:
						logging.debug('Removing old version: ' + str(chapter2))
						chapters.remove(chapter2)
					elif chapter["version"] < chapter2["version"]:
						logging.debug('Removing old version: ' + str(chapter))
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
			return self.page.select('a[href*="bato.to/search?artist_name"]')[0].text.title()

		def artist():
			return self.page.select('a[href*="bato.to/search?artist_name"]')[1].text.title()

		options = {"title": title, "description": description, "author": author, "artist": artist}
		return options[search]()
