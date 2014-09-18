#!/usr/bin/env python

# encoding=utf-8

import csv
import jieba

big_hash = {}
reader = csv.reader(file('ans.csv', 'rb'))
for line in reader:
	# line = line.decode("gb2312").encode("utf8")
	# stkcd,ANSID1,ANSNM1,ANSDETAIL1,year,n3,n2,n1
	[stkcd, tmp, ansmn1, ans, year, n1, n2, n3] = line
	if stkcd == 'stkcd': continue # header

	if not len(ansmn1): ansmn1 = ''

	seg_list = jieba.cut(ans)
	for seg in seg_list:
		seg = seg.encode('utf8')
		if not stkcd in big_hash: big_hash[stkcd] = {}
		if not year in big_hash[stkcd]: big_hash[stkcd][year] = {}
		if not ansmn1 in big_hash[stkcd][year]: big_hash[stkcd][year][ansmn1] = {}
		if not seg in big_hash[stkcd][year][ansmn1]: big_hash[stkcd][year][ansmn1][seg] = 0
		big_hash[stkcd][year][ansmn1][seg] += 1

# csv out
writer = csv.writer(file('out.csv', 'wb'))
writer.writerow(['stkcd', 'year', 'word', 'count'])
for stkcd in sorted(big_hash):
	for year in sorted(big_hash[stkcd]):
		for ansmn1 in sorted(big_hash[stkcd][year]):
			for seg in sorted(big_hash[stkcd][year][ansmn1], key=big_hash[stkcd][year][ansmn1].__getitem__, reverse=True):
				seg_text = seg
				try:
					seg_text = seg_text.decode("utf8").encode("gb2312")
				except BaseException, e:
					print e
				writer.writerow([stkcd, year, ansmn1, seg_text, big_hash[stkcd][year][ansmn1][seg]])
