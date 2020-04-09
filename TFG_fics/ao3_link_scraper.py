#!/bin/bash/python3

import requests, time
from bs4 import BeautifulSoup

def check_for_text(blurb): #returns true if the fic contains at least 40 words per chapter on average
	contains_text = True
	
	#print(blurb.find('dd', class_='words').text) #debug
	num_words = (blurb.find('dd', class_='words').text).replace(',','') #take away the comma that marks the thousands

	if num_words == '': contains_text = False #there's a bug in AO3 that makes some works appear with no word count (not '0'; it doesn't show a number at all)
	else:
		num_words=int(num_words) 
		
		if num_words == 0: contains_text = False
		else:
			num_chapters = int(((blurb.find('dd', class_='chapters').text).split('/'))[0]) #chapters are displayed as '# of current chapters / total # of chapters', we only want the current chapters
			#print(num_words/num_chapters) #debug
		
			if (num_words/num_chapters) < 40: 
				contains_text = False


	#if not contains_text: print('in: ',((blurb.find('h4')).find('a'))['href']) #debug
	return contains_text


def get_work_links(page_link):
	page = requests.get(page_link) #get first page of the archive
	soup = BeautifulSoup(page.content, 'html.parser')

	#figure out how many pages in total there are
	page_list = (soup.find(class_='pagination actions')).find_all('li')
	number_of_pages = int(page_list[len(page_list)-2].text) #there are number_of_pages pages in total

	#get work links in all pages
	work_links = []
	discarded_links = []
	current_page = 1
	while current_page < number_of_pages:
		blurbs = soup.find_all(class_='work blurb group')
		#print('current page: ',current_page) #debug

		for blurb in blurbs:
			#filter out fics that don't contain text
			contains_text = check_for_text(blurb)
			
			work_id = (blurb.find('h4')).find('a')
			if contains_text: work_links.append('https://archiveofourown.org'+work_id['href'])
			else: 
				discarded_links.append('https://archiveofourown.org'+work_id['href'])
				#print('out:', work_id['href'])	
		#end 'for blurb' loop

		current_page +=1
		next_page_link = page_link.replace('&page=1&','&page='+str(current_page)+'&')
		while True: #wait out if too many requests
			page = requests.get(next_page_link)
			
			if page.status_code == 429:  #Too Many Requests
				print('Sleeping...')
				time.sleep(120)
				print('Woke up')

			else: break

		soup = BeautifulSoup(page.content, 'html.parser')

	#end while loop

	#get work links in last page (the loop won't catch it)
	blurbs = soup.find_all(class_='work blurb group')

	for blurb in blurbs:
		#filter out fics that don't contain text
		contains_text = check_for_text(blurb)
		
		work_id = (blurb.find('h4')).find('a')
		if contains_text == True: work_links.append('https://archiveofourown.org'+work_id['href'])
		else: discarded_links.append('https://archiveofourown.org'+work_id['href'])
	#end 'for blurb' loop
	print('Current page: ',current_page) #debug
	return work_links, discarded_links


start = time.time()
work_links, discarded_links = get_work_links('https://archiveofourown.org/tags/Good%20Omens%20-%20Neil%20Gaiman%20*a*%20Terry%20Pratchett/works?commit=Sort+and+Filter&page=1&utf8=%E2%9C%93&work_search%5Bcomplete%5D=&work_search%5Bcrossover%5D=&work_search%5Bdate_from%5D=&work_search%5Bdate_to%5D=&work_search%5Bexcluded_tag_names%5D=Fanart%2CPodfic&work_search%5Blanguage_id%5D=en&work_search%5Bother_tag_names%5D=&work_search%5Bquery%5D=&work_search%5Bsort_column%5D=revised_at&work_search%5Bwords_from%5D=&work_search%5Bwords_to%5D=')
end = time.time()

print('Time: ',(end-start)/60,' mins','\nNumber of fics: ',len(work_links),'\nDiscarded links: ',len(discarded_links)) #debug

fic_work_links = open('./fic_work_links.txt', 'w')

for link in work_links:
	fic_work_links.write(link+'\n')

fic_work_links.close()

discarded_works = open('./discarded_works.txt', 'w')
for link in discarded_links:
	discarded_works.write(link+'\n')

discarded_works.close()

