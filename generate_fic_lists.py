#!/usr/bin/bash/python3

from fanfic_util import FanficGetter
from fanfic_util import FanficHTMLHandler

import string, sys, re

### VARIABLES ###
FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'
ROMANCE_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/romance_fic_paths.txt'
FRIENDSHIP_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/friendship_fic_paths.txt'
ENEMY_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/enemy_fic_paths.txt'
OUT = '/home/maria/Documents/Fanfic_ontology/generate_list_discarded.txt'

ENEMY_TAGS = ['Graphic Depictions Of Violence', 'Rape/Non-con', 'Torture', 'Mind Rape', 'Dead Dove: Do Not Eat']

### MAIN ###

#Initialize handlers, get fanfic paths
fgetter = FanficGetter()
handler = FanficHTMLHandler()

html_fics = fgetter.get_fic_paths_in_list()
print(fgetter.get_fic_listing_path()) #debug
#print(html_fics[:10]) #debug


romance_fics = []
friendship_fics = []
enemy_fics = []

romance = False
friendship = False
for path in html_fics:
	chapters = handler.get_chapters(path)
	ships = handler.get_relationships(path)

	#if chapters[0] == 1 : print(chapters, rating) #debug

	#This hand of the IF-ELSE handles romance and frienship. Because they're very popular, and can feature in long fics, we're restricting it to fics than only have one chapter to ensure that we get the essential characteristics
	if chapters == [1,1]:
		
		if len(ships) > 0:
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
		

	elif int(chapters[0]) < 6: #This hand of the IF-ELSE handles enemy relationships. It's much less popular, so we admit longer fics
		if len(ships) < 2: #We do not want friendship or romance here, we admit one at max
			tags = handler.get_tags(path)

			if any(tag in ENEMY_TAGS for tag in tags): enemy_fics.append(path)
			

#Sometimes, fics about rape contain "romance" relationship tags, let's take them out
for path in romance_fics:
	tags = handler.get_tags(path)
	if 'Rape/Non-con' in tags: romance_fics.remove(path)
			
				


print("Total romance fics: ", len(romance_fics))
print("Total friendship fics: ", len(friendship_fics))
print("Total enemy fics: ", len(enemy_fics))

#Save path lists

for path in romance_fics:
	f = open(ROMANCE_LISTING_PATH, 'a')
	f.write(path+'\n')
	f.close()


for path in friendship_fics:
	f = open(FRIENDSHIP_LISTING_PATH, 'a')
	f.write(path+'\n')
	f.close()

for path in enemy_fics:
	f = open(ENEMY_LISTING_PATH, 'a')
	f.write(path+'\n')
	f.close()

