#!/bin/bash/python3

import requests, time
import urllib.request
from bs4 import BeautifulSoup

def check_for_text(blurb): #returns true if the fic contains at least 40 words per chapter on average
	contains_text = False
	
	#print(blurb.find('dd', class_='words').text) #debug
	num_words = (blurb.find('dd', class_='words').text).replace(',','') #take away the comma that marks the thousands
	if num_words != '': num_words=int(num_words) #there's a bug in AO3 that makes some works appear with no word count (not '0'; it doesn't show a number at all)

	if isinstance(num_words, int) and (num_words > 0):
		num_chapters = int(((blurb.find('dd', class_='chapters').text).split('/'))[0]) #chapters are displayed as '# of current chapters / total # of chapters', we only want the current chapters
		#print(num_chapters) #debug
		
		if num_words/num_chapters > 39 : contains_text = True

	return contains_text

def get_work_links(page_link):
	page = requests.get(page_link) #get first page of the archive
	soup = BeautifulSoup(page.content, 'html.parser')

	#figure out how many total pages there are
	page_list = (soup.find(class_='pagination actions')).find_all('li')
	number_of_pages = int(page_list[len(page_list)-2].text) #there are number_of_pages pages in total

	#get all work links
	work_links = []
	current_page = 1

	while current_page < number_of_pages:
		blurbs = soup.find_all(class_='work blurb group')

		for blurb in blurbs:
			#filter out fics that don't contain text
			contains_text = check_for_text(blurb)
			
			if contains_text:
				work_id = (blurb.find('h4')).find('a')
				work_links.append('https://archiveofourown.org'+work_id['href'])
		#end 'for blurb' loop


		page = requests.get(page_link.replace('&page='+str(current_page)+'&','&page='+str(current_page+1)+'&'))
		soup = BeautifulSoup(page.content, 'html.parser')

		current_page +=1
	#end while loop

	#get work links in last page
	blurbs = soup.find_all(class_='work blurb group')

	for blurb in blurbs:
		#filter out fics that don't contain text
		contains_text = check_for_text(blurb)
		
		if(contains_text):
			work_id = (blurb.find('h4')).find('a')
			work_links.append('https://archiveofourown.org'+work_id['href'])
	#end 'for blurb' loop

	return work_links


start = time.time()
work_links = get_work_links('https://archiveofourown.org/tags/Good%20Omens%20-%20Neil%20Gaiman%20*a*%20Terry%20Pratchett/works?commit=Sort+and+Filter&page=1&utf8=%E2%9C%93&work_search%5Bcomplete%5D=&work_search%5Bcrossover%5D=&work_search%5Bdate_from%5D=&work_search%5Bdate_to%5D=&work_search%5Bexcluded_tag_names%5D=Fanart%2CPodfic&work_search%5Blanguage_id%5D=en&work_search%5Bother_tag_names%5D=&work_search%5Bquery%5D=&work_search%5Bsort_column%5D=revised_at&work_search%5Bwords_from%5D=&work_search%5Bwords_to%5D=')
end = time.time()

print('Time: ',(end-start)/60,' mins', 'number of fics: ',len(work_links)) #debug

fic_work_links = open('./fic_work_links.txt', 'w')

for link in work_links:
	fic_work_links.write(link+'\n')

fic_work_links.close()

