#!/usr/bin/env python

# encoding=utf-8

import csv
import jieba

big_hash = {}
reader = csv.reader(file('ans.csv', 'rb'))
for line in reader:
    [stkcd, ans, year] = line
    if stkcd == 'stkcd': continue # header

    seg_list = jieba.cut(ans)
    for seg in seg_list:
    	seg = seg.encode('utf8')
    	if not stkcd in big_hash: big_hash[stkcd] = {}
    	if not year in big_hash[stkcd]: big_hash[stkcd][year] = {}
    	if not seg in big_hash[stkcd][year]: big_hash[stkcd][year][seg] = 0
    	big_hash[stkcd][year][seg] += 1

# csv out
writer = csv.writer(file('out.csv', 'wb'))
writer.writerow(['stkcd', 'year', 'word', 'count'])
for stkcd in big_hash:
	for year in big_hash[stkcd]:
		for seg in big_hash[stkcd][year]:
			writer.writerow([stkcd, year, seg, big_hash[stkcd][year][seg]])
