import requests
import time
#import pandas as pd
import xml.etree.ElementTree as ET


languageDependenceLevels = ["Useless offset",
"Aucun texte nécessaire dans le jeu",
"Un peu de texte nécessaire - facilement mémorisable ou d'un post-it",
"Texte modéré dans le jeu - a besoin d'une feuille d'aide ou d'un collage.",
"Utilisation extensive du texte - conversion massive nécessaire pour être jouable.",
"Injouable dans une autre langue"]

def formatter(start, end):
    return '{}-{}'.format(start, end)

def re_range(lst):
    n = len(lst)
    result = []
    scan = 0
    while n - scan > 2:
        step = lst[scan + 1] - lst[scan]
        if step != 1 or lst[scan + 2] - lst[scan + 1] != step:
            result.append(str(lst[scan]))
            scan += 1
            continue

        for j in range(scan+2, n-1):
            if lst[j+1] - lst[j] != step:
                result.append(formatter(lst[scan], lst[j]))
                scan = j+1
                break
        else:
            result.append(formatter(lst[scan], lst[-1]))
            return ','.join(result)

    if n - scan == 1:
        result.append(str(lst[scan]))
    elif n - scan == 2:
        result.append(','.join(map(str, lst[scan:])))

    return ','.join(result)

 # CSV

#response = requests.get('https://boardgamegeek.com/geekcollection.php?action=exportcsv&subtype=boardgame&username=Gwandalff&exporttype=csv&all=0')
#with open("bgg.csv", "w") as f:
#    f.write(response.text)
#
#data = pd.read_csv('bgg.csv')
#metrics = ['objectname','objectid','average','avgweight','minplayers','maxplayers','playingtime','minplaytime','maxplaytime','bggrecplayers','bggbestplayers','bggrecagerange']

#games = data[data.columns.intersection(metrics)]
#print(games)


 # XML
status = 202
response = None
while not status == 200:
	time.sleep(1)
	response = requests.get('https://api.geekdo.com/xmlapi/collection/Gwandalff?own=1')
	status = response.status_code

# Save the XML    (python3 bgg.py  2.59s user 0.09s system 13% cpu 20.082 total)
with open("bgg.xml", "w") as f:
	f.write(response.text)

# Don't save the XML (python3 bgg.py  2.54s user 0.06s system 12% cpu 20.698 total)
#games = ET.fromstring(response.text)

status = 202
response = None
while not status == 200:
	time.sleep(1)
	response = requests.get('https://api.geekdo.com/xmlapi/collection/Gwandalff?wishlist=1')
	status = response.status_code

# Save the XML    (python3 bgg.py  2.59s user 0.09s system 13% cpu 20.082 total)
with open("wish.xml", "w") as f:
	f.write(response.text)


# Owned games
games = ET.parse('bgg.xml').getroot()


yml = "games:\n"

for game in games:
	stats = game.find('stats')

	id = game.get('objectid')
	name = game.find('name').text
	thumbnail = game.find('thumbnail').text
	image = game.find('image').text
	minplayers  = stats.get('minplayers')
	maxplayers  = stats.get('maxplayers')
	minplaytime = stats.get('minplaytime')
	maxplaytime = stats.get('maxplaytime')
	playingtime = stats.get('playingtime')
	rating = round(float(stats.find('./rating/average').get('value')), 1)
	url = f"https://boardgamegeek.com/boardgame/{id}"
	



	gameresponse = requests.get(f"https://api.geekdo.com/xmlapi/boardgame/{id}?stats=1")
	gameroot = ET.fromstring(gameresponse.text)
	bg = gameroot.find('boardgame')
	age = bg.find('age').text
	



	numPlayersPoll = bg.find("poll[@name='suggested_numplayers']")
	bests = []
	recommendeds = []
	playerCounts = numPlayersPoll.iter("results")
	for playerCount in playerCounts:
		try:
			pc = int(playerCount.get('numplayers'))
			best = int(playerCount.find("result[@value='Best']").get("numvotes"))
			recommended = int(playerCount.find("result[@value='Recommended']").get("numvotes"))
			notreco = int(playerCount.find("result[@value='Not Recommended']").get("numvotes"))
			if best > recommended and best > notreco:
				bests.append(pc)
				recommendeds.append(pc)
			elif recommended > notreco:
				recommendeds.append(pc)
		except:
			pass
	bestsStr = re_range(bests)
	recoStr = re_range(recommendeds)




	langDepPoll = bg.find("poll[@name='language_dependence']")
	maxVote = -1
	levelIndex = 0
	levels = langDepPoll.find('results').findall("result")
	for level in levels:
		num = int(level.get('numvotes'))
		if num > maxVote:
			maxVote = num
			levelIndex = int(level.get('level'))
	languageDependence = "Unknown"
	if levelIndex > 0 and levelIndex < len(languageDependenceLevels):
		languageDependence = languageDependenceLevels[levelIndex]

		
	weight = bg.find('./statistics/ratings/averageweight').text
	averageweight = round(float(weight), 2)

	yml = yml + f'''  - name: "{name}"
    thumbnail: "{thumbnail}"
    image: "{image}"
    url: "{url}"
    rating: {rating}
    complexity: {averageweight}
    langdep: "{languageDependence}"
    age: {age}
    duration:
      min: {minplaytime}
      max: {maxplaytime}
      average: {playingtime}
    players:
      min: {minplayers}
      max: {maxplayers}
      best: "{bestsStr}"
      recommended: "{recoStr}"

'''

with open("./_data/bgg.yml", "w") as f:
	f.write(yml)



# Wishlist games
# Owned games
games = ET.parse('wish.xml').getroot()

priorityList = ["This should never appear", "Un MUST","J'adorerai","J'aimerai bien","J'y réfléchi","Jamais, s'il-vous plaît"]

yml = "games:\n"

for game in games:
	id = game.get('objectid')
	name = game.find('name').text
	thumbnail = game.find('thumbnail').text
	image = game.find('image').text
	url = f"https://boardgamegeek.com/boardgame/{id}"
	priority = game.find('status').get("wishlistpriority")
	comment = priority + " - " + priorityList[int(priority)]

	yml = yml + f'''  - name: "{name}"
    thumbnail: "{thumbnail}"
    image: "{image}"
    url: "{url}"
    priority: "{comment}"
'''

with open("./_data/wish.yml", "w") as f:
	f.write(yml)
