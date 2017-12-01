import requests
import json
import sqlite3

token = 'EAACEdEose0cBAAB1a84p7zzsJ5B9ly5WIbx6mAaWsaJWzyJEWpOl34qAcZCHKLctQMsPBKuZAfN4NgfMawiN6BWEmB6y2jU6MeMRZAE0vh5heQvZCcoZBym6vtjHtc3ti2KnMZC2ukVw5h3yGE5dHcb0i2wWtyyzLRLfwdN9t6IgGv84P34YlN1sCSHe1o2X8ZD'
fbbase_url = 'https://graph.facebook.com/v2.11/'

CACHE_FNAME = 'SI206_Final_Project_Cache.json'

try:
	cache_file = open(CACHE_FNAME, 'r')
	CACHE_DICTION = json.loads(cache_file.read())
	cache_file.close()

except:
	CACHE_DICTION = {}

def get_fb_likes(user):
	if user in CACHE_DICTION:
		return CACHE_DICTION[user]
	else:
		results = json.loads(requests.get('https://graph.facebook.com/v2.11/{}/likes?limit=100&access_token={}'.format(user,token)).text)
		page_2_results = json.loads(requests.get(results['paging']['next']).text)
		for item in page_2_results['data']:
			if len(results['data']) < 100:
				results['data'].append(item)
		CACHE_DICTION[user] = results
		cache_file = open(CACHE_FNAME, 'w')
		cache_file.write(json.dumps(CACHE_DICTION))
		cache_file.close()
		return CACHE_DICTION[user]

my_likes = get_fb_likes('me')
print(len(CACHE_DICTION['me']['data']))