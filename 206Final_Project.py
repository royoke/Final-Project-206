import requests
import json
import sqlite3
import facebook
import final_project_info
from datetime import datetime
import calendar
import re

graph = facebook.GraphAPI(access_token = final_project_info.fb_access_key) # creating connection with facebook Graph API
############################################################################################################################### Setting up cache
CACHE_FNAME = '206_final_project_cache.json'

try:
	cache_file = open(CACHE_FNAME, 'r')
	contents = cache_file.read()
	CACHE_DICTION = json.loads(contents)
	cache_file.close()
except:
	CACHE_DICTION = {}
############################################################################################################################### Creating cache function to get fb posts and likes
def get_facebook_data(user):
	if 'fb_likes' in CACHE_DICTION:
		return CACHE_DICTION['fb_likes']
	else:
		fb_likes = graph.get_all_connections(id = user, connection_name = 'likes')
		CACHE_DICTION['fb_likes'] = [data for data in fb_likes] # must use iteration to receive data from generator objects
		CACHE_DICTION['fb_likes'] = CACHE_DICTION['fb_likes'][:100] # ensured that exactly 100 objects were being retreived
		fb_posts = graph.get_all_connections(id = user, connection_name = 'posts')
		CACHE_DICTION['fb_posts'] = [data for data in fb_posts]
		CACHE_DICTION['fb_posts'] = CACHE_DICTION['fb_posts'][:100]
		cache_file = open(CACHE_FNAME, 'w')
		cache_file.write(json.dumps(CACHE_DICTION))
		cache_file.close()
		return CACHE_DICTION['fb_likes']
get_facebook_data('me') # calling function in order to get my likes into cache
############################################################################################################################### Creating cache function to get my instagram posts and likes
def get_insta_data(user):
	if 'insta_posts' in CACHE_DICTION:
		return CACHE_DICTION['insta_posts']
	else:
		insta_posts = requests.get('https://api.instagram.com/v1/users/{}/media/recent?access_token={}'.format(user, final_project_info.insta_access_token))
		CACHE_DICTION['insta_posts'] = json.loads(insta_posts.text)
		insta_likes = requests.get('https://api.instagram.com/v1/users/{}/media/liked?access_token={}'.format(user, final_project_info.insta_access_token))
		CACHE_DICTION['insta_likes'] = json.loads(insta_likes.text)
		cache_file = open(CACHE_FNAME, 'w')
		cache_file.write(json.dumps(CACHE_DICTION))
		cache_file.close()
		return CACHE_DICTION['insta_posts']
get_insta_data('self')
############################################################################################################################### Getting the dates of my data
def get_day_of_week(timestamp):
	if '-' not in timestamp:
		timestamp = datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d')
		timestamp = datetime.strptime(timestamp, '%Y-%m-%d')
		return calendar.day_name[timestamp.weekday()]
	else:
		num_date = re.findall('[0-9]{4}-[0-9]{2}-[0-9]{2}', timestamp) # takes only the date from the full timestamp
		date_obj = datetime.strptime(num_date[0], '%Y-%m-%d') # converts the string into the actual datetime object
		return calendar.day_name[date_obj.weekday()] # uses calender to return what day of the week that date occured on
############################################################################################################################### Writting data into DB
conn = sqlite3.connect('206Final_ProjectDBs.sqlite')
cur = conn.cursor()

cur.execute('DROP TABLE IF EXISTS FB_Likes')
cur.execute('CREATE TABLE FB_Likes (page_name TEXT, id TEXT, time_liked DATETIME, weekday TEXT)')

for data in CACHE_DICTION['fb_likes']:
	cur.execute('INSERT INTO FB_Likes (page_name, id, time_liked, weekday) VALUES (?,?,?,?)', (data['name'], data['id'], data['created_time'], get_day_of_week(data['created_time'])))

cur.execute('DROP TABLE IF EXISTS FB_Posts')
cur.execute('CREATE TABLE FB_Posts (message_or_story TEXT, id TEXT, time_posted DATETIME, weekday TEXT)')

for data in CACHE_DICTION['fb_posts']:
	if 'message' in data: # must specify whether 'message' or 'story' (your post v sharing someone elses)
		cur.execute('INSERT INTO FB_Posts (message_or_story, id, time_posted, weekday) VALUES (?,?,?,?)', (data['message'], data['id'], data['created_time'], get_day_of_week(data['created_time'])))
	else:
		cur.execute('INSERT INTO FB_Posts (message_or_story, id, time_posted, weekday) VALUES (?,?,?,?)', (data['story'], data['id'], data['created_time'], get_day_of_week(data['created_time'])))



conn.commit()
conn.close()
############################################################################################################################### Getting data to input into plot.ly
weekday_dict = {}
for data in CACHE_DICTION['fb_likes']:
	weekday_dict[get_day_of_week(data['created_time'])] = weekday_dict.get(get_day_of_week(data['created_time']), 0) + 1 
# used to imput data into plot.ly


