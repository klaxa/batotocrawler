#!/usr/bin/python

from Batoto import Batoto

#manga = Batoto(nisekoi_doc)
manga = Batoto("http://www.batoto.net/comic/_/comics/nisekoi-r951")

def print_info():
	print("Title:", manga.series_info("title"))
	print("Author:", manga.series_info("author"))
	print("Artist:", manga.series_info("artist"))
	print("Description:", manga.series_info("description"))

#print_info()
chapters = manga.series_chapters()
print(chapters)
for chapter in chapters:
	print(chapter["chapter"], chapter["name"], chapter["url"])
	print(manga.chapter_images(chapter["url"]))
