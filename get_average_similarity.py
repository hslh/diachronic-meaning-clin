#!/usr/bin/env python
# -*- coding:utf-8 -*-

import gensim
from scipy.spatial.distance import cosine
import argparse
import json
import time

''' 
Script that takes a list of words (one per line) and a directory containing one or more 
sets of diachronic embeddings. Outputs average self-similarity from year-to-year for 
the words in the list.
'''

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
print 'Read list of {0} words'.format(len(words))

# Generate year-slice numbers
years = range(2016, 1993, -1)

# Load models, query words, store results
results = {} # format: {avg_similarity_volkskrant_1995_1994: 0.1, ...}
papers = ['volkskrant', 'trouw']
for paper in papers:
	time_0 = time.time()
	num_words = len(words)
	print 'Querying against embeddings from {0}'.format(paper)
	print '\tLoading models, should take a while...'
	models = []
	if args.initialize:
		print '\tLoading initial model...'
		models.append(gensim.models.Word2Vec.load_word2vec_format('working/{0}_initial_reverse.w2v'.format(paper)))
		print '\tDone! took {0} seconds'.format(time.time() - time_0)
	for year in years:
		print '\tLoading model {0}_{1}...'.format(paper, year)
		time_0 = time.time()
		models.append(gensim.models.Word2Vec.load_word2vec_format('working/{0}_{1}_reverse.w2v'.format(paper, year)))
		print '\tDone! took {0:.2f} seconds'.format(time.time() - time_0)

	print '\nQuerying words...'
	time_0 = time.time()
	for word in words:
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
					try:
						results['avg_similarity_{0}_{1}_{2}'.format(paper, year + 1, year)] += similarity
					except KeyError:
						results['avg_similarity_{0}_{1}_{2}'.format(paper, year + 1, year)] = similarity
		except KeyError:
			print 'Word {0} not found.'.format(word)
			num_words -= 1
			continue
	print 'Got similarities for {0} of {1} words'.format(num_words, len(words))
	print 'Took {0:.4f} seconds'.format(time.time() - time_0)

	# Get avg from sum
	for key in results:
		if paper in key:
			results[key] /= num_words

# Output results to file
json.dump(results, open('{1}/{0}_average_similarity.json'.format(args.word_list[:-4], args.embedding_dir), 'w'))
