#!/usr/bin/env python
# -*- coding:utf-8 -*-

import gensim
import codecs, argparse, time, re
from scipy.spatial.distance import cosine
import subprocess
import shlex
import csv
import json

'''
Script that takes a list of words, a directory containing one or more sets of diachronic embeddings.
Outputs csv-formatted data containing the word, its embeddings, its self-similarity across time, its
raw counts, and its corpus frequencies (which requires corpus totals).
'''

# Get arguments
parser = argparse.ArgumentParser(description = '')
parser.add_argument('word_list', metavar = 'LIST', type = str, help = "Specify the file containing the list of words (one-per-line) to query.")
parser.add_argument('embedding_dir', metavar = 'DIR', type = str, help = "Specify the directory containing the Volkskrant and Trouw embeddings.")
parser.add_argument('-in', '--initialize', action = 'store_true', help = "Initialize embedding using first slice")
args = parser.parse_args()

# Read in word list
words = []
word_list_file = open(args.word_list, 'r')
for line in word_list_file:
	if ' ' in line.strip():
		print 'More than one word on this line: {0}'.format(line.strip())
	else:
		words.append(line.strip())
print 'List of words: {0}\n'.format(', '.join(words))

# Generate year slice numbers
years = range(2016, 1993, -1)

# Load models, query words, store results
time_0 = time.time()
results = {} # format: {'word': {'word': 'word', similarity_1994:0.1, ...}}
for word in words:
	results[word] = {'word': word}
papers = ['volkskrant', 'trouw']

for paper in papers:
	print 'Querying against embeddings from {0}'.format(paper)
	print '\tLoading models, should take a while...'
	year_totals = {} # {year: total}
	models = []
	# Load embeddings
	if args.initialize:
		print '\tLoading initial model...'
		models.append(gensim.models.Word2Vec.load_word2vec_format('working/{0}_initial_reverse.w2v'.format(paper)))
		print '\tDone! took {0} seconds'.format(time.time() - time_0)
	for year in years:
		print '\tLoading model {0}_{1}...'.format(paper, year)
		time_0 = time.time()
		models.append(gensim.models.Word2Vec.load_word2vec_format('working/{0}_{1}_reverse.w2v'.format(paper, year)))
		print '\tDone! took {0:.2f} seconds'.format(time.time() - time_0)
		# Get word counts per year-slice subcorpus
		processing_call = shlex.split('wc -w {0}/{1}_{2}_tokenized'.format(args.embedding_dir, paper, year))
		proc = subprocess.Popen(processing_call, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		year_totals[year] = proc.stdout.read().strip().split(' ')[0]

	# Query words and get data points we need
	print '\nQuerying words...'
	for word in words:
		print '\tQuerying word {0}'.format(word)
		try:
			for idx, model in enumerate(models):
				if idx == 0:
					continue
				else:
					prev_model = models[idx-1]
					similarity = 1 - cosine(model[word], prev_model[word])
					if args.initialize:
						year = years[idx-1]
					else:
						year = years[idx]
					results[word]['similarity_{0}_{1}_{2}'.format(paper, year + 1, year)] = similarity
					print '\tyear: {0} - similarity: {1:.5f}'.format(year, similarity)
					# Get count and frequency of word in corpus
					processing_call = shlex.split("grep -c '\\b{0}\\b' {1}/{2}_{3}_tokenized".format(word, args.embedding_dir, paper, year))
					proc = subprocess.Popen(processing_call, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
					word_count = proc.stdout.read().strip()
					results[word]['count_{0}_{1}'.format(paper, year)] = word_count
					results[word]['frequency_{0}_{1}'.format(paper, year)] = float(word_count)/float(year_totals[year])*1000000.0
		except KeyError:
			print 'Word not found.'
			continue
	
# Output results to file
json.dump(results, open('{1}/{0}_results.json'.format(args.word_list[:-4], args.embedding_dir), 'w'))

# Generate CSV-headers
columns = ['word']
for paper in papers:
	for year in years[1:]:
		for cat in ['similarity', 'count', 'frequency']:
			if cat == 'similarity':
				columns.append('{0}_{1}_{2}_{3}'.format(cat, paper, year + 1, year))
			else:
				columns.append('{0}_{1}_{2}'.format(cat, paper, year))

# Write CSV to file
with open('{1}/{0}_results.csv'.format(args.word_list[:-4], args.embedding_dir), 'wb') as of:
	writer = csv.writer(of, delimiter=';')
	writer.writerow(columns) # Write header
	for word in words:
		word_results = results[word]
		if len(word_results) == len(columns):
			row_list = []
			for column in columns:
				row_list.append(word_results[column])
			writer.writerow(row_list)
		else:
			print 'No results for {0}'.format(word)
