#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import csv, time
import requests
import os.path

# import httplib
# httplib.HTTPConnection.debuglevel = 1

# import logging
# logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

Bin = os.path.dirname(os.path.abspath(__file__))

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)'})

def main():
	xtfile = sys.argv[1]

	if not os.path.exists(Bin + '/images'):
		os.mkdir(Bin + '/images')

	reader = csv.reader(file(xtfile, 'rb'))
	for line in reader:
		[barcode, image_url] = line
		if barcode == 'Jan' or image_url == 'Image': continue
		if not len(image_url): continue

		download_image(image_url, Bin + '/images/' + barcode + '.jpg')

def download_image(url, fn):
	if os.path.exists(fn):
		return True

	print "[%s] # get %s to %s" % (os.getpid(), url, fn);
	tried_times = 0
	while True:
		res = None
		try:
			res = session.get(url, timeout=60)
		except BaseException, e:
			print e

		time.sleep(2)
		if not res or res.status_code > 200:
			tried_times = tried_times + 1
			if tried_times > 5:
				return # just skip it
			continue

		fh = open(fn, 'wb')
		data = res.content
		fh.write(data)
		fh.close()
		break

if __name__ == '__main__':
	main()