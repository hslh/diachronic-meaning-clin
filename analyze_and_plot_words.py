#!/usr/bin/env python
# -*- coding:utf-8 -*-

import argparse
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from math import log, log10
from scipy.stats.stats import pearsonr, spearmanr

''' Script that takes the raw data (output of query_words_in_embeddings.py), does frequency cut-off, 
	frequency discounting, and plotting for a given word. Also calculates some correlations.'''

# Get arguments
parser = argparse.ArgumentParser(description = '')
parser.add_argument('results', metavar = 'RESULTS.json', type = str, help = "Specify the file containing the raw data (in json-format) to analyze.")
parser.add_argument('--avg', '-a', metavar = 'AVG_SIM.json', type = str, help = "Specify the file containing the average similarity to plot.")
parser.add_argument('--word', '-w', metavar = 'WORD', type = str, help = "Runs the analysis for a given word.")
parser.add_argument('--min-count', '-mc', metavar = 'COUNT', type = int, help = "If given, returns the list of words with a count > COUNT in all years in both newspapers.")
parser.add_argument('--min-freq', '-mf', metavar = 'FREQ', type = float, help = "If given, returns the list of words with a freq > FREQ in all years in both newspapers.")
parser.add_argument('--min-avg-freq', '-maf', metavar = 'FREQ', type = float, help = "If given, returns the list of words with a average freq > FREQ in both newspapers.")
args = parser.parse_args()

# Read data, remove words which don't occur in both embedding sets
results = json.load(open(args.results, 'r'))
clean_results = {}
for word in results:
	if len(results[word]) == 133:
		clean_results[word] = results[word]
results = clean_results

# Take data for a single word, plot self-distance over time
if args.word:
	# Read data
	try:
		results = results[args.word]
	except KeyError:
		raise SystemExit("Quitting: Word {0} not found".format(args.word))
	if args.avg:
		average_similarity = json.load(open(args.avg, 'r'))

	# Get values of different variables
	years = range(1995,2016)
	sorted_keys = sorted(results.keys()) # Make sure keys are sorted as to not mix up years!
	volkskrant_count= [float(results[key]) for key in sorted_keys if 'count_volkskrant' in key][1:]
	trouw_count = [float(results[key]) for key in sorted_keys if 'count_trouw' in key][1:]
	volkskrant_frequency = [float(results[key]) for key in sorted_keys if 'frequency_volkskrant' in key][1:]
	trouw_frequency = [float(results[key]) for key in sorted_keys if 'frequency_trouw' in key][1:]
	volkskrant_similarity = [float(results[key]) for key in sorted_keys if 'similarity_volkskrant' in key][1:]
	trouw_similarity = [float(results[key]) for key in sorted_keys if 'similarity_trouw' in key][1:]
	volkskrant_distance = [1 - similarity for similarity in volkskrant_similarity]
	trouw_distance = [1 - similarity for similarity in trouw_similarity]
	if args.avg:
		volkskrant_average_similarity = [float(average_similarity[key]) for key in sorted(average_similarity.keys()) if 'avg_similarity_volkskrant' in key][1:-1]
		trouw_average_similarity = [float(average_similarity[key]) for key in sorted(average_similarity.keys()) if 'avg_similarity_trouw' in key][1:-1]

	# Get some correlations
	print 'Trouw similarity vs. Volkskrant similarity: ' + str(spearmanr(trouw_similarity, volkskrant_similarity))
	print 'Trouw frequency vs. Volskrant frequency:  ' + str(spearmanr(trouw_frequency, volkskrant_frequency))
	print 'Trouw similaritys vs. Trouw frequency: ' + str(spearmanr(trouw_similarity, trouw_frequency))
	print 'Volkskrant similarity vs. Volkskrant frequency: ' + str(spearmanr(volkskrant_similarity, volkskrant_frequency))
	print 'Average frequency (Trouw, Volkskrant): ' + str((sum(trouw_frequency)/len(trouw_frequency),sum(volkskrant_frequency)/len(volkskrant_frequency)))
	print 'Average similarity (Trouw, Volkskrant): ' + str((sum(trouw_similarity)/len(trouw_similarity),sum(volkskrant_similarity)/len(volkskrant_similarity)))

	# Calculate a normalized distance
	volkskrant_min_frequency = min(volkskrant_frequency)
	volkskrant_log_frequency = [log10(x) + 1 for x in volkskrant_frequency]
	volkskrant_norm_log_frequency = [x/min(volkskrant_log_frequency) for x in volkskrant_log_frequency]
	volkskrant_norm_distance = [(1.0 - similarity) / volkskrant_norm_log_frequency[idx] for idx, similarity in enumerate(volkskrant_similarity)]
	trouw_min_frequency = min(trouw_frequency)
	trouw_log_frequency = [log10(x) + 1 for x in trouw_frequency]
	trouw_norm_log_frequency = [x/min(trouw_log_frequency) for x in trouw_log_frequency]
	trouw_norm_distance = [(1.0 - similarity) / trouw_norm_log_frequency[idx] for idx, similarity in enumerate(trouw_similarity)]

	# Plot all variables for analysis
	fig = plt.figure(1, figsize=(15,10))
	fig.suptitle('Analysis of word \'{0}\''.format(args.word), fontweight = 'bold')

	plt.subplot(221)
	lines = plt.plot(years, volkskrant_count, 'b-', label='Volkskrant')
	plt.setp(lines, marker = '.')
	lines = plt.plot(years, trouw_count, 'r-', label='Trouw')
	plt.setp(lines, marker = '.')
	plt.legend(framealpha=0.5)
	plt.ylim(0,)
	plt.xlabel("Year")
	plt.ylabel("Word Count")
	plt.title("Word count by year")

	plt.subplot(222)
	lines = plt.plot(years, volkskrant_frequency, 'b-', label='Volkskrant')
	plt.setp(lines, marker = '.')
	lines = plt.plot(years, trouw_frequency, 'r-', label='Trouw')
	plt.setp(lines, marker = '.')
	plt.legend(framealpha=0.5)
	plt.ylim(0,)
	plt.xlabel("Year")
	plt.ylabel("Word Frequency (words per million)")
	plt.title("Word frequency by year")

	plt.subplot(223)
	lines = plt.plot(years, volkskrant_similarity, 'b-', label='Volkskrant')
	plt.setp(lines, marker = '.')
	lines = plt.plot(years, trouw_similarity, 'r-', label='Trouw')
	plt.setp(lines, marker = '.')
	if args.avg:
		lines = plt.plot(years, volkskrant_average_similarity, 'b--', label='Volkskrant average')
		lines = plt.plot(years, trouw_average_similarity, 'r--', label='Trouw average')
	plt.legend(framealpha=0.5)
	plt.ylim(0,1)
	plt.xlabel("Year")
	plt.ylabel("Cosine self-similarity from year to year + 1")
	plt.title("Cosine self-similarity by year")

	plt.subplot(224)
	lines = plt.plot(years, volkskrant_norm_distance, 'b-', label='Volkskrant')
	plt.setp(lines, marker = '.')
	lines = plt.plot(years, trouw_norm_distance, 'r-', label='Trouw')
	plt.setp(lines, marker = '.')
	plt.legend(framealpha=0.5)
	plt.ylim(0,1)
	plt.xlabel("Year")
	plt.ylabel("Normalized self-distance")
	plt.title("Normalized self-distance by year")

	plt.show()

	# Plots for slides/paper
	# #5d0919 = 20% dark crimson 
	color_1 = '#5d0919'
	# #4781eb = 60% dark cornflowerblue
	color_2 = '#4781eb'
	
	plt.rcParams.update({'font.size': 29})
	fig = plt.figure(1, figsize=(25.58,8), tight_layout = True)
	lines = plt.plot(years, volkskrant_similarity, linestyle='solid', color=color_2, label='Volkskrant', linewidth = 4.0, markeredgewidth = 7.5)
	plt.setp(lines, marker = '.')
	lines = plt.plot(years, trouw_similarity, linestyle='solid', color=color_1, label='Trouw', linewidth = 4.0, markeredgewidth = 7.5)
	plt.setp(lines, marker = 's')
	if args.avg:
		lines = plt.plot(years, volkskrant_average_similarity, linestyle='dashed', color=color_2, label='Volkskrant average', linewidth = 3.0)
		lines = plt.plot(years, trouw_average_similarity, linestyle='dashed', color=color_1, label='Trouw average', linewidth = 3.0)
	plt.legend(framealpha=0.5)
	plt.ylim(0,1)
	plt.xlim(years[0]-.5,years[-1]+.5)
	plt.xlabel("Year")
	plt.ylabel("Self-similarity of year to year+1")
	ax = plt.gca()
	ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
	plt.show()

	plt.rcParams.update({'font.size': 29})
	fig = plt.figure(1, figsize=(25.58,8), tight_layout = True)
	lines = plt.plot(years, volkskrant_frequency, linestyle='solid', color=color_2, label='Volkskrant', linewidth = 4.0, markeredgewidth = 7.5)
	plt.setp(lines, marker = '.')
	lines = plt.plot(years, trouw_frequency, linestyle='solid', color=color_1, label='Trouw', linewidth = 4.0, markeredgewidth = 7.5)
	plt.setp(lines, marker = 's')
	plt.legend(framealpha=0.5)
	plt.ylim(0,)
	plt.xlim(years[0]-.5,years[-1]+.5)
	plt.xlabel("Year")
	plt.ylabel("Frequency (words per million)")
	ax = plt.gca()
	ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
	plt.show()

# Give word list with minimum count
word_list = []
if args.min_count:
	for word in results:
		under_count = False
		word_results = results[word]
		for key in word_results:
			if 'count' in key:
				if int(word_results[key]) < args.min_count:
					under_count = True
					print '{0} has too low count in at least one year'.format(word)
					break
		if not under_count:
			word_list.append(word.encode('utf-8'))	
	print 'Remaining words: {0}'.format(', '.join(word_list))

# Give word list with minimum count
word_list = []
if args.min_freq:
	for word in results:
		under_count = False
		word_results = results[word]
		for key in word_results:
			if 'frequency' in key:
				if float(word_results[key]) < args.min_freq:
					under_count = True
					print '{0} has too low frequency in at least one year'.format(word)
					break
		if not under_count:
			word_list.append(word.encode('utf-8'))	
	print 'Remaining words: {0}'.format(', '.join(word_list))

# Give word list with minimum count
word_list = []
if args.min_avg_freq:
	for word in results:
		word_results = results[word]
		freqs = []
		for key in word_results:
			if 'frequency' in key:
				freqs.append(float(word_results[key]))
		if sum(freqs)/len(freqs) > args.min_avg_freq:
			word_list.append(word.encode('utf-8'))	
		else:
			pass
			print '{0} has too low frequency in at least one year'.format(word)
	print 'Remaining words: {0}'.format(', '.join(word_list))
