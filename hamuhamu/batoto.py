from bs4 import BeautifulSoup
import gzip
import re
import StringIO
import urllib2

class Batoto(object):
	def __init__(self, url):
		if url == None:
			self.page = None
		else:
			self.page = BeautifulSoup(self.open_url(url))

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

	# Function designed to create a request object with correct headers and decompress it if needed.
	def open_url(self, url):
		req = urllib2.Request(url, headers={'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36', 'Accept-encoding': 'gzip'})
		response = urllib2.urlopen(req)
		if response.info().get('Content-Encoding') == 'gzip':
			buf = StringIO.StringIO(response.read())
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

#manga = Batoto(nisekoi_doc)
manga = Batoto("http://www.batoto.net/comic/_/comics/nisekoi-r951")

def print_info():
	print "Title:", manga.series_info("title")
	print "Author:", manga.series_info("author")
	print "Artist:", manga.series_info("artist")
	print "Description:", manga.series_info("description")

#print_info()
chapters = manga.series_chapters()
print chapters
for chapter in chapters:
	print chapter["chapter"], chapter["name"], chapter["url"]
	print manga.chapter_images(chapter["url"])