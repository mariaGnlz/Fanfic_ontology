#!/bin/bash/python3

import requests, time, sys
import urllib.request
from urllib.error import URLError, HTTPError, ContentTooShortError
from bs4 import BeautifulSoup

### VARIABLES ###
HTML_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_fics/html/'
HTML_FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'

### FUNCTIONS ###
def get_work_links_from_file():
	link_file = open('fic_work_links.txt', 'r')

	work_links = [line[:-1] for line in link_file.readlines()] #take out the \n at the end of the line
	link_file.close()
	
	return work_links 

def write_out_file(link, reason, index):
	out_file = open(HTML_FICS_PATH+'out.txt', 'a')
	out_file.write(link+'\nReason: '+reason+' Index: '+str(index)+'\n')
	out_file.close()


def get_html_link(page):
	soup = BeautifulSoup(page.content, 'html.parser')
			

	if soup.find('title').text == '\n          New\n          Session\n        |\n        Archive of Our Own\n    ':
		#the work is private and shouldn't be downloaded
		html_link=''
	
	else:				
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
				write_out_file(work_links[i], 'deleted', i)

				break

			else: break

		if not deleted: #only continue with iteration if the work is still online

			html_link = get_html_link(page)

			if html_link == '': #this work is private
				num_deleted += 1
				write_out_file(work_links[i], 'private', i)
				print('Private work at '+work_links[i])
				
			else:
				download_link = 'https://archiveofourown.org'+html_link['href']
				#print(download_link) #debug
			
				print('Downloading ',i,'of ',end,'. . .')

				try:
					fanfic_path, _ = urllib.request.urlretrieve(download_link, HTML_FICS_PATH+'gomensfanfic_'+str(i)+'.html')
					#print(fanfic_path) #debug

					#Write path to fanfic on html_fic_paths.txt
					html_list = open(HTML_FIC_LISTING_PATH, 'a')
					html_list.write(fanfic_path+'\n')
					html_list.close()
	
				except HTTPError as e:
					print('HTTPError ',e.code,': ',e.reason,'\nIn fanfic number ',i)
					if e.code == 429: #Too Many Requests
						i-=1 #Will re-attempt iteration from the beginning

				except ContentTooShortError as e:
					print('ContentTooShortError ',e.code,':',e.reason,'\nIn fanfic number ',i)
					write_out_file(work_links[i], e.reason, i)

				except URLError as e:
					print('URLError ',e.code,': ',e.reason,'\nIn fanfic number ',i)
					write_out_file(work_links[i], e.reason, i)

				except (IOError, OSError) as e:
					print('IOError/OSerror ',e.errno,': ',e.strerror,'\nIn fanfic number ',i)
					write_out_file(work_links[i], e.strerror, i)

				except Error as e:
					print('Error ',e.errno,': ',e.strerror,'\nIn fanfic number ',i)
					write_out_file(work_links[i], e.strerror, i)

		
		#end if not deleted

		i+=1
	#end while loop

	num_fics = len((open(HTML_FIC_LISTING_PATH, 'r')).readlines())
	return num_deleted, num_fics #return number of deleted fics and fics successfully downloaded


### M A I N ###

work_links = get_work_links_from_file()
initial_num = len((open(HTML_FIC_LISTING_PATH, 'r')).readlines())

if len(sys.argv) == 3:
	start_index = int(sys.argv[1])
	end_index = int(sys.argv[2])
	print(type(start_index), end_index) #debug

	start = time.time()
	num_deleted, num_fics = download_works_in_range(work_links, start_index, end_index)
	end = time.time()

	print('Successfully downloaded ',(num_fics-initial_num),' fanfics in ',(end-start)/60,' minutes to '+HTML_FICS_PATH)
	print('Deleted fics: ',num_deleted)

elif len(sys.argv) == 1:	
	start = time.time()
	num_deleted, num_fics = download_works_in_range(work_links, 5147, 6000)
	#num_deleted, num_fics = download_works_in_range(work_links, 0, 10) #debug
	end = time.time()

	print('Successfully downloaded ',(num_fics-initial_num),' fanfics in ',(end-start)/60,' minutes to '+HTML_FICS_PATH)
	print('Deleted fics: ',num_deleted)

else:
	print('Error. Correct usage: check_correct.py OR check_correct.py [start_index] [end_index]')



