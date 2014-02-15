#!/usr/bin/python

import sys
import threading
import re
import urllib.request
import time
import os
import queue
import io
import gzip
import html.parser
import traceback
from multiprocessing import Pool
import zipfile

if len(sys.argv) < 2:
	print("No u!")
	sys.exit(0)

LOGLEVEL = 4

DEBUG = 5
INFO = 4

THREADS = 10


def debug(message):
	if LOGLEVEL >= DEBUG:
		print("D: " + message)

def info(message):
	if LOGLEVEL >= INFO:
		print("I: " + message)

def zipdir(path, zipf):
	for root, dirs, files in os.walk(path):
		for file in files:
			zipf.write(os.path.join(root, file))
def deltree(path):
	for root, dirs, files in os.walk(path, topdown=False):
		for name in files:
			os.remove(os.path.join(root, name))
		for name in dirs:
			os.rmdir(os.path.join(root, name))
	os.rmdir(path)
def get_directory_size(folder):
	total_size = os.path.getsize(folder)
	for item in os.listdir(folder):
		itempath = os.path.join(folder, item)
		if os.path.isfile(itempath):
			total_size += os.path.getsize(itempath)
		elif os.path.isdir(itempath):
			total_size += get_directory_size(itempath)
	return total_size
def decompress(data):
	try:
		data = gzip.decompress(data)
		debug("File was gzip'd")
	except:
		debug("File was not gzip'd")
	return data

def download_to_file(url, filename):
	if os.path.isfile(filename) and os.path.getsize(filename) > 0:
		info("Not overwriting " + filename)
		return
	elif os.path.isfile(filename) and os.path.getsize(filename) == 0:
		info("Overwriting empty file " + filename)
	download_file = open(filename, "wb")			
	now = time.time()
	result = decompress(urllib.request.urlopen(url).read())
	download_file.write(result)
	downloaded = time.time()
	size = os.path.getsize(filename)
	info("Downloaded file %s; %d kBytes in %f seconds (%f kB/s)." % (url, int(size/1024), downloaded - now, int(size/1024) / (downloaded - now)))
	return

def download(url):
	return decompress(urllib.request.urlopen(url).read()).decode('utf-8')

def download_batoto_page(url, path, page_num):
	debug("Initiating download of " + url)
	if not os.path.exists(path):
		os.makedirs(path)
		debug("Created directory " + path + " for downloads.")
	data = download(url)
	for line in data.split("\n"):
		if re.match(".*src=\"http://img.batoto.net/.*read.*", line):
			image = re.findall("http[^\"]*", line)[0]
			filename = "%s/%04d.%s" % (path, page_num, re.sub(".*\.", "", image)) # batoto can't into ordering
			debug("Downloading image " + image + " to " + filename + ".")
			download_to_file(image, filename)
			return
			
			
def download_batoto_chapter(chapter_url, chapter_count, title):
	debug("Downloading chapter " + chapter_url)
	chapter = download(chapter_url)
	no_pages = True
	for line in chapter.split("\n"):
		if re.match(".*<option.*page.*</option>.*", line) and no_pages:
			no_pages = False
			pages = []
			for page in re.findall("http[^\"]*", line):
				pages.append(page)
			debug("Chapter " + str(chapter_count) + " has " + str(len(pages)) + " pages.")
			page_num = 0
			for page in pages:
				debug("Initiating download of " + chapter_url)
				try:
					download_batoto_page(page, "%s/%02d" % (title, chapter_count), page_num)
				except BaseException as e:
					print(traceback.format_exc())
				page_num += 1
def main():
	if __name__ == '__main__':
		info("Starting!")
		debug("Creating thread pool")
		parser = html.parser.HTMLParser()
		thread_pool = Pool(processes=THREADS)
		base_url = sys.argv[1]
		title = ""
		debug("Downloading main page")
		debug("Filename: " + re.sub(".*/", "", base_url))
		chapters = []
		start_time = time.time()
		main_page = download(base_url)
		check_for_link = False
		check_for_title = False
		for line in main_page.split("\n"):
			if check_for_title:
				if re.match(".*</h1>.*", line):
					debug("Title is: " + title)
					check_for_title = False
				else:
					title = parser.unescape(line.strip())
			if check_for_link and re.match(".*http://www.batoto.net/read/.*", line):
				chapter = re.findall("http[^\"]*", line)[0]
				chapters.append(chapter)
				debug("Added chapter " + chapter + " to download list.")
			if re.match(".*class=\"row lang_English chapter_row\".*", line):
				check_for_link = True
			elif re.match(".*class=\"row lang_.*", line):
				check_for_link = False
			elif re.match(".*ipsType_pagetitle.*", line):
				check_for_title = True
		chapter_count = 0
		while chapters:
			debug("Adding chapter to download queue (" + str(chapter_count) + ")")
			thread_pool.apply_async(download_batoto_chapter, (chapters.pop(), chapter_count,title,))
			chapter_count += 1
		debug("Done adding chapters! Waiting for Threadpool to finish...")
		thread_pool.close()
		thread_pool.join()
		finish_time = time.time()
		size = get_directory_size(title)
		debug("Threadpool finished!")
		info("Downloaded %d kBytes in %f seconds (%f kB/s)." % (int(size/1024), finish_time - start_time, int(size/1024) / (finish_time - start_time)))
		info("Creating zip...")
		zipf = zipfile.ZipFile(title + ".zip", 'w')
		zipdir(title, zipf)
		zipf.close()
		info("Deleting temporary directory...")
		deltree(title)
		info("Done!")
main()
