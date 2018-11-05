#!/usr/bin/env python

# encoding=utf-8

import csv
import jieba

year = '2016'
big_hash = {}
ant_hash = {}
reader = csv.reader(file(year + '.csv', 'rb'))
for line in reader:
	# line = line.decode("gb2312").encode("utf8")
	# stkcd,ANSID1,ANSNM1,ANSDETAIL1,year,n3,n2,n1
	stkcd = line.pop(0)
	if stkcd == 'stkcd': continue # header

	x = 4
	while True:
		if len(line) < x: break;

		ppl = line[x]
		ans = line[x + 1]
		x = x + 4

		# print ppl + ': ' + ans

		# by stkcd year & by stkcd year person
		seg_list = jieba.cut(ans)
		for seg in seg_list:
			seg = seg.encode('utf8')
			if not stkcd in big_hash: big_hash[stkcd] = {}
			if not year in big_hash[stkcd]: big_hash[stkcd][year] = {}
			if not ppl in big_hash[stkcd][year]: big_hash[stkcd][year][ppl] = {}
			if not seg in big_hash[stkcd][year][ppl]: big_hash[stkcd][year][ppl][seg] = 0
			big_hash[stkcd][year][ppl][seg] += 1

			if not stkcd in ant_hash: ant_hash[stkcd] = {}
			if not year in ant_hash[stkcd]: ant_hash[stkcd][year] = {}
			if not seg in ant_hash[stkcd][year]: ant_hash[stkcd][year][seg] = 0
			ant_hash[stkcd][year][seg] += 1

# csv out
writer = csv.writer(file(year + '_out.csv', 'wb'))
writer.writerow(['stkcd', 'year', 'person', 'word', 'count'])
for stkcd in sorted(big_hash):
	for year in sorted(big_hash[stkcd]):
		for ppl in sorted(big_hash[stkcd][year]):
			for seg in sorted(big_hash[stkcd][year][ppl], key=big_hash[stkcd][year][ppl].__getitem__, reverse=True):
				seg_text = seg
				# try:
				# 	seg_text = seg_text.decode("utf8").encode("gb2312")
				# except BaseException, e:
				# 	print e
				writer.writerow([stkcd, year, ppl, seg_text, big_hash[stkcd][year][ppl][seg]])

writer = csv.writer(file(year + '_out.2.csv', 'wb'))
writer.writerow(['stkcd', 'year', 'word', 'count'])
for stkcd in sorted(ant_hash):
	for year in sorted(ant_hash[stkcd]):
		for seg in sorted(ant_hash[stkcd][year], key=ant_hash[stkcd][year].__getitem__, reverse=True):
			seg_text = seg
			# try:
			# 	seg_text = seg_text.decode("utf8").encode("gb2312")
			# except BaseException, e:
			# 	print e
			writer.writerow([stkcd, year, seg_text, ant_hash[stkcd][year][seg]])