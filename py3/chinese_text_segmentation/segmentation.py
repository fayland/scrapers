#!/usr/bin/env python3

# encoding=utf-8

import csv
import jieba

big_hash = {}
with open('a1.csv', newline='', encoding='gbk') as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		# stkcd,year,id,pkeys,,
		[stkcd, year, tid, pkeys, n1, n2] = row
		if stkcd == 'stkcd': continue # header

		if not len(pkeys): continue

		seg_list = jieba.cut(pkeys)
		for seg in seg_list:
			if not stkcd in big_hash: big_hash[stkcd] = {}
			if not year in big_hash[stkcd]: big_hash[stkcd][year] = {}
			if not tid in big_hash[stkcd][year]: big_hash[stkcd][year][tid] = {}
			if not seg in big_hash[stkcd][year][tid]: big_hash[stkcd][year][tid][seg] = 0
			big_hash[stkcd][year][tid][seg] += 1

# csv out
with open('out.csv', 'w', newline='') as f:
	writer = csv.writer(f)
	writer.writerow(['stkcd', 'year', 'word', 'count'])
	for stkcd in sorted(big_hash):
		for year in sorted(big_hash[stkcd]):
			for tid in sorted(big_hash[stkcd][year]):
				for seg_text in sorted(big_hash[stkcd][year][tid], key=big_hash[stkcd][year][tid].__getitem__, reverse=True):
					try:
						writer.writerow([stkcd, year, tid, seg_text, big_hash[stkcd][year][tid][seg]])
					except KeyError as e:
						pass
