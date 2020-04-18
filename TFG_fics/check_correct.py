#!/bin/bash/python3

from bs4 import BeautifulSoup

HTML_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_fics/html/'
HTML_FIC_LISTING_PATH='/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'
DELETED_FICS = []

def get_deleted_fics():
	f = open(HTML_FICS_PATH+'deleted.txt', 'r')
	lines = [line[:-1] for line in f.readlines()]
	f.close()

	index_lines = [line.split(' ') for line in lines if lines.index(line)%2 != 0]
	DELETED_FICS = [int(line[len(line)-1]) for line in index_lines]

	return DELETED_FICS

def write_out_file(link, reason, index):
	out_file = open('./out.txt', 'a')
	out_file.write(link+'\nReason: '+reason+' Index: '+str(index)+'\n')
	out_file.close()


DELETED_FICS = get_deleted_fics()
#print(DELETED_FICS) #debug

f = open(HTML_FIC_LISTING_PATH, 'r')
downloaded_works = [line[:-1] for line in f.readlines()] #take out the \n at the end of the line
f.close()
f = open('/home/maria/Documents/Fanfic_ontology/TFG_fics/fic_work_links.txt', 'r')
work_links = [line[:-1] for line in f.readlines()] #take out the \n at the end of the line
f.close()
f.close()

print('Number of downloaded fics: ',len(downloaded_works))

for index in DELETED_FICS:
	downloaded_works.insert(index, '<padding>') #because of deleted works, the list of downloaded works and the list in work_links are not the same length. this fixes that, for indexing purposes only


exists = True
all_equal = True
for i in range(len(downloaded_works)):
#for i in range(2): #debug
	if i not in DELETED_FICS:	
		try:
			#f = open(HTML_FICS_PATH+'gomensfanfic_'+str(i)+'.html') #debug
			f = (open(downloaded_works[i], 'r')).read()
		
			soup = BeautifulSoup(f, 'html.parser')
			links = (soup.find('p', class_='message')).find_all('a')
			work_link = (links[1]['href']).replace('http://archiveofourown.org/','')
			#print(work_link) #debug
			
			listed_link = work_links[i].replace('https://archiveofourown.org/','')
			#print(listed_link) #debug

			if listed_link != work_link: 
				all_equal = False
				write_out_file(work_link+' '+listed_link, 'Different links in file and list', i)						

		except OSError as e:
			print('IOError ',e.errno,': ',e.strerror,' in ',i)
			exists = False
			write_out_file(work_link, 'OSError', i)
		
		except:
			print('Some error occurred in ',i)
		

if exists and all_equal: print('All fic path and links are correct :D')
else: print('Some fic paths and links have problems')

