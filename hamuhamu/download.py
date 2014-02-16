import os
import re
import urllib.request

def download_file(url, filename):
	file_extension = re.search(r'.*\.(.*)', url).group(1)
	filename = os.getcwd() + "/" + str(filename) + "." + file_extension

	req = urllib.request.Request(url, headers={'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36', 'Accept-encoding': 'gzip'})
	response = urllib.request.urlopen(req)

	if os.path.isfile(filename):
		print("TEMPORARY DEBUG MESSAGE: File exists.")
		if os.stat(filename).st_size == int(response.info().get('Content-Length')):
			print("TEMPORARY DEBUG MESSAGE: File complete. Skip.")
			return
		else:
			print("TEMPORARY DEBUG MESSAGE: File incomplete. Download.")
			f = open(filename, 'wb')
			f.write(response.read())
			f.close()
	else:
		print("TEMPORARY DEBUG MESSAGE: File doesn't exist. Download.")
		f = open(filename, 'wb')
		f.write(response.read())
		f.close()

image_list = ["http://stallman.org/rms.jpg", "http://stallman.org/rms-by-simon.png", "http://stallman.org/image001.jpg"]

for image_name, image_url in enumerate(image_list, start=1):
	print(image_url, image_name)
	download_file(image_url, "{0:04d}".format(image_name))