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
############################################################################################################################### Creating cache function to get pages liked
def get_liked_fb_pages(user):
	if user in CACHE_DICTION:
		return CACHE_DICTION[user]
	else:
		results = graph.get_all_connections(id = user, connection_name = 'likes')
		CACHE_DICTION[user] = [data for data in results] # must use iteration to receive data from generator objects
		CACHE_DICTION[user] = CACHE_DICTION[user][:100] # ensured that exactly 100 objects were being retreived
		cache_file = open(CACHE_FNAME, 'w')
		cache_file.write(json.dumps(CACHE_DICTION))
		cache_file.close()
		return CACHE_DICTION[user]
my_liked_data = get_liked_fb_pages('me')
############################################################################################################################### Getting the dates of my likes
def get_day_of_week(timestamp):
	num_date = re.findall('[0-9]{4}-[0-9]{2}-[0-9]{2}', timestamp) # takes only the date from the full timestamp
	date_obj = datetime.strptime(num_date[0], '%Y-%m-%d') # converts the string into the actual datetime object
	return calendar.day_name[date_obj.weekday()] # uses calender to return what day of the week that date occured on
############################################################################################################################### Writting data into DB
conn = sqlite3.connect('206Final_ProjectDBs.sqlite')
cur = conn.cursor()

cur.execute('DROP TABLE IF EXISTS Likes')
cur.execute('CREATE TABLE Likes (page_name TEXT, id TEXT, time_liked DATETIME, weekday TEXT)')

for data in CACHE_DICTION['me']:
	cur.execute('INSERT INTO Likes (page_name, id, time_liked, weekday) VALUES (?,?,?,?)', (data['name'], data['id'], data['created_time'], get_day_of_week(data['created_time'])))

conn.commit()
conn.close()
############################################################################################################################### Getting data to input into plot.ly
weekday_dict = {}
for data in CACHE_DICTION['me']:
	weekday_dict[get_day_of_week(data['created_time'])] = weekday_dict.get(get_day_of_week(data['created_time']), 0) + 1 
print(weekday_dict) # used to imput data into plot.ly


