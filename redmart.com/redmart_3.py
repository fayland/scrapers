#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import csv
import requests
from bs4 import BeautifulSoup
import hashlib
import os.path
import re
import pprint
import html2text
import json

## config
CATEGORIES = [
	'food-cupboard', 'household', 'fresh-produce'
]

Bin = os.path.dirname(os.path.abspath(__file__))
pp = pprint.PrettyPrinter(indent=4)

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)'})

IS_save_html = True

def main():
	# create path if needed
	if IS_save_html and not os.path.exists(Bin + '/html_cache'):
		os.mkdir(Bin + '/html_cache')

	session_id = 'YTI4UGJveFNOUlRTc250OVFMOXJxUlQ2UE1WeUxTdWdFZ2lMVTJMb09XWUZmSmlaOTdhbzFhT2pCR3lYY2xqazUzZ0ZYN0Zhc1B0aUpHVTNvMzdZbExXWkRhQk13a3g1SXNSZnZraGlQTG89'
	apiConsumerId = '51f0af75-17f3-41df-b26c-1035dc18b7a3'

	base_url = 'https://redmart.com/product/'
	for CAT in CATEGORIES:
		csvwriter = csv.writer(open(CAT + '.csv', 'wb'))
		csvwriter.writerow(['NAME', 'PRICE', 'PRODUCT DESC', 'URL'])

		page = 1
		while True:
			param_page = page if page > 1 else 'null'
			url = 'https://api.redmart.com/v1.4.1/products/bycategory/?uri=' + CAT + '&page=' + str(param_page) + '&pageSize=20&instock=false&sort=null&session=' + session_id + '&apiConsumerId=' + apiConsumerId;

			c = get_url(url)
			data = json.loads(c)
			for product in data['products']:
				csvwriter.writerow([product['title'].encode('utf8'), product['pricing']['price'], product['desc'].encode('utf8'), base_url + product['details']['uri']])

			page = page + 1
			if 20 * page >= data['total']: break

def get_url(url):
	m5 = hashlib.new('md5', url).hexdigest()
	fn = Bin + "/html_cache/" + m5 + ".html"

	if os.path.exists(fn):
		print("[%s] # open %s for %s" % (os.getpid(), fn, url))
		fh = open(fn, 'r')
		content = fh.read()
		fh.close()
		if content.endswith('}'): return content

	print("[%s] # get %s to %s" % (os.getpid(), url, fn))
	tried_times = 0
	while True:
		res = None
		try:
			res = session.get(url, timeout=60)
		except BaseException as e:
			print(e)

		if not res or res.status_code > 200:
			tried_times = tried_times + 1
			if tried_times > 5:
				return # just skip it
			continue

		data = res.text.encode('utf8')
		if IS_save_html:
			fh = open(fn, 'w')
			fh.write(data)
			fh.close()

		return data

if __name__ == '__main__':
	main()