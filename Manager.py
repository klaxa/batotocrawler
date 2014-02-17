#!/usr/bin/python

import getopt
import os
import re
import sys
import urllib.request
import zipfile
from Batoto import Batoto

def download_file(url, filename):
	file_extension = re.search(r'.*\.(.*)', url).group(1)
	filename = os.getcwd() + "/" + str(filename) + "." + file_extension

	req = urllib.request.Request(url, headers={'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36', 'Accept-encoding': 'gzip'})
	response = urllib.request.urlopen(req)

	f = open(filename, 'wb')
	f.write(response.read())
	f.close()

	return filename

def clean_filename(filename):
	filename = re.sub('[/:;|]', '', filename)
	filename = re.sub('[\s]+', '_', filename)
	filename = re.sub('__', '_', filename)
	return filename

def zip_files(filelist, filename):
	filename = os.getcwd() + "/" + filename + ".zip"
	zipf = zipfile.ZipFile(filename, mode="w")
	for f in filelist:
		zipf.write(f, os.path.basename(f))
		os.remove(f)
	print("Zip created: " + filename)

optlist, args = getopt.getopt(sys.argv[1:], 's:e:')

# If there are options provided, declare the applicable variables with values.
if len(optlist) > 0:
	for opt, arg in optlist:
		if opt == "-s":
			chapters_start = arg
		elif opt == "-e":
			chapters_end = arg

# If there are no arguments provided, ask user for input. If there is more than one argument, reject input. Otherwise use the input as the URL.
if len(args) == 0:
	url = input('>> ')
elif len(args) > 1:
	print("Too many args.")
	exit()
else:
	url = sys.argv.pop()

manga = Batoto(url)
chapters = manga.series_chapters()

'''If there is a start variable declared, look for it by comparing it chapter["chapter"] strings.
If the string isn't found or no start variable is declared, iteration is started from 0.'''
if 'chapters_start' in locals():
	start_num = -1
	for num, chapter in enumerate(chapters): 
		if chapters_start == chapter["chapter"]:
			print("Starting download at chapter " + chapter["chapter"])
			start_num = num
	if start_num == -1:
		print("Defined starting chapter not found. Starting from chapter " + chapters[-1]["chapter"] + ".")
else:
	start_num = -1

'''If there is a end variable declared, look for it by comparing it chapter["chapter"] strings.
If the string isn't found or no end variable is declared, iteration is done to list end.'''
if 'chapters_end' in locals():
	end_num = None
	for num, chapter in enumerate(chapters): 
		if chapters_end == chapter["chapter"]:
			print("Ending download at chapter " + chapter["chapter"])
			end_num = num - 1
	if end_num == None:
		print("Defined end chapter not found. Ending at chapter " + chapters[0]["chapter"] + ".")
else:
	end_num = None

for chapter in chapters[start_num:end_num:-1]:
	if chapter["name"] != None:
		print("Chapter " + chapter["chapter"] + " - " + chapter["name"])
	else:
		print("Chapter " + chapter["chapter"])

	clean_title = clean_filename(manga.series_info("title"))
	image_list = manga.chapter_images(chapter["url"])
	file_list = []

	for image_name, image_url in enumerate(image_list, start=1):
		print("Download: Page " + "{0:04d}".format(image_name))
		downloaded_file = download_file(image_url, "{0:04d}".format(image_name))
		file_list.append(downloaded_file)

	'''If the "chapter number" string contains a floating point number, the integer part is padded to four digits and the decimal part is added to it.
	If the "chapter number" contains only numbers, it is padded to four digits.
	If the "chapter number" is something else (like 'extra'), it is not padded. Also, the '_c' prefix is omitted.'''
	if re.match(r'[0-9]*\.[0-9]*', chapter["chapter"]):
		zip_files(file_list, clean_title + "_c" + re.search(r'(.*)\.(.*)', chapter["chapter"]).group(1).zfill(4) + "." + re.search(r'(.*)\.(.*)', chapter["chapter"]).group(2))
	elif re.match(r'^[0-9]', chapter["chapter"]):
		zip_files(file_list, clean_title + "_c" + chapter["chapter"].zfill(4))
	else:
		zip_files(file_list, clean_title + "_" + chapter["chapter"])