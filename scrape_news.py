#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Scrape Dutch news sites to make a large diachronic corpus'''

import re, requests, time, json, os, argparse
from bs4 import BeautifulSoup

def get_dates_from_archive(newspaper, archive_url, year):
	'''Scrapes archive overview page for a given year for a given newspaper, returns all dates for which archive is available'''

	dates = []
	year_url = archive_url + year
	year_page = requests.get(year_url, cookies = cookiewall_cookie)
	year_soup = BeautifulSoup(year_page.content, 'html.parser')
	for link in year_soup.find_all('a'):
		try:
			date = ''
			if newspaper == 'trouw':
				if re.search('archiveDay=', link['href']):
					date = link['href'][-8:]
					dates.append(date)
			if newspaper == 'volkskrant':
				if re.search('archief/detail/', link['href']):
					date = link['href'][-9:-1]
					dates.append(date)
		except KeyError: # When link has no 'href', just skip
			pass
	return dates

def get_articles_for_date_trouw(base_date_url, date):
	'''Scrapes archive page for a certain date for Trouw, returns urls for all articles of that date'''

	article_urls = []
	date_page = requests.get(base_date_url + date, cookies = cookiewall_cookie)
	date_soup = BeautifulSoup(date_page.content, 'html.parser')
	for link in date_soup.find_all('a'):
		try:
			if link.parent.parent.parent.name == 'div' and link.parent.parent.parent['class'][0] == 'articleOverview':
				if link.parent.parent.name == 'dl':
					if link.parent.name == 'dd':
						article_url= link['href']
						if re.match('http://www.trouw.nl/tr/nl/.*/archief/article/detail/', article_url):
							article_urls.append(article_url)
		except AttributeError:
			pass
	return article_urls

def get_articles_for_date_volkskrant(base_date_url, date):
	'''Scrapes archive page for a certain date for Volkskrant, returns urls for all articles of that date'''

	article_urls = []
	date_page = requests.get(base_date_url + date)
	date_soup = BeautifulSoup(date_page.content, 'html.parser')
	next_page = True
	next_page_url = ''
	while next_page:
		next_page = False
		for link in date_soup.find_all("a"):
			if link.parent.name == 'article':
				article_urls.append(link['href'])
		if date_soup.find_all("a", class_="pager--next"): # If there is a next page, get it and parse it
			next_page = True
			next_page_url = date_soup.find_all("a", class_="pager--next")[0]['href']
			date_page = requests.get(next_page_url)
			date_soup = BeautifulSoup(date_page.content, 'html.parser')
	return article_urls

def get_text_from_article(newspaper, article_url):
	'''Scrapes article page of a given newspaper to get all the content text, returns text'''

	article_text = ''
	try:
		article_page = requests.get(article_url, cookies = cookiewall_cookie)
	except requests.exceptions.TooManyRedirects: # Sometimes the article page just redirects, then skip it
		return ''
	except requests.exceptions.ConnectionError: # Instable connection? Wait for a bit, then skip its
		time.sleep(5)
		return ''
	article_soup = BeautifulSoup(article_page.content, 'html.parser')
	# Newspaper-specific things
	headers = []
	if newspaper == 'trouw':
		headers = article_soup.find_all('h1', id='articleDetailTitle')
	if newspaper == 'volkskrant':
		headers = article_soup.find_all('h1', class_='article__title')
	# Scrape header text 
	for header in headers:
		article_text += header.text.strip() + '\n'
	# Scrape text body
	for paragraph in article_soup.find_all('p'):
		try:
			if paragraph.parent.name == 'div':
				is_correct_parent = False
				# Newspaper-specific things
				if newspaper == 'trouw':
					is_correct_parent = re.match('art_box', paragraph.parent['id'])
				if newspaper == 'volkskrant':
					is_correct_parent = re.match('article__intro', paragraph.parent['class'][0]) or re.match('article__body', paragraph.parent['class'][0])			
				if is_correct_parent:
					if paragraph.text:
						text = re.sub('\n+', '\n', paragraph.text) # Remove extra newlines or spaces
						text = re.sub(' +', ' ', text)
						article_text += text.strip() + '\n'
		except KeyError:
			pass
	return article_text

def scrape_newspaper(newspaper, years):
	'''Scrape article texts from Trouw or Volkskrant archive, store per-year'''

	if newspaper == 'trouw':
		base_year_url = 'FILL THIS IN'
		base_date_url = 'FILL THIS IN'
	else:
		base_year_url = 'FILL THIS IN'
		base_date_url = 'FILL THIS IN'
	# Cyle through years specified
	year_range = [str(year) for year in years]
	for year in year_range:
		logfile = open('working/{1}_{0}.log'.format(year, newspaper), 'w', buffering=0) # No buffering, so able to read from log constantly while running
		# Scrape or load dates
		time0 = time.time()
		logfile.write('Scraping {1} for year {0}\n'.format(year, newspaper.capitalize()))
		fn = 'working/{1}_dates_{0}.json'.format(year, newspaper)
		if os.path.exists(fn):
			logfile.write('Loading dates from {0}\n'.format(fn))
			with open(fn, 'r') as f:
				dates = json.load(f)
		else:
			logfile.write('Scraping dates for year {0}\n'.format(year))
			if newspaper == 'trouw':
				dates = get_dates_from_archive(newspaper, base_year_url, year)
			if newspaper == 'volkskrant':
				dates = get_dates_from_archive(newspaper, base_year_url, year)
			with open(fn, 'w') as of:
				json.dump(dates, of)
		time1 = time.time()
		logfile.write('Found {0} dates for year {1}, took {2} seconds\n'.format(len(dates), year, time1 - time0))
		# Scrape or load article urls
		fn = 'working/{1}_article_urls_{0}.json'.format(year, newspaper)
		if os.path.exists(fn):
			logfile.write('Loading article urls from {0}\n'.format(fn))
			with open(fn, 'r') as f:
				article_urls = json.load(f)
		else:
			logfile.write('Scraping article URLs for year {0}\n'.format(year))
			article_urls = []
			for date in dates:
				if newspaper == 'trouw':
					article_urls += get_articles_for_date_trouw(base_date_url, date)
				if newspaper == 'volkskrant':
					article_urls += get_articles_for_date_volkskrant(base_date_url, date)
			with open(fn, 'w') as of:
				json.dump(article_urls, of)
		article_urls = list(set(article_urls)) # Remove duplicates
		time2 = time.time()
		logfile.write('Found {0} article URLs for year {1}, took {2} seconds\n'.format(len(article_urls), year, time2 - time1))
		# Scrape text from article pages
		logfile.write('Scraping article text for year {0}\n'.format(year))
		fn = 'working/{1}_{0}'.format(year, newspaper)
		with open(fn, 'w') as of:
			prev_time = time.time()
			for idx, article_url in enumerate(article_urls):
				if idx % 100 == 0 and idx > 1:
					logfile.write('Scraping article {0} of {1}. Previous 100 took {2} seconds.\n'.format(idx, len(article_urls), time.time() - prev_time))
					prev_time = time.time()
				if newspaper == 'trouw':
					of.write(get_text_from_article(newspaper, article_url).encode('utf-8'))
				if newspaper == 'volkskrant':
					of.write(get_text_from_article(newspaper, article_url).encode('utf-8'))
		time3 = time.time()
		logfile.write('Done! Took {0} seconds\n'.format(time3 - time2))
	logfile.close()
		
if __name__ == '__main__':
	# Parse arguments
	parser = argparse.ArgumentParser(description = 'Arguments for newspaper scraping')
	parser.add_argument('newspaper', metavar = 'trouw|volkskrant', type = str, help = 'Specify whether to scrape Trouw or Volkskrant')
	parser.add_argument('-y', '--year', metavar = 'YEAR', type = str, help = "Specify which year of Trouw (1994-2016) or Volkskrant (1994-2016) to scrape. If this argument is not given, all years will be scraped")
	args = parser.parse_args()
	# Get years to scrape
	if args.year:
		years = [args.year]
	else:
		years = range(1994,2017)
	# Define cookie needed for scraping
	cookiewall_cookie = {'nl_cookiewall_version': '1'}
	if args.newspaper.lower() == 'trouw':
		scrape_newspaper('trouw', years)
	elif args.newspaper.lower() == 'volkskrant' or args.newspaper.lower() == 'vk':
		scrape_newspaper('volkskrant', years)
	else:
		print '{0} is not a valid option for scraping'.format(args.newspaper)
