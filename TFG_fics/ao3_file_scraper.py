#!/bin/bash/python3

import requests, time
import urllib.request
from urllib.error import URLError, HTTPError, ContentTooShortError
from bs4 import BeautifulSoup

### VARIABLES ###
HTML_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_fics/html/'
HTML_FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'

def get_work_links_from_file():
	link_file = open('fic_work_links.txt', 'r')

	work_links = [line[:-1] for line in link_file.readlines()]
	
	return work_links 

def get_html_link(page):
	soup = BeautifulSoup(page.content, 'html.parser')
	all_links = (soup.find(class_='download')).find_all('a')
	html_link = all_links[len(all_links)-1]

	return html_link


def download_works_in_range(work_links, start, end):
	num_deleted = 0
	
	i = start
	while i<end:
		deleted = False
		
		while True:		
			page = requests.get(work_links[i])
		
			if page.status_code == 429: #Too Many Requests
				print('Sleeping...')
				time.sleep(120)
				print('Woke up')
			
			elif page.status_code ==404: #Page Not Found
				print('Deleted work at '+work_links[i])
				deleted = True
				num_deleted += 1
				break

			else: break

		if not deleted: #only continue with iteration if the work is still online

			html_link = get_html_link(page)
	
			download_link = 'https://archiveofourown.org'+html_link['href']
			#print(download_link) #debug
			
			print('Downloading ',i,'of ',end,'. . .')

			try:
				fanfic_path, _ = urllib.request.urlretrieve(download_link, HTML_FICS_PATH+'gomensfanfic_'+str(i)+'.html')
				#print(fanfic_path) #debug

				#Write path to fanfic on html_fic_paths.txt
				html_list = open(HTML_FIC_LISTING_PATH, 'w')
				html_list.write(fanfic_path+'\n')
				html_list.close()

			except HTTPError as e:
				print('HTTPError ',e.code,': ',e.reason,'\nIn fanfic number ',i)
				if e.code == 429: #Too Many Requests
					i-=1 #Will re-attempt iteration from the beginning

			except ContentTooShortError as e:
				print('ContentTooShortError ',e.code,':',e.reason,'\nIn fanfic number ',i)

			except URLError as e:
				print('URLError ',e.code,': ',e.reason,'\nIn fanfic number ',i)

			except (IOError, OSError) as e:
				print('IOError ',e.code,': ',e.reason,'\nIn fanfic number ',i)

			except Error as e:
				print('Error ',e.code,': '.e.reason,'\nIn fanfic number ',i)

		
		#end if not deleted

		i+=1
	#end while loop

	num_fics = len((open(HTML_FIC_LISTING_PATH, 'r')).readlines())
	return num_deleted, num_fics #return number of deleted fics and fics successfully downloaded

work_links = get_work_links_from_file()

start = time.time()
num_deleted, num_fics = download_works_in_range(work_links, 751, 2000)
#_, num_fics = download_works_in_range(work_links, 0, 1) #debug
end = time.time()

print('Successfully downloaded ',num_fics,' fanfics in ',(end-start)/60,' minutes to '+HTML_FICS_PATH)
print('Deleted fics: ',num_deleted)

