#!/usr/bin/env python
# -*- coding:utf-8 -*-

import gensim
import codecs, argparse, time, re
from scipy.spatial.distance import cosine

'''
Script for interactively comparing multiple embeddings of a word across time. Loads all models (takes a while), 
asks user for word input, shows year-to-year self-similarity.
'''

# Get arguments
parser = argparse.ArgumentParser(description = '')
parser.add_argument('newspaper', metavar = 'trouw|volkskrant', type = str, help = "Specify which newspaper (Trouw or Volkskrant) to train on")
parser.add_argument('-r', '--reverse', action = 'store_true', help = "Compare in reverse, i.e. from recent years to older years, instead of vice versa")
parser.add_argument('-in', '--initialize', action = 'store_true', help = "Initialize embedding using first slice")
args = parser.parse_args()
paper = args.newspaper
if paper not in ['volkskrant', 'trouw']:
	print 'Not an available newspaper!'
	raise SystemExit

# Generate year slice numbers
years = range(1994,2017)
if args.reverse:
	years.reverse()

# Add reverse to input filenames
if args.reverse:
	reverse = '_reverse'
else:
	reverse = ''

# Load models
print 'Loading models, should take a while...'
time_0 = time.time()
models = []
if args.initialize:
	print 'Loading initial model...'
	models.append(gensim.models.Word2Vec.load_word2vec_format('working/{0}_initial{1}.w2v'.format(paper, reverse)))
	print 'Done! took {0} seconds'.format(time.time() - time_0)
for year in years:
	print 'Loading model {0}_{1}'.format(paper, year)
	time_0 = time.time()
	models.append(gensim.models.Word2Vec.load_word2vec_format('working/{0}_{1}{2}.w2v'.format(paper, year, reverse)))
	print 'Done! took {0:.2f} seconds'.format(time.time() - time_0)

# Set up querying
while True:
	user_input = unicode(raw_input("Enter a word to query, or 'quit' to exit: "), 'utf-8')
	user_input = re.sub('[^\w]', '', user_input, flags = re.UNICODE)
	print 'Word: {0}'.format(user_input)
	if user_input.lower() == 'quit' or user_input.lower() == 'exit':
		break
	else:
		try:
			for idx, model in enumerate(models):
				if idx == 0:
					continue
				else:
					prev_model = models[idx-1]
					similarity = 1 - cosine(model[user_input], prev_model[user_input])
					if args.initialize:
						year = years[idx-1]
					else:
						year = years[idx]
					print 'year: {0} - similarity: {1:.5f}'.format(year, similarity)
		except KeyError:
			print 'Word not found.'
