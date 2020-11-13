#!/usr/bin/bash/python3

from fanfic_util import FanficGetter
from fanfic_util import FanficHTMLHandler

import string, sys, re

### VARIABLES ###
FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'
ROMANCE_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/romance_fic_paths2.txt'
FRIENDSHIP_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/friendship_fic_paths.txt'
EXPLICIT_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/explicit_fic_paths.txt'
OUT = '/home/maria/Documents/Fanfic_ontology/generate_fic_discarded.txt'

fgetter = FanficGetter()
handler = FanficHTMLHandler()
print(fgetter.get_fic_listing_path()) #debug

#0 5000
html_fics = fgetter.get_fic_paths_in_range(0,10000)


romance_fics = []
friendship_fics = []
explicit_fics = []

romance = False
friendship = False
for path in html_fics:
	chapters = handler.get_chapters(path)
	rating = handler.get_rating(path)
	ships = handler.get_relationships(path)

	#if chapters[0] == 1 : print(chapters, rating) #debug

	if chapters == [1,1]:
		if rating in ['Explicit','Mature']:
			explicit_fics.append(path)

		else:
			for ship in ships:
				if re.match('(\s*\w* \w*/\w* \w*)|(\s*\w*/\w*)', ship): #If the fic has a romantic relationship tag
					romance = True
					break

				elif re.match('(\s*\w* \w* & \w* \w*)|(\s*\w* & \w*)', ship): #If the fic has a friendship relationship tag
					friendship = True
					#print(ship, path) #debug

				elif re.match('(\s*\w* \w* and \w* \w*)|(\s*\w* and \w*)', ship, re.IGNORECASE): #If the fic has a friendship relationship tag
					friendship = True
					#print(ship) #debug
			

			if romance: romance_fics.append(path)
			elif friendship: friendship_fics.append(path)
			else: 
				f = open(OUT, 'a')
				f.write(path+'\n')
				f.close()

			romance = friendship = False


print("Total PG romance fics: ", len(romance_fics))
print("Total friendship fics: ", len(friendship_fics))
print("Total explicit fics: ", len(explicit_fics))

#Save path lists
for path in romance_fics:
	f = open(ROMANCE_LISTING_PATH, 'a')
	f.write(path+'\n')
	f.close()


for path in friendship_fics:
	f = open(FRIENDSHIP_LISTING_PATH, 'a')
	f.write(path+'\n')
	f.close()


for path in explicit_fics:
	f = open(EXPLICIT_LISTING_PATH, 'a')
	f.write(path+'\n')
	f.close()

