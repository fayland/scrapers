#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import csv
import requests
from bs4 import BeautifulSoup
import md5, time, pickle
import os.path
import re
import pprint
import urllib

Bin = os.path.dirname(os.path.abspath(__file__))
pp = pprint.PrettyPrinter(indent=4)

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)'})
# session.proxies = {'http': 'socks5://127.0.0.1:9050',
#                    'https': 'socks5://127.0.0.1:9050'}

def main():
	# create path if needed
	if not os.path.exists(Bin + '/html'):
		os.mkdir(Bin + '/html')

	all_r_links = []
	all_m_links = []
	all_mo_links = []
	scraped_links = {}

	# do not loop through files b/c it takes time
	pickle_file = Bin + '/links.pickle'
	if os.path.exists(pickle_file):
		pkl_file = open(pickle_file, 'rb')
		data = pickle.load(pkl_file)
		all_r_links = data['all_r_links']
		all_m_links = data['all_m_links']
		all_mo_links = data['all_mo_links']
	else:
		c = get_url("http://www.zabihah.com/beta")
		soup = BeautifulSoup(c)
		regLinks = soup.find_all('a', attrs={'href': re.compile('/reg/')})
		regLinks = map(lambda x: x['href'], regLinks)
		while True:
			if not len(regLinks): break
			regLink = regLinks.pop(0)
			if regLink in scraped_links: continue
			scraped_links[regLink] = 1
			c = get_url("http://www.zabihah.com" + regLink)

			soup = BeautifulSoup(c)
			tables = soup.find_all('table', attrs={'cellpadding': 0, 'cellspacing': 0, 'border': 0, 'width': 800})
			for table in tables:
				inRegLinks = table.find_all('a', attrs={'href': re.compile('/reg/')})
				inRegLinks = map(lambda x: x['href'], inRegLinks)
				inSubLinks = table.find_all('a', attrs={'href': re.compile('/sub/')})
				inSubLinks = map(lambda x: x['href'], inSubLinks)
				if inRegLinks: regLinks = inRegLinks + regLinks
				if inSubLinks: regLinks = inSubLinks + regLinks

			titleBS = soup.find_all('div', attrs={'class': 'titleBS'})
			titleBS = map(lambda x: x.find('a', attrs={'href': re.compile('/biz/')}), titleBS)
			titleBS = map(lambda x: x['href'], titleBS)
			if titleBS: all_r_links = all_r_links + titleBS

			mosque_link = soup.find('a', attrs={'href': re.compile('salatomatic.com')})
			if mosque_link and 'NO MOSQUES' not in c:
				all_mo_links = all_mo_links + [mosque_link['href']]

			market_link = soup.find('a', attrs={'href': re.compile('t=m')})
			if market_link and 'NO MARKETS' not in c:
				c = get_url("http://www.zabihah.com" + market_link['href'])

				soup = BeautifulSoup(c)
				titleBS = soup.find_all('div', attrs={'class': 'titleBS'})
				titleBS = map(lambda x: x.find('a', attrs={'href': re.compile('/biz/')}), titleBS)
				titleBS = map(lambda x: x['href'], titleBS)
				if titleBS: all_m_links = all_m_links + titleBS

			# if len(all_r_links) > 10: break

		# save for next run
		data = {
			'all_r_links': all_r_links,
			'all_m_links': all_m_links,
			'all_mo_links': all_mo_links
		}
		pkl_file = open(pickle_file, 'wb')
		pickle.dump(data, pkl_file)

	is_market = {}
	for link in all_m_links:
		is_market[link] = 1

	csvwriter = csv.writer(file('data.csv', 'wb'))
	csvwriter.writerow(['NAME', 'ADDRESS', 'TYPE', 'PLACE', 'URL'])

	total = len(all_r_links) + len(all_m_links)
	i = 0
	scraped_links = {}
	for r_link in all_r_links + all_m_links:
		if r_link in scraped_links: continue
		scraped_links[r_link] = 1
		i = i + 1
		print "[%s/%s] " % (str(i), str(total))
		c = get_url("http://www.zabihah.com" + r_link)
		if not c:
			print "NO CONTENT FOUND."
			continue

		soup = BeautifulSoup(c)
		title = soup.find('div', attrs={'class': 'titleBL'})
		if not title:
			print "NO TITLE FOUND."
			continue
		title = title.get_text().strip()
		address = soup.find('div', attrs={'class': 'bodyLink'}).get_text().strip()
		z3_fg = soup.find_all('div', attrs={'class': 'z3_fg'})
		z3_fg = map(lambda x: x.find('a'), z3_fg)
		z3_fg = filter(lambda x: x is not None, z3_fg)
		z3_fg = map(lambda x: x.get_text(), z3_fg)
		place = ' / '.join(z3_fg)

		title = title.encode('utf8')
		title = re.sub('\s+', ' ', title).strip()
		address = address.encode('utf8')
		address = re.sub('\s+', ' ', address).strip()
		place = place.encode('utf8')
		place = re.sub('\s+', ' ', place).strip()

		ltype = 'RESTAURANT'
		if r_link in is_market:
			ltype = 'MARKET'

		# csvwriter.writerow(['NAME', 'ADDRESS', 'TYPE', 'PLACE', 'URL'])
		csvwriter.writerow([title, address, ltype, place, "http://www.zabihah.com" + r_link])

	total = len(all_mo_links)
	i = 0
	scraped_links = {}
	for m_link in all_mo_links:
		if m_link in scraped_links: continue
		scraped_links[m_link] = 1
		i = i + 1
		print "[%s/%s] " % (str(i), str(total))
		c = get_url(m_link)

		soup = BeautifulSoup(c)
		subtitleLink = soup.find_all('div', attrs={'class': 'subtitleLink'})
		subtitleLink = map(lambda x: x.find('a', target=False, attrs={'href': re.compile('/d/')}), subtitleLink)
		subtitleLink = filter(lambda x: x is not None, subtitleLink)
		subtitleLink = map(lambda x: x['href'], subtitleLink)

		for m2_link in subtitleLink:
			if m2_link in scraped_links: continue
			scraped_links[m2_link] = 1
			c = get_url(m2_link)
			if not c:
				print "NO CONTENT FOUND."
				continue

			soup = BeautifulSoup(c)
			title = soup.find('div', attrs={'class': 'titleBM'})
			address = title.next_sibling.strip()
			title = title.get_text().strip()
			z3_fg = soup.find('div', attrs={'class': 'bmLink'})
			z3_fg = z3_fg.find_all('a')
			z3_fg = map(lambda x: x.get_text(), z3_fg)
			z3_fg = filter(lambda x: x != 'HOME', z3_fg)
			place = ' / '.join(z3_fg)

			title = title.encode('utf8')
			title = re.sub('\s+', ' ', title).strip()
			address = address.encode('utf8')
			address = re.sub('\s+', ' ', address).strip()
			place = place.encode('utf8')
			place = re.sub('\s+', ' ', place).strip()
			# csvwriter.writerow(['NAME', 'ADDRESS', 'TYPE', 'PLACE', 'URL'])
			csvwriter.writerow([title, address, 'MOSQUE', place, m2_link])

def get_url(url):
	m5 = md5.new(url).hexdigest()
	fn = Bin + "/html/" + m5 + ".html"

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
			res = session.get(url, timeout=30)
		except BaseException, e:
			print e

		# time.sleep(1)
		if not res or res.status_code > 200:
			tried_times = tried_times + 1
			if tried_times > 5:
				return # just skip it
			continue

		fh = open(fn, 'w')
		data = res.text.encode(res.encoding)
		fh.write(data)
		fh.close()

		return data

if __name__ == '__main__':
	main()