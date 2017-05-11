#!/usr/bin/env python
# -*- coding:utf-8 -*-

import gensim
import codecs, argparse, time

'''
Script for training word embeddings on a diachronic corpus using gensim, in per-year slices. 
Based on the original script by Marco Del Tredici
'''

start_time = time.time()

# Get arguments
parser = argparse.ArgumentParser(description = '')
parser.add_argument('newspaper', metavar = 'trouw|volkskrant', type = str, help = "Specify which newspaper (Trouw or Volkskrant) to train on")
parser.add_argument('-t', '--max-threads', metavar = 'NUM_THREADS', type = int, default = 4, help = "Maximum number of threads to use for training the model, default is 4")
parser.add_argument('-r', '--reverse', action = 'store_true', help = "Train in reverse, i.e. from recent years to older years, instead of vice versa")
parser.add_argument('-va', '--vocab-all', action = 'store_true', help = "Use the whole corpus (all years) to generate the vocabulary") 
parser.add_argument('-in', '--initialize', action = 'store_true', help = "Initialize embedding using first slice")
parser.add_argument('-is', '--intersect', action ='store_true', help = "Use intersect on saved embeddings of previous slice")
args = parser.parse_args()
paper = args.newspaper
if paper not in ['volkskrant', 'trouw']:
	print 'Not an available newspaper!'
	raise SystemExit

# Initialize model
model = gensim.models.Word2Vec(sg=1, hs=1, alpha=0.01, size=200, window=5, min_count=30, iter=20, workers = args.max_threads)
print 'Initialized model'

# Generate year slice numbers
years = range(1994,2017)
if args.reverse:
	years.reverse()

# Initialize vocabulary
if args.vocab_all:
	try:
		vocab_file = codecs.open('working/{0}_all_tokenized'.format(paper), 'r', encoding = 'utf-8')
	except IOError:
		print 'The file working/{0}_all_tokenized doesn\'t exist!'.format(paper)
		raise SystemExit
else:
	try:
		vocab_file = codecs.open('working/{0}_{1}_tokenized'.format(paper, years[0]), 'r', encoding = 'utf-8')
	except IOError:
		print 'The file working/{0}_{1}_tokenized doesn\'t exist!'.format(paper, years[0])
		raise SystemExit
vocab_sentences = gensim.models.word2vec.LineSentence(vocab_file)
model.build_vocab(vocab_sentences)
print 'Initialized vocabulary'

# Add reverse to output filenames
if args.reverse:
	reverse = '_reverse'
else:
	reverse = ''

# Cycle through year slices
for idx, year in enumerate(years):
	# Initialize on first slice if argument given
	if idx == 0 and args.initialize:
		print 'Initializing on year {0}'.format(year)
		time_before = time.time()
		input_file = codecs.open('working/{0}_{1}_tokenized'.format(paper, year), 'r', encoding = 'utf-8')
		sentences = gensim.models.word2vec.LineSentence(input_file)
		model.train(sentences)
		model.save_word2vec_format('working/{0}_initial{1}.w2v'.format(paper, reverse))
		if args.intersect:
			model.intersect_word2vec_format('working/{0}_initial{1}.w2v'.format(paper, reverse))
		print 'Initializing took {0} seconds'.format(time.time() - time_before)
	# Train on year slices
	print 'Training on year {0}'.format(year)
	time_before = time.time()
	# Intersect if argument given
	if idx != 0 and args.intersect:
		model.intersect_word2vec_format('working/{0}_{1}{2}.w2v'.format(paper, years[idx - 1], reverse))
	# Read new input slice
	input_file = codecs.open('working/{0}_{1}_tokenized'.format(paper, year), 'r', encoding = 'utf-8')
	sentences = gensim.models.word2vec.LineSentence(input_file)
	# Train and store embeddings
	model.train(sentences)
	model.save_word2vec_format('working/{0}_{1}{2}.w2v'.format(paper, year, reverse))
	print 'Training on year {0} took {1} seconds'.format(year, time.time() - time_before)

print 'Done! Total time elapsed: {0} seconds'.format(time.time() - start_time)
