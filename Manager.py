#!/usr/bin/python

import logging
import getopt
import os
import os.path
import re
import sys
import urllib.request
import zipfile

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(module)s: %(funcName)s: %(msg)s')

def print_info(message, newline=True):
	if not 'silent_mode' in globals():
		if newline == False:
			print(message, end="")
		else:
			print(message)

def download_file(url, filename):
	file_extension = re.search(r'.*\.([A-Za-z]*)', url).group(1)
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
	if 'cbz_mode' in globals():
		file_extension = ".cbz"
	else:
		file_extension = ".zip"

	filename = os.getcwd() + "/" + filename + file_extension
	zipf = zipfile.ZipFile(filename, mode="w")
	for f in filelist:
		zipf.write(f, os.path.basename(f))
		os.remove(f)
	print_info("Zip created: " + filename.replace(os.environ['HOME'], "~"))

def duplicate_chapters(chapters):
	numbers = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]

	def print_initial():
		if len(duplicates) > 9:
			number_of_releases = len(duplicates)
		else:
			number_of_releases = numbers[len(duplicates)]

		if manga.uses_groups:
			print_info("{} releases for chapter {}: ".format(number_of_releases, duplicates[0]["chapter"]), newline=False)
			for item in duplicates[:-1]:		
				print_info("{}, ".format(item["group"]), newline=False)
			print_info("{}.".format(duplicates[-1]["group"]))
		else:
			print_info("{} releases for chapter {}".format(number_of_releases, duplicates[0]["chapter"]))

	def no_preference():
		print_initial()

		if manga.uses_groups:
			print_info("No preference set. Picking {} for chapter {}.".format(duplicates[0]["group"], chapter["chapter"]))
		else:
			print_info("No preference set. Picking latter chapter.")

		for item in duplicates[1:]:
			chapters.remove(item)

	def preference(group):
		print_initial()

		for item in duplicates:
			if item["group"] == group:
				print_info("Preference: {}. Picking {} for chapter {}.".format(group, item["group"], item["chapter"]))
				duplicates.remove(item)
				for item in duplicates:
					chapters.remove(item)
				return

		print_info("Preference: {}. Not found. Picking {} for chapter {}.".format(group, duplicates[-1]["group"], duplicates[-1]["chapter"]))
		for item in duplicates[:-1]:
			chapters.remove(item)

	def interactive():
		print_initial()

		for num, item in enumerate(duplicates, start=1):
			if manga.uses_groups:
				print("{}. {}".format(num, item["group"]))
			else:
				print("{}. Release {}".format(num, num))

		# Try to delete the given item from the duplicates list. Loops until a valid item is entered.
		while(True):
			choice = input('>> ')
			try:
				if manga.uses_groups:
					print_info("Picking {} for chapter {}.".format(duplicates[int(choice)-1]["group"], duplicates[int(choice)-1]["chapter"]))
				else:
					print_info("Picking release {} for chapter {}.".format(int(choice), duplicates[int(choice)-1]["chapter"]))
				del duplicates[int(choice)-1]
				break
			except:
				print("Invalid input.")

		# Deletes all the chapters that are in the duplicates list from the chapter list, since the version to keep is no longer on that list.
		for item in duplicates:
			chapters.remove(item)

	logging.debug('Searching duplicate chapters')
	for num, chapter in enumerate(chapters):
		duplicates = [chapter]
		for chapter2 in chapters[num+1:]:
			if chapter["chapter"] == chapter2["chapter"]:
				duplicates.append(chapter2)
		if len(duplicates) > 1:
			if 'interactive_mode' in globals():
				interactive()
			elif 'group_preference' in globals():
				if manga.uses_groups:
					preference(group_preference)
				else:
					logging.debug('Unable to use group preference with site: using no_preference as fallback')
					no_preference()
			else:
				no_preference()
	logging.debug('Duplicate chapter search finished')

def read_config():
	config_file = os.environ['HOME'] + '/.config/batotocrawler.conf'
	config_data = []

	# Open the config file for reading, go through it line by line and if line doesn't start with #, add it as a arg.
	if os.path.isfile(config_file):
		with open(config_file, 'r') as f:
			for line in f:
				if line[0] != '#':
					config_data += line.split()

	return config_data

# Combine the config file and command-line arguments and split them into options and arguments.
user_config = read_config()
arguments = user_config + sys.argv[1:]
optlist, args = getopt.getopt(arguments, 'qs:e:', ['prefer-group=', 'interactive', 'quiet', 'debug', 'cbz'])

# If there are options provided, declare the applicable variables with values.
if len(optlist) > 0:
	for opt, arg in optlist:
		if opt == "-s":
			chapters_start = arg
		elif opt == "-e":
			chapters_end = arg
		elif opt == "-q":
			silent_mode = True
		elif opt == "--quiet":
			silent_mode = True
		elif opt == "--debug":
			logging.getLogger().setLevel(logging.DEBUG)
		elif opt == "--interactive":
			interactive_mode = True
		elif opt == "--prefer-group":
			group_preference = arg
		elif opt == "--cbz":
			cbz_mode = True

logging.debug('User config: ' + str(user_config))
logging.debug('Command-line args: ' + str(sys.argv[1:]))

# If there are no arguments provided, ask user for input. If there is more than one argument, reject input. Otherwise use the input as the URL.
if len(args) == 0:
	url = input('>> ')
elif len(args) > 1:
	print_info("Too many args.")
	exit()
else:
	url = sys.argv.pop()

# Intializes the manga object if the URL is valid and has a scraper.
if re.match(r'.*batoto\.net/.*', url):
	logging.debug('URL match: Batoto')
	from Batoto import Batoto
	manga = Batoto(url)
elif re.match(r'.*kissmanga\.com/manga/.*', url, flags=re.IGNORECASE):
	logging.debug('URL match: KissManga')
	from KissManga import KissManga
	manga = KissManga(url)
else:
	print_info("Invalid input.")
	exit()

# Print a warning if the user tries to specify --prefer-group with a site that doesn't use group names.
if manga.uses_groups == False and 'group_preference' in globals():
	print_info("WARNING: Unable to use '--prefer-group' with {}.".format(manga.__class__.__name__))

chapters = manga.series_chapters()
if len(chapters) > 1:
	duplicate_chapters(chapters)

'''If there is a end variable declared and more than one chapter,
look for it by comparing it chapter["chapter"] strings. If the string
isn't found or no start variable is declared, iteration is started from 0.'''
if 'chapters_start' in locals() and len(chapters) > 1:
	start_num = -1
	for num, chapter in enumerate(chapters):
		if chapters_start == chapter["chapter"]:
			print_info("Starting download at chapter " + chapter["chapter"])
			start_num = num
			break
	if start_num == -1:
		print_info("Defined starting chapter not found. Starting from chapter " + chapters[-1]["chapter"] + ".")
else:
	start_num = -1

'''If there is a end variable declared and more than one chapter,
look for it by comparing it chapter["chapter"] strings. If the string
isn't found or no end variable is declared, iteration is done to list end.'''
if 'chapters_end' in locals() and len(chapters) > 1:
	end_num = None
	for num, chapter in enumerate(chapters):
		if chapters_end == chapter["chapter"]:
			print_info("Ending download at chapter " + chapter["chapter"])
			end_num = num - 1
			break
	if end_num == None:
		print_info("Defined end chapter not found. Ending at chapter " + chapters[0]["chapter"] + ".")
else:
	end_num = None

for chapter in chapters[start_num:end_num:-1]:
	if chapter["name"] != None:
		print_info("Chapter " + chapter["chapter"] + " - " + chapter["name"])
	else:
		print_info("Chapter " + chapter["chapter"])

	clean_title = clean_filename(manga.series_info("title"))
	image_list = manga.chapter_images(chapter["url"])
	image_count = len(image_list)
	file_list = []

	for image_name, image_url in enumerate(image_list, start=1):
		print_info("Download: Page {0:04d}".format(image_name) + " / {0:04d}".format(image_count))
		downloaded_file = download_file(image_url, "{0:04d}".format(image_name))
		file_list.append(downloaded_file)

	'''If the "chapter number" string contains a floating point number, the integer part is padded to four digits and the decimal part is added to it.
	If the "chapter number" contains only numbers, it is padded to four digits.
	If the "chapter number" is something else (like 'extra'), it is not padded. Also, the '_c' prefix is omitted.'''
	if re.match(r'[0-9]*\.[0-9]*', chapter["chapter"]):
		zip_files(file_list, clean_title + "_c" + re.search(r'(.*)\.(.*)', chapter["chapter"]).group(1).zfill(4) + "." + re.search(r'(.*)\.(.*)', chapter["chapter"]).group(2))
	elif re.match(r'^[0-9]', chapter["chapter"]):
		zip_files(file_list, clean_title + "_c" + chapter["chapter"].zfill(4) + ".0")
	else:
		zip_files(file_list, clean_title + "_" + chapter["chapter"])
