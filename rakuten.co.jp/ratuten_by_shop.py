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
import urllib

Bin = os.path.dirname(os.path.abspath(__file__))
pp = pprint.PrettyPrinter(indent=4)

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)'})

IS_save_html = True

def main():
	csvwriter = csv.writer(file('shop.csv', 'wb'))
	csvwriter.writerow(['BARCODE', 'INGREDIENTS', 'PRODUCT NAME', 'CATEGORY', 'IMAGE'])

	# create path if needed
	if IS_save_html and not os.path.exists(Bin + '/phtml'):
		os.mkdir(Bin + '/phtml')
	if not os.path.exists(Bin + '/uploads'):
		os.mkdir(Bin + '/uploads')

	DEBUG_BARCODE = None

	re_ingredients = [
		re.compile('原材料名</b>\s*<br/>\s*(.*?)\s*<br/>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料名】<br/>\s*(.*?)\s*</p>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料名】<br/>\s*(.*?)\s*<br/>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料名：\s*(.*?)\s*</span>\s*<br/>\s*<br/>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料名</td>\s*<td[^\>]*>\s*(.*?)\s*<hr/>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),

		re.compile('＜成分＞<br/>\s*(.*?)\s*<br/>\s*【'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),

		re.compile('原材料に含まれるアレルギー物質：?\s*(.*?)\s*</p>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料に含まれるアレルギー物質：?\s*</div><div[^\>]*>(.*?)\s*</div>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料</b>\s*<br/>\s*(.*?)\s*<br/>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料：\s*(.*?)\s*<br/>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料\S?\s*<br/>\s*(.*?)\s*<br/>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料</b>\s*<br/>\s*<br/>\s*<br/>\s*(.*?)<br/>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料</\w{2,3}>\s*<div[^\>]*>\s*(.*?)</div>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料\s*<br/>\s*(<table.*?</table>)'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料</b><br/><br/><br/>\s*(<table.*?</table>)'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
	]

	re_barcodes = [
		re.compile(r'JANコード：(\d{13}|\d{8})\b'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
	]

	url = "http://search.rakuten.co.jp/search/inshop-mall/-/-/sid.242246-st.A?x=35"
	c = get_url(url)

	page_now = 1
	while True:
		soup = BeautifulSoup(c)
		rsrSResultPhoto = soup.find_all('img', attrs={'src': re.compile('ex=96x96')})
		rsrSResultPhoto = map(lambda x: x.find_parent('a', attrs={'href': re.compile('http')}), rsrSResultPhoto)
		rsrSResultPhoto = filter(lambda x: x is not None, rsrSResultPhoto)
		rsrSResultPhoto = map(lambda x: x['href'], rsrSResultPhoto)

		if not rsrSResultPhoto:
			print '## CAN NOT FIND ANY RESULT RELATED TO ' + url
			break

		next_page = False
		pages = soup.find_all('a', attrs={'href': re.compile('-p.\d+-')})
		pages = filter(lambda x: x.get_text().strip() == str(page_now + 1), pages)
		if pages: next_page = pages[0]['href']
		page_now = page_now + 1
		# if page_now > 10: break

		to_fix = 0
		name, ingredients, image, matched_url = '', '', '', ''
		for in_url in rsrSResultPhoto:
			if 'http://item.rakuten.co.jp/book/' in in_url: continue

			print "\n\n"

			name, ingredients, image, matched_url = '', '', '', in_url
			c = get_url(in_url)
			if not c: continue # skip
			c.replace("<tr></font></td>", "</font></td>")

			soup = BeautifulSoup(c)
			cc = soup.decode_contents()

			barcode = ''
			for re_i in re_barcodes:
				m = re.search(re_i, cc)
				if m:
					barcode = m.group(1)

			if not barcode:
				barcode = soup.find('span', attrs={'class': 'item_number'})
				if barcode:
					barcode = barcode.get_text()
					barcode = re.sub('-(.*?)$', '', barcode)
					if (len(barcode) != 13 and len(barcode) != 8) or not barcode.isdigit():
						print "UNKNOWN barcode: " + barcode.encode('utf8')
						barcode = ''
			if not barcode:
				print "CAN NOT GET BARCODE FROM " + in_url
				continue
			print "get barcode as " + barcode.encode('utf8')

			for re_i in re_ingredients:
				m = re.search(re_i, cc)
				if m:
					tmptext = m.group(1).strip()
					soup2 = BeautifulSoup(tmptext)
					ingredients = soup2.get_text().strip()
					if len(ingredients) < 1000: break

			if '原材料'.decode('utf8') in cc and not ingredients:
				if DEBUG_BARCODE: print cc
				print "FIXME for " + in_url
				to_fix = 1

			if DEBUG_BARCODE: print ingredients

			if not len(name):
				name = soup.find('span', attrs={'class': 'content_title'})
				if name:
					name = name.get_text()
					name = re.sub('【\d+】'.decode('utf8'), '', name)

			image = soup.find('a', attrs={'class': re.compile('ImageMain')})
			if image and 'href' in image.attrs:
				image = image['href']
			elif image:
				image = image.find('img')
				if image:
					image = image['src']
					image = re.sub('\?.+$', '', image)

			category = soup.find('td', attrs={'class': 'sdtext'})
			if category: category = category.get_text().strip()

			if not ingredients:
				print 'no ingredients'
				continue

			if not image:
				print 'no image'
				continue # FIXME

			get_url(image, Bin + "/uploads/" + barcode + ".jpg");

			ingredients = ingredients.encode('utf8')
			ingredients = re.sub('\s+', ' ', ingredients).strip()
			name = name.encode('utf8')
			name = re.sub('\s+', ' ', name).strip()
			if not category: category = ''
			category = category.encode('utf8')
			category = re.sub('\s+', ' ', category).strip()
			csvwriter.writerow([barcode, ingredients, name, category, "uploads/" + barcode + ".jpg", matched_url])

		if not next_page: break # when it's an end
		print "### get next page: " + next_page
		c = get_url(next_page)

def get_url(url, image_file=None):
	fn = image_file
	if fn is None:
		m5 = md5.new(url).hexdigest()
		fn = Bin + "/phtml/" + m5 + ".html"

	if os.path.exists(fn):
		if image_file: return True

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

		if not image_file:
			data = res.text.encode(res.encoding)
			if IS_save_html:
				fh = open(fn, 'w')
				fh.write(data)
				fh.close()
		else:
			data = res.content
			fh = open(fn, 'wb')
			fh.write(data)
			fh.close()

		return data

if __name__ == '__main__':
	main()