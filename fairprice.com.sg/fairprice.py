#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import csv
import requests
from bs4 import BeautifulSoup
import md5
import os.path
import re
import pprint
import html2text

## config
CATEGORY_URLS = {
	'heathy': 'http://www.fairprice.com.sg/webapp/wcs/stores/servlet/CategoryDisplay?storeId=10001&beginIndex=0&urlRequestType=Base&categoryId=13508&pageView=grid&catalogId=10051&langId=-1',
	'beverages': 'http://www.fairprice.com.sg/webapp/wcs/stores/servlet/CategoryDisplay?storeId=10001&beginIndex=0&urlRequestType=Base&categoryId=13502&pageView=grid&catalogId=10051&langId=-1',
	'baby': 'http://www.fairprice.com.sg/webapp/wcs/stores/servlet/CategoryDisplay?storeId=10001&beginIndex=0&urlRequestType=Base&categoryId=13506&pageView=grid&catalogId=10051&langId=-1',
	'bear': 'http://www.fairprice.com.sg/webapp/wcs/stores/servlet/CategoryDisplay?storeId=10001&beginIndex=0&urlRequestType=Base&categoryId=13503&pageView=grid&catalogId=10051&langId=-1'
}

Bin = os.path.dirname(os.path.abspath(__file__))
pp = pprint.PrettyPrinter(indent=4)

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)'})

IS_save_html = True

def main():
	# create path if needed
	if IS_save_html and not os.path.exists(Bin + '/html_cache'):
		os.mkdir(Bin + '/html_cache')

	for cat_name, url in CATEGORY_URLS.items():
		curr_page = 1

		csvwriter = csv.writer(file(cat_name + '.csv', 'wb'))
		csvwriter.writerow(['NAME', 'PRICE', 'PRODUCT DESC', 'URL'])

		while True:
			c = get_url(url)
			if 'The page you are looking for cannot be found' in c: break
			soup = BeautifulSoup(c)

			product_urls = soup.find_all('a', attrs={'id': re.compile('catalogEntry_img')})
			product_urls = map(lambda x: x['href'], product_urls)

			for in_url in product_urls:
				c = get_url(in_url)
				soup = BeautifulSoup(c)

				prodn_txt_wrp = soup.find('div', attrs={'class': 'prodn_txt_wrp'})
				name = prodn_txt_wrp.find('h1').get_text().strip()
				price = prodn_txt_wrp.find('p', attrs={'class': 'disc_price'}).get_text().strip()
				desc = soup.find('div', attrs={'class': 'product_det_desc_wrpr'})
				desc.find('script').clear() # remove script tag
				desc = html2text.html2text(desc.prettify()).strip()
				desc = desc.replace('###  Product Description', '').replace("\n\n", "\n").strip()

				csvwriter.writerow([name.encode('utf8'), price, desc.encode('utf8'), in_url])

			beginIndex = curr_page * 24
			curr_page  = curr_page + 1
			url = re.sub('beginIndex=\d+', 'beginIndex=' + str(beginIndex), url)

def get_url(url):
	m5 = md5.new(url).hexdigest()
	fn = Bin + "/html_cache/" + m5 + ".html"

	if os.path.exists(fn):
		print "[%s] # open %s for %s" % (os.getpid(), fn, url);
		fh = open(fn, 'r')
		content = fh.read()
		fh.close()
		if '</html>' in content: return content

	print "[%s] # get %s to %s" % (os.getpid(), url, fn);
	tried_times = 0
	while True:
		res = None
		try:
			res = session.get(url, timeout=60)
		except BaseException, e:
			print e

		if not res or res.status_code > 200:
			tried_times = tried_times + 1
			if tried_times > 5:
				return # just skip it
			continue

		data = res.text.encode(res.encoding)
		if IS_save_html:
			fh = open(fn, 'w')
			fh.write(data)
			fh.close()

		return data

if __name__ == '__main__':
	main()