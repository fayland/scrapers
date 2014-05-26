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

Bin = os.path.dirname(os.path.abspath(__file__))
pp = pprint.PrettyPrinter(indent=4)

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)'})

def main():
	csvwriter = csv.writer(file('pdata.csv', 'wb'))
	csvwriter.writerow(['BARCODE', 'INGREDIENTS', 'PRODUCT NAME', 'IMAGE'])

	# create path if needed
	if not os.path.exists(Bin + '/phtml'):
		os.mkdir(Bin + '/phtml')

	DEBUG_BARCODE = None

	re_ingredients = [
		re.compile('原材料</b>\s*<br/>\s*(.*?)\s*<br/>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料名</b>\s*<br/>\s*(.*?)\s*<br/>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料：\s*(.*?)\s*<br/>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料】<br/>\s*(.*?)\s*<br/>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料名】<br/>\s*(.*?)\s*</p>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料名】<br/>\s*(.*?)\s*<br/>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料</b>\s*<br/>\s*<br/>\s*<br/>\s*(.*?)<br/>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料</\w{2,3}>\s*<div[^\>]*>\s*(.*?)</div>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料\s*<br/>\s*(<table.*?</table>)'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料名</td>\s*<td[^\>]*>\s*(.*?)\s*<hr/>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料</b><br/><br/><br/>\s*(<table.*?</table>)'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料に含まれるアレルギー物質：?\s*(.*?)\s*</p>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
		re.compile('原材料に含まれるアレルギー物質：?\s*</div><div[^\>]*>(.*?)\s*</div>'.decode('utf8'), re.I|re.DOTALL|re.MULTILINE),
	]

	txtfile = sys.argv[1]
	fh = open(txtfile, 'r')
	while True:
		barcode = fh.readline()
		if not barcode: break
		barcode = barcode.strip()
		if barcode == 'Barcode': continue
		if DEBUG_BARCODE and barcode != DEBUG_BARCODE: continue

		print "\n\n"

		url = "http://search.rakuten.co.jp/search/mall?sitem=" + barcode + "&g=0&myButton.x=0&myButton.y=0&v=2&s=1&p=1&min=&max=&sf=0&st=A&nitem=&grp=product";
		c = get_url(url)
		soup = BeautifulSoup(c)
		rsrSResultPhoto = soup.find_all('div', attrs={'class': 'rsrSResultPhoto'})
		rsrSResultPhoto = map(lambda x: x.find('a', attrs={'href': re.compile('http')}), rsrSResultPhoto)
		rsrSResultPhoto = filter(lambda x: x is not None, rsrSResultPhoto)
		rsrSResultPhoto = map(lambda x: x['href'], rsrSResultPhoto)

		if not rsrSResultPhoto:
			print '## MISSING results for ' + barcode
			continue

		to_fix = 0
		name, ingredients, image, matched_url = '', '', '', ''
		for in_url in rsrSResultPhoto:
			if 'http://item.rakuten.co.jp/book/' in in_url: continue
			if 'rakuten.co.jp/doremi/' in in_url: continue # skip BAD
			if 'rakuten.co.jp/at-life/' in in_url: continue

			name, ingredients, image, matched_url = '', '', '', in_url
			c = get_url(in_url)
			if not c: continue # skip
			c.replace("<tr></font></td>", "</font></td>")

			soup = BeautifulSoup(c)
			trs = soup.find_all('tr')
			while True:
				if not len(trs): break
				tr = trs.pop(0)
				__trs = tr.find_all('tr')
				if len(__trs): continue

				tds = tr.find_all(re.compile("^t[dh]$"))
				tds = map(lambda x: x.get_text().strip(), tds)
				tds = filter(lambda x: len(x), tds)
				if not len(tds): continue

				if tds[0] == '商品名'.decode('utf8'):
					if len(tds) > 1: name = tds[1]
				elif tds[0].endswith('原材料'.decode('utf8')) and len(tds) <= 2:
					if len(tds) > 1:
						ingredients = tds[1]
					else:
						ingredients = trs.pop(0).get_text().strip()
				elif (
						len(tds[0]) < 50 and ('原材料'.decode('utf8') in tds[0] or ('成分'.decode('utf8') in tds[0] and '栄養成分'.decode('utf8') not in tds[0]))
					) or (
						tds[0].endswith('原材料'.decode('utf8'))
					):
					if not ingredients:
						if len(tds) > 1:
							ingredients = tds[1]
						else:
							ingredients = trs.pop(0).get_text().strip()
				# remove BAD for next choice
				if 'item.rakuten.co.jp' in ingredients or 'iframe' in ingredients or len(ingredients) > 1000:
					ingredients = ''

			cc = soup.decode_contents()
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

			if name and ingredients: break

		if not image:
			print 'no image'
			continue # FIXME
			sys.exit(1)
		if not name:
			print 'no name'
			sys.exit(1)
		if not ingredients:
			print 'no ingredients'
			if to_fix:
				print "REAL FIXME: " + barcode
			continue ## FIXME
			sys.exit(1)

		get_url(image, Bin + "/uploads/" + barcode + ".jpg");

		ingredients = ingredients.encode('utf8')
		ingredients = re.sub('\s+', ' ', ingredients).strip()
		name = name.encode('utf8')
		name = re.sub('\s+', ' ', name).strip()
		csvwriter.writerow([barcode, ingredients, name, "uploads/" + barcode + ".jpg", matched_url])

	fh.close()

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

		fh = open(fn, 'w')
		data = res.content
		if not image_file:
			data = res.text.encode(res.encoding)
		fh.write(data)
		fh.close()

		return data

if __name__ == '__main__':
	main()