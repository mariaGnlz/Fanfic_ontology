#!/bin/bash/python3

import requests
import urllib.request
from bs4 import BeautifulSoup

def get_download_links(work_links):
	download_links = []

	for link in work_links:
		page = BeautifulSoup((requests.get(link)).content, 'html.parser')

		all_links = (page.find(class_='download')).find_all('a')

		html_link = all_links[len(all_links)-1]
		download_links.append('https://archiveofourown.org'+html_link['href'])

	return download_links

#download_links = get_download_links(work_links)
"""
count = 1
for link in download_links:
	fanfic_path, _ = urllib.request.urlretrieve(link, 'trial_fanfic'+str(count)+'.html')

	count +=1
	print(fanfic_path)
"""
